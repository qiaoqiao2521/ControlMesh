from __future__ import annotations

import argparse
import copy
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import pwd
import stat
import types
import uuid

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/paperclip/cm-agy"
IDS = {k: str(uuid.uuid5(uuid.NAMESPACE_URL, "cm-agy-test-" + k))
       for k in ("issue", "parent", "company", "agent", "supervisor", "run", "next", "conversation")}


@pytest.fixture(scope="module")
def mod():
    value = types.ModuleType("cm_agy")
    value.__file__ = str(SCRIPT)
    SourceFileLoader(value.__name__, str(SCRIPT)).exec_module(value)
    return value


class FakeAPI:
    def __init__(self):
        self.issue = {"id": IDS["issue"], "companyId": IDS["company"],
                      "assigneeAgentId": IDS["agent"], "parentId": IDS["parent"],
                      "status": "todo", "description": "Complete only this declared child task."}
        self.run = {"id": IDS["run"], "companyId": IDS["company"], "agentId": IDS["agent"],
                    "status": "running", "contextSnapshot": {"issueId": IDS["issue"]}}
        self.parent = {"id": IDS["parent"], "companyId": IDS["company"], "assigneeAgentId": IDS["supervisor"]}
        self.comments, self.calls = [], []
        self.links = [{"issueId": IDS["issue"]}]
        self.lose_patch_response = False
        self.lose_before_patch = False
        self.lose_checkout = False

    def __call__(self, method, path, body=None):
        self.calls.append((method, path, copy.deepcopy(body)))
        if method == "GET":
            if path == "/api/issues/" + IDS["issue"]:
                return copy.deepcopy(self.issue)
            if path == "/api/issues/" + IDS["parent"]:
                return copy.deepcopy(self.parent)
            if path.startswith("/api/heartbeat-runs/"):
                return copy.deepcopy(self.links if path.endswith("/issues") else self.run)
            if path.endswith("/comments"):
                return copy.deepcopy(self.comments)
        if method == "POST" and path.endswith("/checkout"):
            assert body["agentId"] == IDS["agent"]
            self.issue.update(status="in_progress", checkoutRunId=self.run["id"])
            if self.lose_checkout:
                raise ValueError("api_transport_unknown")
            return copy.deepcopy(self.issue)
        if method == "PATCH":
            if self.lose_before_patch:
                raise ValueError("api_transport_unknown")
            self.issue["status"] = body["status"]
            self.comments.append({"id": str(uuid.uuid5(uuid.NAMESPACE_URL, "comment-" + self.run["id"])),
                    "body": body["comment"], "createdByRunId": self.run["id"],
                    "authorAgentId": IDS["agent"], "issueId": IDS["issue"], "companyId": IDS["company"]})
            if self.lose_patch_response:
                raise ValueError("api_transport_unknown")
            return copy.deepcopy(self.issue)
        raise AssertionError((method, path))


@pytest.fixture
def setup(tmp_path, mod, monkeypatch):
    # Exercise the real bounded process helper without Google/model calls.
    if os.geteuid() == 0:
        pytest.skip("live fake-CLI tests must themselves run as an ordinary user")
    api = FakeAPI()
    calls = tmp_path / "cli-calls.jsonl"
    cli = tmp_path / "fake-agy"
    cli.write_text("#!/usr/bin/env python3\nimport json,os,sys\n"
                   f"with open({str(calls)!r},'a') as f: f.write(json.dumps({{'args':sys.argv[1:],'env_keys':sorted(os.environ)}})+'\\n')\n"
                   f"print(json.dumps({{'status':'SUCCESS','conversation_id':{IDS['conversation']!r},'response':'worker evidence ready'}}))\n")
    cli.chmod(0o700)
    env = {**os.environ, "HOME": pwd.getpwuid(os.geteuid()).pw_dir,
           "PAPERCLIP_API_KEY": "fixture-native-run-token", "BW_SESSION": "fixture-vault-secret",
           "GITHUB_TOKEN": "fixture-manager-secret", "ANTHROPIC_AUTH_TOKEN": "fixture-api-override",
           "OPENAI_API_KEY": "fixture-api-override"}
    for key, suffix in (("issue", "TASK_ID"), ("company", "COMPANY_ID"), ("agent", "AGENT_ID"), ("run", "RUN_ID")):
        env["PAPERCLIP_" + suffix] = IDS[key]
    args = argparse.Namespace(agy=str(cli), cwd=str(tmp_path), state_dir=str(tmp_path / "private"),
                              timeout=2, resume_run=None)
    return mod.Worker(args, env, api), api, calls, cli


