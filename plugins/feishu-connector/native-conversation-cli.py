#!/usr/bin/env python3
"""An explicitly paired local Feishu sender uses Paperclip's Board chat API.

This bridge does not schedule, invoke models, enable features, or send Feishu
messages. Runtime configuration is a private 0600 file outside the repository.
"""

import argparse
import http.client
import json
import os
import re
import signal
import socket
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

API_BASE = "http://127.0.0.1:3100"
BOARD_USER = "local-board"
MAX_INPUT = 65536
MAX_RESPONSE = 2 * 1024 * 1024
BINDING_FIELDS = ("companyId", "agentId", "connectionId", "senderOpenId", "chatId")
TERMINAL_FAILURES = {"failed", "cancelled", "interrupted", "timed_out"}
REQUEST_NAMESPACE = uuid.UUID("483a3d22-02c0-50c4-85a0-f860cd3bffac")


class BridgeError(Exception):
    def __init__(self, code, status="failed", **details):
        self.result = {"ok": False, "status": status, "code": code, **details}
        super().__init__(code)


def parse_json(raw):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise BridgeError("duplicate_json_key")
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except (UnicodeError, ValueError):
        raise BridgeError("invalid_json") from None
    if not isinstance(value, dict):
        raise BridgeError("json_object_required")
    return value


def load_config(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        raise BridgeError("private_config_unavailable") from None
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid not in {0, os.getuid()}):
            raise BridgeError("private_config_permissions")
        raw = handle.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise BridgeError("config_too_large")
    config = parse_json(raw)
    if (config.get("apiBase") != API_BASE
            or config.get("boardUserId") != BOARD_USER
            or config.get("localTrusted") is not True):
        raise BridgeError("local_board_configuration_required")
    if not isinstance(config.get("bindings"), list):
        raise BridgeError("explicit_bindings_required")
    timeout = config.get("timeoutSeconds", 10)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 10:
        raise BridgeError("invalid_timeout")
    return config


def validate_request(request, config):
    if request.get("operation") not in {"send", "status"}:
        raise BridgeError("unsupported_operation")
    for key in (*BINDING_FIELDS, "messageId"):
        value = request.get(key)
        if not isinstance(value, str) or not value or len(value) > 256 or any(ord(c) < 32 for c in value):
            raise BridgeError("invalid_request_identity", field=key)
    text = request.get("text")
    if request["operation"] == "send" and (not isinstance(text, str) or not text.strip()):
        raise BridgeError("message_text_required")
    if text is not None and (not isinstance(text, str) or len(text.encode("utf-8")) > 32768):
        raise BridgeError("invalid_message_text")
    for key in ("commentId", "conversationIssueId"):
        value = request.get(key)
        if value is not None and (not isinstance(value, str) or not value or len(value) > 256
                                  or any(ord(c) < 32 for c in value)):
            raise BridgeError("invalid_receipt_identity", field=key)
    matching = [binding for binding in config["bindings"] if isinstance(binding, dict)
                and all(binding.get(key) == request[key] for key in BINDING_FIELDS)]
    if len(matching) != 1:
        raise BridgeError("sender_binding_not_unique")
    # One owner/Agent cannot silently route its native conversation to two DMs.
    targets = [binding for binding in config["bindings"] if isinstance(binding, dict)
               and binding.get("companyId") == request["companyId"]
               and binding.get("agentId") == request["agentId"]]
    if len(targets) != 1:
        raise BridgeError("conversation_binding_not_unique")


def client_request_id(request):
    identity = json.dumps([request["connectionId"], request["chatId"], request["messageId"]],
                          ensure_ascii=False, separators=(",", ":"))
    return str(uuid.uuid5(REQUEST_NAMESPACE, identity))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BridgeError("api_redirect_rejected")


class BoardAPI:
    def __init__(self, config):
        self.timeout = config.get("timeoutSeconds", 10)
        self.deadline = time.monotonic() + 20
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, method, path, body=None):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeError("api_deadline_exceeded", "unknown")
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(API_BASE + path, data=data, method=method,
                                         headers={"Content-Type": "application/json", "Accept": "application/json"})
        try:
            with self.opener.open(request, timeout=min(self.timeout, remaining)) as response:
                raw = response.read(MAX_RESPONSE + 1)
        except urllib.error.HTTPError as error:
            raise BridgeError("api_http_error", "unknown" if error.code >= 500 else "failed", httpStatus=error.code) from None
        except (TimeoutError, socket.timeout, urllib.error.URLError, OSError, http.client.IncompleteRead):
            raise BridgeError("api_request_unconfirmed", "unknown") from None
        if len(raw) > MAX_RESPONSE:
            raise BridgeError("api_response_too_large", "unknown")
        try:
            return json.loads(raw)
        except (UnicodeError, ValueError):
            raise BridgeError("api_invalid_response", "unknown") from None


def segment(value):
    return urllib.parse.quote(value, safe="")


