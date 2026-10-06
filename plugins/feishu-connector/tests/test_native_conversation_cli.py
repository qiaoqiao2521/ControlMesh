"""Contract tests use a mock API; no runtime, model, or Feishu message is called."""

import copy
import importlib.util
import http.client
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error


MODULE_PATH = Path(__file__).resolve().parents[1] / "native-conversation-cli.py"
spec = importlib.util.spec_from_file_location("native_conversation_cli", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def configuration():
    return {"apiBase": bridge.API_BASE, "boardUserId": bridge.BOARD_USER, "localTrusted": True,
            "bindings": [{"companyId": "company-a", "agentId": "agent-a", "connectionId": "bot-a",
                          "senderOpenId": "user-a", "chatId": "dm-a"}]}


def message(operation="send"):
    return {"operation": operation, **configuration()["bindings"][0], "messageId": "message-a", "text": "接着刚才的任务。"}


class APIStub:
    def __init__(self, request=None):
        request = request or message()
        self.calls = []
        self.issue = {"id": "conversation-a", "companyId": request["companyId"],
                      "conversationAgentId": request["agentId"], "assigneeAgentId": request["agentId"],
                      "conversationUserId": bridge.BOARD_USER, "conversationSessionGeneration": 0}
        self.source = {"id": "comment-a", "issueId": self.issue["id"], "companyId": request["companyId"],
                       "authorUserId": bridge.BOARD_USER, "authorAgentId": None,
                       "clientRequestId": bridge.client_request_id(request), "body": request["text"]}
        self.runs = []
        self.replies = []
        self.interactions = []
        self.health = {"deploymentMode": "local_trusted"}
        self.session = {"user": {"id": bridge.BOARD_USER}, "session": {"userId": bridge.BOARD_USER}}
        self.enabled = True

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if path == "/api/health":
            return self.health
        if path == "/api/auth/get-session":
            return self.session
        if path == "/api/instance/settings/experimental":
            return {"enableAgentChat": self.enabled}
        if "/chats/" in path:
            return self.issue
        if path.endswith("/comments") and method == "POST":
            return self.source
        if path.endswith("/comments/comment-a"):
            return self.source
        if "comments?order=desc" in path:
            return [self.source, *self.replies]
        if "comments?after=" in path:
            return self.replies
        if "/heartbeat-runs?" in path:
            return self.runs
        if path.startswith("/api/heartbeat-runs/"):
            return next(r for r in self.runs if r["id"] == path.rsplit("/", 1)[-1])
        if path.endswith("/interactions"):
            return self.interactions
        raise AssertionError((method, path))


def run(source="comment-a", agent="agent-a", state="succeeded", run_id="run-a", generation=0):
    return {"id": run_id, "companyId": "company-a", "agentId": agent, "status": state,
            "contextSnapshot": {"issueId": "conversation-a", "wakeCommentId": source,
                                "conversationSessionGeneration": generation}}


def reply(run_id="run-a", agent="agent-a", body="已检查，现在继续。"):
    return {"id": "reply-a", "companyId": "company-a", "issueId": "conversation-a", "body": body,
            "authorAgentId": agent, "authorUserId": None, "createdByRunId": run_id}


class ConversationContractTest(unittest.TestCase):
    def test_core_presentation_decision_selects_final_instead_of_later_progress(self):
        api = APIStub(message("status"))
        final = reply(body="已交付最终成果。")
        progress = {**reply(body="补充进度。"), "id": "progress-a"}
        api.runs = [{**run(), "resultJson": {"presentationDecision": {
            "schema": "paperclip.run_presentation_decision.v1", "commentId": final["id"]}}}]
        api.replies = [final, progress]
        self.assertEqual(bridge.execute(message("status"), configuration(), api)["text"], final["body"])

    def test_success_without_core_final_never_delivers_progress(self):
        for result_json in (
            {"presentationDecision": {"schema": "paperclip.run_presentation_decision.v1", "commentId": None}},
            {"semanticToolReceipts": [{"operationId": "report_progress", "result": {"commentId": "reply-a"}}]},
        ):
            api = APIStub(message("status"))
            api.runs = [{**run(), "resultJson": result_json}]
            api.replies = [reply(body="我正在处理。")]
            with self.subTest(result=result_json):
                self.assertEqual(bridge.execute(message("status"), configuration(), api)["status"], "unknown")

    def test_send_uses_native_comments_without_extra_invoke(self):
        api = APIStub()
        result = bridge.execute(message(), configuration(), api)
        self.assertEqual(result["status"], "submitted")
        posts = [c for c in api.calls if c[0] == "POST"]
        self.assertEqual([c[1] for c in posts], ["/api/companies/company-a/chats/agent-a", "/api/issues/conversation-a/comments"])
        self.assertEqual(posts[1][2], {"body": message()["text"], "clientRequestId": bridge.client_request_id(message())})

    def test_duplicate_message_reuses_client_id_and_different_message_does_not(self):
        api = APIStub()
        first = bridge.execute(message(), configuration(), api)
        second = bridge.execute(message(), configuration(), api)
        self.assertEqual(first["clientRequestId"], second["clientRequestId"])
        changed = {**message(), "messageId": "message-b"}
        self.assertNotEqual(first["clientRequestId"], bridge.client_request_id(changed))
        changed_bot = {**message(), "connectionId": "bot-b"}
        self.assertNotEqual(first["clientRequestId"], bridge.client_request_id(changed_bot))

    def test_unknown_sender_is_rejected_before_any_api_call(self):
        api = APIStub()
        with self.assertRaises(bridge.BridgeError) as caught:
            bridge.execute({**message(), "senderOpenId": "stranger"}, configuration(), api)
        self.assertEqual(caught.exception.result["code"], "sender_binding_not_unique")
        self.assertEqual(api.calls, [])

    def test_ambiguous_binding_is_rejected(self):
        config = configuration()
        config["bindings"].append(copy.deepcopy(config["bindings"][0]))
        with self.assertRaises(bridge.BridgeError):
            bridge.execute(message(), config, APIStub())

    def test_shared_native_conversation_cannot_route_to_two_dms(self):
        config = configuration()
        config["bindings"].append({**config["bindings"][0], "chatId": "dm-b"})
        with self.assertRaises(bridge.BridgeError) as caught:
            bridge.execute(message(), config, APIStub())
        self.assertEqual(caught.exception.result["code"], "conversation_binding_not_unique")

    def test_two_agents_have_distinct_conversations(self):
        config = configuration()
        other = {**config["bindings"][0], "agentId": "agent-b", "connectionId": "bot-b", "chatId": "dm-b"}
        config["bindings"].append(other)
        request = {**message(), **other}
        api = APIStub(request)
        api.issue["id"] = "conversation-b"
        api.source["issueId"] = "conversation-b"
        result = bridge.execute(request, config, api)
        self.assertEqual(result["conversationIssueId"], "conversation-b")
        self.assertIn(("POST", "/api/companies/company-a/chats/agent-b", None), api.calls)

    def test_wrong_board_identity_and_disabled_feature_never_send(self):
        for mutation, expected in (("identity", "board_identity_mismatch"), ("feature", "agent_chat_disabled"),
                                   ("mode", "local_trusted_runtime_required")):
            api = APIStub()
            if mutation == "identity":
                api.session["user"]["id"] = "other-board"
            elif mutation == "feature":
                api.enabled = False
            else:
                api.health["deploymentMode"] = "authenticated"
            with self.subTest(mutation=mutation), self.assertRaises(bridge.BridgeError) as caught:
                bridge.execute(message(), configuration(), api)
            self.assertEqual(caught.exception.result["code"], expected)
            self.assertFalse(any(c[0] == "POST" for c in api.calls))

    def test_conversation_owner_and_assignee_are_checked(self):
        for key, value in (("companyId", "other-company"), ("conversationUserId", "other-user"),
                           ("conversationAgentId", "agent-b"), ("assigneeAgentId", "agent-b")):
            api = APIStub()
            api.issue[key] = value
            with self.subTest(key=key), self.assertRaises(bridge.BridgeError):
                bridge.execute(message(), configuration(), api)
            self.assertFalse(any(c[1].endswith("/comments") for c in api.calls))

    def test_status_recovers_lost_receipt_without_any_post(self):
        request = message("status")
        api = APIStub(request)
        api.runs = [run()]
        api.replies = [reply()]
        result = bridge.execute(request, configuration(), api)
        self.assertEqual(result["status"], "replied")
        self.assertEqual(result["text"], reply()["body"])
        self.assertEqual(result["commentId"], "comment-a")
        self.assertTrue(all(c[0] == "GET" for c in api.calls))

    def test_source_receipt_must_match_message_identity(self):
        request = {**message("status"), "commentId": "comment-a"}
        api = APIStub(request)
        api.source["clientRequestId"] = "unrelated-request"
        with self.assertRaises(bridge.BridgeError) as caught:
            bridge.execute(request, configuration(), api)
        self.assertEqual(caught.exception.result["code"], "source_comment_identity_mismatch")

    def test_reply_requires_exact_run_and_agent_not_chronological_guess(self):
        for candidate in (reply(run_id="another-turn"), reply(agent="agent-b")):
            api = APIStub(message("status"))
            api.runs = [run(state="running")]
            api.replies = [candidate]
            with self.subTest(reply=candidate):
                result = bridge.execute(message("status"), configuration(), api)
                self.assertEqual(result["status"], "pending")
                self.assertNotIn("text", result)

    def test_coalesced_message_ids_use_full_run_not_list_projection(self):
        api = APIStub(message("status"))
        full = run(source="older-comment")
        full["contextSnapshot"]["wakeCommentIds"] = ["older-comment", "comment-a"]
        api.runs = [full]
        api.replies = [reply()]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "replied")

    def test_previous_turn_run_never_owns_current_reply(self):
        api = APIStub(message("status"))
        api.runs = [run(source="prior-turn-comment")]
        api.replies = [reply()]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "pending")

    def test_reset_completion_requires_native_generation(self):
        request = {**message("status"), "text": "/new"}
        api = APIStub(request)
        api.issue["conversationSessionGeneration"] = 1
        api.source["conversationSessionGeneration"] = 1
        result = bridge.execute(request, configuration(), api)
        self.assertEqual(result["status"], "resetComplete")
        self.assertIn("历史记录保留", result["text"])
        self.assertFalse(any("heartbeat-runs" in c[1] for c in api.calls))

    def test_new_generation_never_returns_old_reply(self):
        api = APIStub(message("status"))
        api.issue["conversationSessionGeneration"] = 1
        api.runs = [run(generation=0)]
        api.replies = [reply()]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "superseded")
        self.assertNotIn("text", result)

    def test_failed_run_returns_specific_safe_code_without_raw_error(self):
        api = APIStub(message("status"))
        api.runs = [{**run(state="failed"), "errorCode": "authentication_required", "error": "token=private"}]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["code"], "authentication_required")
        self.assertNotIn("private", json.dumps(result))

    def test_native_question_is_visible_without_claiming_feishu_buttons(self):
        api = APIStub(message("status"))
        api.runs = [run()]
        api.interactions = [{"id": "question-a", "companyId": "company-a", "issueId": "conversation-a",
                             "createdByAgentId": "agent-a", "sourceRunId": "run-a", "status": "pending",
                             "kind": "ask_user_questions", "payload": {"questions": [{"prompt": "要交付哪个项目？"}]}}]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["kind"], "interaction")
        self.assertIn("要交付哪个项目", result["text"])
        self.assertIn("暂未接入", result["text"])

    def test_succeeded_without_durable_output_is_unknown(self):
        api = APIStub(message("status"))
        api.runs = [run()]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "run_has_no_durable_reply")

    def test_running_progress_comment_is_not_a_final_reply(self):
        api = APIStub(message("status"))
        api.runs = [run(state="running")]
        api.replies = [reply(body="正在检查配置。")]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "pending")
        self.assertNotIn("text", result)

    def test_failed_run_progress_cannot_hide_failure(self):
        api = APIStub(message("status"))
        api.runs = [{**run(state="failed"), "errorCode": "authentication_required"}]
        api.replies = [reply(body="已开始处理。")]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["code"], "authentication_required")
        self.assertNotIn("text", result)

    def test_retry_running_does_not_deliver_previous_completed_run_reply(self):
        api = APIStub(message("status"))
        api.runs = [run(state="running", run_id="run-retry"), run(run_id="run-old")]
        api.replies = [reply(run_id="run-old", body="上一轮已经完成。")]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["runId"], "run-retry")
        self.assertNotIn("text", result)

    def test_history_window_exhaustion_does_not_guess_pending_or_reply(self):
        api = APIStub(message("status"))
        api.runs = [run(source="older-comment", run_id="run-" + str(i)) for i in range(21)]
        result = bridge.execute(message("status"), configuration(), api)
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["code"], "reply_lookup_window_exceeded")