def ledger(worker):
    return json.loads(worker.store.path.read_text())


def test_success_handoff_is_review_pending_and_private(setup, mod):
    worker, api, calls, _ = setup
    assert worker.execute() is True
    record = ledger(worker)["runs"][IDS["run"]]
    assert record["phase"] == "handed_off"
    assert record["outcome"] == "READY_FOR_REVIEW"
    handoff = json.loads(api.comments[0]["body"].removeprefix(mod.PREFIX))
    assert handoff["approval"] == "PENDING_PARENT_REVIEW"
    assert handoff["result"]["response"] == "worker evidence ready"
    assert api.issue["status"] == "done"
    invocation = json.loads(calls.read_text())
    assert invocation["args"][0:2] == ["--model", mod.MODEL]
    assert "--conversation" not in invocation["args"]
    assert "Complete only this declared child task." in invocation["args"]
    forbidden = {"BW_SESSION", "GITHUB_TOKEN", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY"}
    assert forbidden.isdisjoint(invocation["env_keys"])
    assert not any(k.startswith("PAPERCLIP_") for k in invocation["env_keys"])
    for path in worker.store.root.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_same_run_replay_has_no_model_or_mutation(setup):
    worker, api, calls, _ = setup
    worker.execute()
    before = len(api.calls)
    assert worker.execute() is True
    assert len(calls.read_text().splitlines()) == 1
    assert all(method == "GET" for method, _, _ in api.calls[before:])
    assert len(api.comments) == 1


def test_process_run_without_task_env_resolves_native_issue(setup, mod):
    worker, api, calls, _ = setup
    env = {k: v for k, v in worker.env.items() if k != "PAPERCLIP_TASK_ID"}
    native = mod.Worker(worker.args, env, api)
    assert native.ids["issue"] == IDS["issue"]
    assert native.execute() is True
    assert len(calls.read_text().splitlines()) == len(api.comments) == 1


def test_context_missing_resolves_unique_native_association(setup, mod):
    worker, api, calls, _ = setup
    api.run["contextSnapshot"] = None
    env = {k: v for k, v in worker.env.items() if k != "PAPERCLIP_TASK_ID"}
    native = mod.Worker(worker.args, env, api)
    assert native.execute() is True
    assert len(calls.read_text().splitlines()) == 1


@pytest.mark.parametrize("binding", ["missing", "wrong", "ambiguous", "malformed", "assertion"])
def test_invalid_native_associations_rejected_before_checkout_or_model(setup, mod, binding):
    worker, api, calls, _ = setup
    env = {k: v for k, v in worker.env.items() if k != "PAPERCLIP_TASK_ID"}
    other = str(uuid.uuid4())
    if binding == "missing":
        api.links = []
    elif binding == "wrong":
        api.links = [{"issueId": other}]
    elif binding == "ambiguous":
        api.run["contextSnapshot"] = None
        api.links.append({"issueId": other})
    elif binding == "malformed":
        api.links = [{"issueId": None}]
    else:
        env["PAPERCLIP_TASK_ID"] = other
    with pytest.raises(ValueError):
        mod.Worker(worker.args, env, api)
    assert not calls.exists()
    assert all(method == "GET" for method, _, _ in api.calls)


def test_modified_task_is_not_silently_accepted_on_replay(setup):
    worker, api, calls, _ = setup
    worker.execute()
    api.issue["description"] = "A different task after the first result."
    with pytest.raises(ValueError, match="task_scope_changed_review_required"):
        worker.execute()
    assert len(calls.read_text().splitlines()) == 1


def test_scope_changed_during_model_preserves_result_without_handoff(setup, mod, monkeypatch):
    worker, api, calls, _ = setup
    original = mod.run_cli
    def changed(*args):
        result = original(*args)
        api.issue["description"] = "Changed while the model was working."
        return result
    monkeypatch.setattr(mod, "run_cli", changed)
    with pytest.raises(ValueError, match="task_scope_changed_review_required"):
        worker.execute()
    assert ledger(worker)["runs"][IDS["run"]]["phase"] == "model_complete"
    assert not api.comments
    assert len(calls.read_text().splitlines()) == 1


def test_lost_patch_ack_recovers_from_exact_native_comment(setup):
    worker, api, calls, _ = setup
    api.lose_patch_response = True
    with pytest.raises(ValueError, match="api_transport_unknown"):
        worker.execute()
    assert ledger(worker)["runs"][IDS["run"]]["phase"] == "handoff_attempted"
    before = len(api.calls)
    assert worker.execute() is True
    assert all(method == "GET" for method, _, _ in api.calls[before:])
    assert len(calls.read_text().splitlines()) == len(api.comments) == 1


def test_unknown_patch_without_comment_does_not_resend(setup):
    worker, api, calls, _ = setup
    api.lose_before_patch = True
    with pytest.raises(ValueError):
        worker.execute()
    before = len(api.calls)
    with pytest.raises(ValueError, match="handoff_unknown_read_only_reconciliation"):
        worker.execute()
    assert all(method == "GET" for method, _, _ in api.calls[before:])
    assert len(calls.read_text().splitlines()) == 1
    assert not api.comments


def test_checkout_unknown_never_starts_model_on_retry(setup):
    worker, api, calls, _ = setup
    api.lose_checkout = True
    with pytest.raises(ValueError):
        worker.execute()
    with pytest.raises(ValueError, match="model_attempt_unknown_no_automatic_retry"):
        worker.execute()
    assert not calls.exists()


def test_crash_after_model_start_never_restarts(setup, mod, monkeypatch):
    worker, _, calls, _ = setup
    monkeypatch.setattr(mod, "run_cli", lambda *args: (_ for _ in ()).throw(RuntimeError("simulated crash")))
    with pytest.raises(RuntimeError):
        worker.execute()
    assert ledger(worker)["runs"][IDS["run"]]["phase"] == "model_attempted"
    with pytest.raises(ValueError, match="model_attempt_unknown"):
        worker.execute()
    assert not calls.exists()


def new_round(worker, api, mod, explicit):
    api.run["id"] = IDS["next"]
    api.issue.update(status="todo", checkoutRunId=None, executionRunId=IDS["next"], description="Explicit next round.")
    env = {**worker.env, "PAPERCLIP_RUN_ID": IDS["next"]}
    args = copy.copy(worker.args)
    args.resume_run = IDS["run"] if explicit else None
    return mod.Worker(args, env, api)


def test_new_round_requires_explicit_completed_round(setup, mod):
    worker, api, calls, _ = setup
    worker.execute()
    followup = new_round(worker, api, mod, False)
    with pytest.raises(ValueError):
        followup.execute()
    assert len(calls.read_text().splitlines()) == 1
    assert IDS["next"] not in ledger(worker)["runs"]


def test_explicit_next_round_resumes_exact_provider_conversation(setup, mod):
    worker, api, calls, _ = setup
    worker.execute()
    followup = new_round(worker, api, mod, True)
    assert followup.execute() is True
    invocations = [json.loads(line) for line in calls.read_text().splitlines()]
    assert len(invocations) == 2
    args = invocations[1]["args"]
    assert args[args.index("--conversation") + 1] == IDS["conversation"]
    assert "Explicit next round." in args


@pytest.mark.parametrize("corrupt", ["company", "agent", "issue", "parent_company", "other_checkout"])
def test_cross_identity_rejected_before_checkout_or_model(setup, corrupt):
    worker, api, calls, _ = setup
    other = str(uuid.uuid4())
    if corrupt == "company":
        api.run["companyId"] = other
    elif corrupt == "agent":
        api.issue["assigneeAgentId"] = other
    elif corrupt == "issue":
        api.run["contextSnapshot"]["issueId"] = other
    elif corrupt == "parent_company":
        api.parent["companyId"] = other
    else:
        api.issue["checkoutRunId"] = other
    with pytest.raises(ValueError):
        worker.execute()
    assert not calls.exists()
    assert all(method == "GET" for method, _, _ in api.calls)


def test_false_ack_with_other_author_cannot_be_accepted(setup):
    worker, api, calls, _ = setup
    api.lose_patch_response = True
    with pytest.raises(ValueError):
        worker.execute()
    api.comments[0]["authorAgentId"] = IDS["supervisor"]
    with pytest.raises(ValueError, match="handoff_author_mismatch"):
        worker.execute()
    assert len(calls.read_text().splitlines()) == 1


@pytest.mark.parametrize("output", ["not json", '{"status":"ERROR","response":"secret-error-body"}',
                                   '{"status":"SUCCESS","response":""}'])
def test_exit_zero_without_valid_success_is_failed_handoff(setup, output):
    worker, api, _, cli = setup
    cli.write_text("#!/usr/bin/env python3\nprint(" + repr(output) + ")\n")
    assert worker.execute() is False
    record = ledger(worker)["runs"][IDS["run"]]
    assert record["phase"] == "handed_off"
    assert record["outcome"] == "EXECUTION_FAILED"
    assert "secret-error-body" not in api.comments[0]["body"]


def test_stdout_limit_stops_process_and_bounds_private_log(setup, mod):
    worker, _, _, cli = setup
    cli.write_text("#!/usr/bin/env python3\nimport os,time\nwhile True: os.write(1,b'x'*8192)\n")
    assert worker.execute() is False
    record = ledger(worker)["runs"][IDS["run"]]
    assert record["error"] == "output_limit_exceeded"
    assert (worker.store.root / (IDS["run"] + ".stdout.json")).stat().st_size == mod.LIMIT


def test_timeout_reaps_escaped_child(setup):
    worker, _, _, cli = setup
    marker = Path(worker.args.cwd) / "escaped.pid"
    cli.write_text("#!/usr/bin/env python3\nimport subprocess,sys,time\n"
                   "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],start_new_session=True)\n"
                   f"open({str(marker)!r},'w').write(str(p.pid))\n"
                   "time.sleep(60)\n")
    worker.args.timeout = 1
    assert worker.execute() is False
    assert ledger(worker)["runs"][IDS["run"]]["error"] == "process_timeout"
    pid = int(marker.read_text())
    assert not Path(f"/proc/{pid}").exists()


def test_nonroot_and_home_guard(mod, monkeypatch):
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    with pytest.raises(ValueError, match="nonroot_task_user_required"):
        mod.nonroot_environment({"HOME": "/root"})


def test_wrong_home_is_not_native_auth_migration(mod):
    if os.geteuid() == 0:
        pytest.skip("ordinary user guard")
    with pytest.raises(ValueError, match="task_home_mismatch"):
        mod.nonroot_environment({"HOME": "/root"})


@pytest.mark.parametrize("base", ["https://example.com", "http://127.0.0.1:3100/api", "http://user@localhost:3100"])
def test_api_cannot_forward_run_token_to_remote_or_userinfo(mod, base):
    with pytest.raises(ValueError, match="local_api_required"):
        mod.API({"PAPERCLIP_API_URL": base, "PAPERCLIP_API_KEY": "fixture"})


def test_symlink_state_refused(mod, tmp_path):
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    link = tmp_path / "linked"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="state_symlink_refused"):
        mod.Store(link, IDS["issue"])