def verify_board(api):
    health = api.request("GET", "/api/health")
    if not isinstance(health, dict) or health.get("deploymentMode") != "local_trusted":
        raise BridgeError("local_trusted_runtime_required")
    session = api.request("GET", "/api/auth/get-session")
    if (not isinstance(session, dict) or (session.get("user") or {}).get("id") != BOARD_USER
            or (session.get("session") or {}).get("userId") != BOARD_USER):
        raise BridgeError("board_identity_mismatch")
    settings = api.request("GET", "/api/instance/settings/experimental")
    if not isinstance(settings, dict) or settings.get("enableAgentChat") is not True:
        raise BridgeError("agent_chat_disabled")


def verify_conversation(issue, request):
    if (not isinstance(issue, dict) or issue.get("companyId") != request["companyId"]
            or issue.get("conversationAgentId") != request["agentId"]
            or issue.get("assigneeAgentId") != request["agentId"]
            or issue.get("conversationUserId") != BOARD_USER or not issue.get("id")):
        raise BridgeError("conversation_identity_mismatch")


def verify_source(comment, issue, request, request_id):
    if (not isinstance(comment, dict) or comment.get("issueId") != issue["id"]
            or comment.get("companyId") != request["companyId"]
            or comment.get("authorUserId") != BOARD_USER
            or comment.get("clientRequestId") != request_id
            or comment.get("authorAgentId") is not None or comment.get("deletedAt")):
        raise BridgeError("source_comment_identity_mismatch")
    if "text" in request and comment.get("body") != request["text"]:
        raise BridgeError("source_comment_text_mismatch")


def run_belongs(run, issue, request, comment_id):
    if (not isinstance(run, dict) or run.get("companyId") != request["companyId"]
            or run.get("agentId") != request["agentId"]):
        return False
    context = run.get("contextSnapshot") or {}
    ids = [context.get("commentId"), context.get("wakeCommentId"), context.get("sourceCommentId")]
    ids.extend(context.get("wakeCommentIds") or [])
    return context.get("issueId") == issue["id"] and comment_id in ids


def interaction_text(interaction):
    payload = interaction.get("payload") or {}
    if interaction.get("kind") == "ask_user_questions":
        prompts = [q.get("prompt") for q in payload.get("questions", []) if isinstance(q, dict)]
        prompts = [p for p in prompts if isinstance(p, str) and p.strip()]
        if prompts:
            return "\n".join(prompts)[:2000] + "\n请在 Paperclip 对话中回答；飞书暂未接入此问题卡的提交。"
    title = interaction.get("title") or payload.get("title") or "这一步需要你确认。"
    return str(title)[:500] + "\n请在 Paperclip 对话中处理；飞书暂未接入此确认卡的提交。"