class PrivateConfigAndHTTPTest(unittest.TestCase):
    def test_private_file_required_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(configuration()))
            path.chmod(0o600)
            self.assertEqual(bridge.load_config(path)["boardUserId"], bridge.BOARD_USER)
            link = Path(directory) / "link.json"
            link.symlink_to(path)
            with self.assertRaises(bridge.BridgeError):
                bridge.load_config(link)
            path.chmod(0o644)
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.load_config(path)
            self.assertEqual(caught.exception.result["code"], "private_config_permissions")

    def test_only_explicit_local_runtime_allowed(self):
        for key, value in (("apiBase", "https://other.example"), ("boardUserId", "someone"), ("localTrusted", False)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                config = {**configuration(), key: value}
                path = Path(directory) / "config.json"
                path.write_text(json.dumps(config))
                path.chmod(0o600)
                with self.assertRaises(bridge.BridgeError):
                    bridge.load_config(path)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.parse_json('{"operation":"send","operation":"status"}')

    def test_cli_input_limit_and_json_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(configuration()))
            path.chmod(0o600)
            oversized = subprocess.run([sys.executable, str(MODULE_PATH), "--config", str(path)],
                                       input=b" " * (bridge.MAX_INPUT + 1), capture_output=True)
            self.assertEqual(oversized.returncode, 1)
            self.assertEqual(json.loads(oversized.stdout)["code"], "request_too_large")
            self.assertEqual(oversized.stderr, b"")
            stranger = {**message(), "senderOpenId": "stranger"}
            refused = subprocess.run([sys.executable, str(MODULE_PATH), "--config", str(path)],
                                     input=json.dumps(stranger).encode(), capture_output=True)
            self.assertEqual(refused.returncode, 1)
            self.assertEqual(json.loads(refused.stdout)["code"], "sender_binding_not_unique")
            self.assertEqual(refused.stderr, b"")

    def test_large_message_rejected_before_api(self):
        api = APIStub()
        with self.assertRaises(bridge.BridgeError) as caught:
            bridge.execute({**message(), "text": "字" * 11000}, configuration(), api)
        self.assertEqual(caught.exception.result["code"], "invalid_message_text")
        self.assertEqual(api.calls, [])

    def test_post_timeout_is_unknown_and_is_not_retried(self):
        api = bridge.BoardAPI(configuration())
        api.opener = Mock()
        api.opener.open.side_effect = socket.timeout("secret URL or token")
        with self.assertRaises(bridge.BridgeError) as caught:
            api.request("POST", "/api/issues/test/comments", {"body": "hello"})
        self.assertEqual(caught.exception.result["status"], "unknown")
        self.assertNotIn("secret", json.dumps(caught.exception.result))
        self.assertEqual(api.opener.open.call_count, 1)

    def test_get_timeout_is_unknown_without_claiming_run_failure(self):
        api = bridge.BoardAPI(configuration())
        api.opener = Mock()
        api.opener.open.side_effect = urllib.error.URLError("private information")
        with self.assertRaises(bridge.BridgeError) as caught:
            api.request("GET", "/api/health")
        self.assertEqual(caught.exception.result["status"], "unknown")

    def test_overall_deadline_bounds_multiple_api_reads(self):
        api = bridge.BoardAPI(configuration())
        api.opener = Mock()
        with patch.object(bridge.time, "monotonic", return_value=api.deadline + 1):
            with self.assertRaises(bridge.BridgeError) as caught:
                api.request("GET", "/api/health")
        self.assertEqual(caught.exception.result["status"], "unknown")
        self.assertEqual(caught.exception.result["code"], "api_deadline_exceeded")
        api.opener.open.assert_not_called()

    def test_preflight_and_http_4xx_are_definite_failure(self):
        api = bridge.BoardAPI(configuration())
        api.opener = Mock()
        api.opener.open.side_effect = urllib.error.HTTPError(bridge.API_BASE, 403, "private", {}, None)
        with self.assertRaises(bridge.BridgeError) as caught:
            api.request("POST", "/api/issues/test/comments", {"body": "hello"})
        self.assertEqual(caught.exception.result["status"], "failed")
        self.assertEqual(caught.exception.result["httpStatus"], 403)
        preflight = APIStub()
        preflight.enabled = False
        with self.assertRaises(bridge.BridgeError) as caught:
            bridge.execute(message(), configuration(), preflight)
        self.assertEqual(caught.exception.result["status"], "failed")

    def test_post_server_failure_or_incomplete_receipt_is_unknown(self):
        failures = [urllib.error.HTTPError(bridge.API_BASE, 502, "private", {}, None),
                    http.client.IncompleteRead(b"private", 100)]
        for failure in failures:
            api = bridge.BoardAPI(configuration())
            api.opener = Mock()
            api.opener.open.side_effect = failure
            with self.subTest(error=type(failure).__name__), self.assertRaises(bridge.BridgeError) as caught:
                api.request("POST", "/api/issues/test/comments", {"body": "hello"})
            self.assertEqual(caught.exception.result["status"], "unknown")
            self.assertEqual(api.opener.open.call_count, 1)

    def test_redirect_to_external_host_is_rejected(self):
        with self.assertRaises(bridge.BridgeError) as caught:
            bridge.NoRedirect().redirect_request(None, None, 302, "", {}, "http://external.example")
        self.assertEqual(caught.exception.result["code"], "api_redirect_rejected")


if __name__ == "__main__":
    unittest.main()