def inspect_status(api, issue, request, request_id):
    issue_path = "/api/issues/" + segment(issue["id"])
    if request.get("commentId"):
        source = api.request("GET", issue_path + "/comments/" + segment(request["commentId"]))
    else:
        recent = api.request("GET", issue_path + "/comments?order=desc&limit=200")
        if not isinstance(recent, list):
            raise BridgeError("api_invalid_response")
        matches = [c for c in recent if isinstance(c, dict) and c.get("clientRequestId") == request_id]
        if not matches:
            return {"status": "unknown" if len(recent) >= 200 else "not_found",
                    "code": "source_receipt_not_found"}
        if len(matches) != 1:
            raise BridgeError("source_comment_not_unique")
        source = matches[0]
    verify_source(source, issue, request, request_id)
    base = {"commentId": source["id"]}
    if (source.get("body", "").strip() == "/new"
            and isinstance(source.get("conversationSessionGeneration"), int)
            and source["conversationSessionGeneration"] == issue.get("conversationSessionGeneration")):
        return {**base, "status": "resetComplete", "text": "已开启新对话，历史记录保留。",
                "conversationSessionGeneration": source["conversationSessionGeneration"]}
    if (source.get("conversationSessionGeneration") is not None
            and source["conversationSessionGeneration"] != issue.get("conversationSessionGeneration")):
        return {**base, "status": "superseded", "code": "conversation_session_changed"}
    runs = api.request("GET", "/api/companies/" + segment(request["companyId"])
                       + "/heartbeat-runs?agentId=" + segment(request["agentId"]) + "&limit=200&summary=true")
    if not isinstance(runs, list):
        raise BridgeError("api_invalid_response")
    # List projection omits coalesced wakeCommentIds; inspect the bounded full
    # records of this issue, never infer ownership just from chronological order.
    issue_runs = [r for r in runs if isinstance(r, dict)
                  and (r.get("contextSnapshot") or {}).get("issueId") == issue["id"]]
    candidates = issue_runs[:20]
    matching_runs = []
    superseded = False
    for candidate in candidates:
        run = api.request("GET", "/api/heartbeat-runs/" + segment(candidate["id"]))
        if run_belongs(run, issue, request, source["id"]):
            generation = (run.get("contextSnapshot") or {}).get("conversationSessionGeneration")
            if generation is not None and generation != issue.get("conversationSessionGeneration"):
                superseded = True
                continue
            matching_runs.append(run)
    if not matching_runs:
        if superseded:
            return {**base, "status": "superseded", "code": "conversation_session_changed"}
        if len(issue_runs) > 20 or len(runs) >= 200:
            return {**base, "status": "unknown", "code": "reply_lookup_window_exceeded"}
        return {**base, "status": "pending"}
    # API run lists are newest first. A retry of this turn supersedes its older
    # runs; their progress or completed comments cannot finish the current run.
    latest = matching_runs[0]
    interactions = api.request("GET", issue_path + "/interactions")
    if not isinstance(interactions, list):
        raise BridgeError("api_invalid_response")
    for interaction in interactions:
        if (isinstance(interaction, dict) and interaction.get("companyId") == request["companyId"] and interaction.get("issueId") == issue["id"]
                and interaction.get("sourceRunId") == latest["id"] and interaction.get("createdByAgentId") == request["agentId"]
                and interaction.get("status") == "pending"):
            return {**base, "status": "interaction", "kind": "interaction", "interactionId": interaction["id"],
                    "interactionKind": interaction.get("kind"), "text": interaction_text(interaction)}
    if latest.get("status") in {"queued", "running"}:
        return {**base, "status": "pending", "runId": latest["id"]}
    if latest.get("status") in TERMINAL_FAILURES:
        code = latest.get("errorCode")
        if not isinstance(code, str) or not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,100}", code):
            code = "run_" + latest["status"]
        return {**base, "status": "failed", "runId": latest["id"], "runStatus": latest["status"], "code": code}
    if latest.get("status") == "succeeded":
        comments = api.request("GET", issue_path + "/comments?after=" + segment(source["id"]) + "&order=asc&limit=200")
        if not isinstance(comments, list):
            raise BridgeError("api_invalid_response")
        # IssueComment has no final/progress discriminator. Wait for the Run's
        # terminal success, then select only that Run's final durable comment.
        replies = [c for c in comments if isinstance(c, dict) and c.get("companyId") == request["companyId"]
                   and c.get("issueId") == issue["id"] and c.get("authorAgentId") == request["agentId"]
                   and not c.get("authorUserId") and c.get("createdByRunId") == latest["id"] and not c.get("deletedAt")]
        result_json = latest.get("resultJson") or {}
        decision = result_json.get("presentationDecision") or {}
        if decision.get("schema") == "paperclip.run_presentation_decision.v1":
            # The core explicitly selected this final comment, or selected none.
            replies = [c for c in replies if c.get("id") == decision.get("commentId")]
        else:
            progress_ids = {(r.get("result") or {}).get("commentId")
                            for r in result_json.get("semanticToolReceipts", [])
                            if isinstance(r, dict) and r.get("operationId") == "report_progress"}
            replies = [c for c in replies if c.get("id") not in progress_ids]
        if replies:
            reply = replies[-1]
            return {**base, "status": "replied", "runId": latest["id"], "replyCommentId": reply["id"], "text": reply.get("body", "")}
        return {**base, "status": "unknown", "runId": latest["id"], "code": "run_has_no_durable_reply"}
    return {**base, "status": "pending", "runId": latest["id"]}


def execute(request, config, api=None):
    validate_request(request, config)
    api = api or BoardAPI(config)
    verify_board(api)
    request_id = client_request_id(request)
    chat_path = "/api/companies/" + segment(request["companyId"]) + "/chats/" + segment(request["agentId"])
    issue = api.request("POST" if request["operation"] == "send" else "GET", chat_path)
    base = {"ok": True, "agentId": request["agentId"], "clientRequestId": request_id}
    if issue is None and request["operation"] == "status":
        return {**base, "status": "not_found", "code": "conversation_not_found"}
    verify_conversation(issue, request)
    if request.get("conversationIssueId") and request["conversationIssueId"] != issue["id"]:
        raise BridgeError("conversation_receipt_mismatch")
    base["conversationIssueId"] = issue["id"]
    if request["operation"] == "send":
        comment = api.request("POST", "/api/issues/" + segment(issue["id"]) + "/comments",
                              {"body": request["text"], "clientRequestId": request_id})
        verify_source(comment, issue, request, request_id)
        return {**base, "status": "submitted", "commentId": comment["id"]}
    return {**base, **inspect_status(api, issue, request, request_id)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    def deadline_reached(_signum, _frame):
        raise BridgeError("bridge_deadline_exceeded", "unknown")
    signal.signal(signal.SIGALRM, deadline_reached)
    signal.setitimer(signal.ITIMER_REAL, 20)
    try:
        config = load_config(args.config)
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise BridgeError("request_too_large")
        result = execute(parse_json(raw), config)
    except BridgeError as error:
        result = error.result
    except Exception:
        result = {"ok": False, "status": "unknown", "code": "bridge_internal_error"}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
