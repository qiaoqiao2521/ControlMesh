from __future__ import annotations

from datetime import datetime, timedelta, UTC
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
import types
from unittest.mock import MagicMock

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "paperclip" / "cm-process-runner"


@pytest.fixture(scope="module")
def runner_mod():
    mod = types.ModuleType("cm_process_runner")
    SourceFileLoader(mod.__name__, str(SCRIPT_PATH)).exec_module(mod)
    return mod


@pytest.fixture
def api(runner_mod, monkeypatch):
    calls = []
    responses = {
        "/api/heartbeat-runs/run-1": {
            "id": "run-1",
            "companyId": "company-1",
            "agentId": "agent-1",
            "contextSnapshot": {"issueId": "issue-1"},
        },
        "/api/heartbeat-runs/run-1/issues": [{"issueId": "issue-1", "title": "mutable-title"}],
        "/api/issues/issue-1": {
            "id": "issue-1",
            "companyId": "company-1",
            "assigneeAgentId": "agent-1",
            "title": "mutable-title",
            "originKind": "routine_execution",
            "originId": "routine-1",
        },
        "/api/routines/routine-1": {
            "id": "routine-1",
            "companyId": "company-1",
            "assigneeAgentId": "agent-1",
            "variables": [{"name": "cmJobId", "type": "text", "defaultValue": "job-1"}],
        },
    }

    def call(method, path, payload=None, **kwargs):
        calls.append((method, path, payload))
        result = responses.get(path, {}) if method == "GET" else {}
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(runner_mod, "api_call", call)
    return calls, responses


def statuses(calls):
    return [payload["status"] for method, _, payload in calls if method == "PATCH"]


def configure_job(tmp_path, notify="anomaly", publish=None):
    (tmp_path / "cron_jobs.json").write_text(
        json.dumps(
            {"jobs": [{"id": "job-1", "task_folder": "job-1", "quiet_start": 0, "quiet_end": 0}]}
        )
    )
    task = tmp_path / "workspace" / "cron_tasks" / "job-1"
    (task / "output").mkdir(parents=True)
    (task / "task.config.json").write_text(
        json.dumps(
            {
                "delivery": {"notify_when": notify, "primary": "feishu"},
                "publish": publish or {"enabled": False},
            }
        )
    )
    return task


def execute(runner_mod, tmp_path):
    return runner_mod.execute_cron_job(
        "job-1", "issue-1", "run-1", tmp_path, Path("/unused/controlmesh"), "http://local", None
    )


def native_env(monkeypatch, tmp_path, argv=None):
    for key in ("PAPERCLIP_TASK_ID", "CM_CONTROLLED_TRIAL_TITLE", "PAPERCLIP_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    for key, val in {
        "CONTROLMESH_HOME": str(tmp_path),
        "PAPERCLIP_RUN_ID": "run-1",
        "PAPERCLIP_COMPANY_ID": "company-1",
        "PAPERCLIP_AGENT_ID": "agent-1",
    }.items():
        monkeypatch.setenv(key, val)
    monkeypatch.setattr(sys, "argv", ["runner", *(argv or [])])


def artifact_execution(runner_mod, monkeypatch, task, changes=None):
    def run(cmd, timeout_seconds=600):
        assert cmd[-2:] == ["--json", "--no-notify"]
        data = {
            "status": "success",
            "written_at": datetime.now(UTC).isoformat(),
            "result_text": "PRIVATE_FULL_RESULT_正文",
            "provider": "codex",
            "model": "example",
        }
        data.update(changes or {})
        (task / "output" / "last_run.json").write_text(json.dumps(data))
        return None, 0

    mock = MagicMock(side_effect=run)
    monkeypatch.setattr(runner_mod, "run_owned_process", mock)
    return mock


def test_quiet_hours(runner_mod):
    for dt in (
        datetime(2026, 10, 1, 14, 30, tzinfo=UTC),
        datetime(2026, 9, 30, 23, 15, tzinfo=UTC),
    ):
        assert runner_mod.is_in_quiet_hours(dt, 21, 8, "Asia/Shanghai")
    assert not runner_mod.is_in_quiet_hours(
        datetime(2026, 10, 1, 2, tzinfo=UTC), 21, 8, "Asia/Shanghai"
    )
    assert not runner_mod.is_in_quiet_hours(datetime.now(UTC), 0, 0, "UTC")


def test_watermark_retains_other_fields(runner_mod, tmp_path):
    configure_job(tmp_path)
    runner_mod.update_cron_registry_watermark(
        tmp_path / "cron_jobs.json", "job-1", "success", "2026-10-01T00:00:00Z"
    )
    job = json.loads((tmp_path / "cron_jobs.json").read_text())["jobs"][0]
    assert job["task_folder"] == "job-1"
    assert job["last_run_status"] == job["manual_run_status"] == "success"
    assert job["last_run_at"] == job["manual_run_at"] == "2026-10-01T00:00:00Z"
    assert (tmp_path / "cron_jobs.json").stat().st_mode & 0o777 == 0o600


def test_api_call_headers_and_no_error_body(runner_mod, monkeypatch):
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.read.return_value = b'{"status":"ok"}'
    mock = MagicMock(return_value=resp)
    monkeypatch.setattr(runner_mod.urllib.request, "urlopen", mock)
    assert runner_mod.api_call(
        "GET", "/api/health", api_base="http://local", token="secret", run_id="run-1"
    ) == {"status": "ok"}
    request = mock.call_args.args[0]
    assert request.get_header("X-paperclip-run-id") == "run-1"
    import io

    mock.side_effect = runner_mod.urllib.error.HTTPError(
        "http://local", 403, "private", {}, io.BytesIO(b"PRIVATE_RESPONSE_SECRET")
    )
    with pytest.raises(RuntimeError, match="api_http_403") as exc:
        runner_mod.api_call("GET", "/api/health", api_base="http://local")
    assert "PRIVATE" not in str(exc.value)


def test_native_context_issue_is_authoritative(runner_mod, tmp_path, monkeypatch, api):
    calls, responses = api
    configure_job(tmp_path)
    native_env(monkeypatch, tmp_path)
    responses["/api/heartbeat-runs/run-1/issues"].insert(
        0, {"issueId": "other-issue", "title": "job-1"}
    )
    execute_mock = MagicMock(return_value=0)
    monkeypatch.setattr(runner_mod, "execute_cron_job", execute_mock)
    assert runner_mod.main() == 0
    assert execute_mock.call_args.args[:3] == ("job-1", "issue-1", "run-1")
    assert ("GET", "/api/issues/other-issue", None) not in calls


@pytest.mark.parametrize(
    ("links", "expected"),
    [([{"issueId": "issue-1"}], 0), ([{"issueId": "issue-1"}, {"issueId": "other"}], 1), ([], 1)],
)
def test_context_missing_requires_unique_association(
    runner_mod, tmp_path, monkeypatch, api, links, expected
):
    calls, responses = api
    configure_job(tmp_path)
    native_env(monkeypatch, tmp_path)
    responses["/api/heartbeat-runs/run-1"]["contextSnapshot"] = {}
    responses["/api/heartbeat-runs/run-1/issues"] = links
    launch = MagicMock(return_value=0)
    monkeypatch.setattr(runner_mod, "execute_cron_job", launch)
    assert runner_mod.main() == expected
    assert launch.call_count == (expected == 0)
    if expected:
        assert not statuses(calls)  # Never mutate an unverified association.


@pytest.mark.parametrize(
    "kind",
    [
        "run_company",
        "run_agent",
        "ctx_mismatch",
        "issue_company",
        "issue_assignee",
        "issue_missing_company",
        "issue_missing_assignee",
        "issue_malformed",
        "issue_read_failed",
    ],
)
def test_native_identity_rejects_explicit_job_bypass(runner_mod, tmp_path, monkeypatch, api, kind):
    calls, responses = api
    configure_job(tmp_path)
    native_env(monkeypatch, tmp_path, ["--job", "job-1"])
    run = responses["/api/heartbeat-runs/run-1"]
    issue = responses["/api/issues/issue-1"]
    if kind == "run_company":
        run["companyId"] = "other"
    elif kind == "run_agent":
        run["agentId"] = "other"
    elif kind == "ctx_mismatch":
        run["contextSnapshot"]["issueId"] = "other"
    elif kind == "issue_company":
        issue["companyId"] = "other"
    elif kind == "issue_assignee":
        issue["assigneeAgentId"] = "other"
    elif kind == "issue_missing_company":
        issue.pop("companyId")
    elif kind == "issue_missing_assignee":
        issue.pop("assigneeAgentId")
    elif kind == "issue_malformed":
        responses["/api/issues/issue-1"] = []
    else:
        responses["/api/issues/issue-1"] = RuntimeError("PRIVATE_API_BODY")
    launch = MagicMock()
    monkeypatch.setattr(runner_mod, "execute_cron_job", launch)
    assert runner_mod.main() == 1
    launch.assert_not_called()
    assert not statuses(calls)


@pytest.mark.parametrize(
    "kind",
    ["no_origin", "no_mapping", "multiple_mapping", "routine_wrong_owner", "explicit_mismatch"],
)
def test_native_titles_cannot_authorize_cron(runner_mod, tmp_path, monkeypatch, api, kind):
    calls, responses = api
    configure_job(tmp_path)
    native_env(monkeypatch, tmp_path, ["--job", "other-job"] if kind == "explicit_mismatch" else [])
    responses["/api/issues/issue-1"]["title"] = "job-1"
    routine = responses["/api/routines/routine-1"]
    if kind == "no_origin":
        responses["/api/issues/issue-1"].pop("originId")
    elif kind == "no_mapping":
        routine["variables"] = []
    elif kind == "multiple_mapping":
        routine["variables"] *= 2
    elif kind == "routine_wrong_owner":
        routine["assigneeAgentId"] = "other"
    launch = MagicMock()
    monkeypatch.setattr(runner_mod, "execute_cron_job", launch)
    assert runner_mod.main() == 1
    launch.assert_not_called()
    assert statuses(calls) == ["blocked"]


def test_controlled_trial_requires_explicit_host_permit_and_real_metrics(
    runner_mod, tmp_path, monkeypatch, api
):
    calls, responses = api
    native_env(monkeypatch, tmp_path)
    issue = responses["/api/issues/issue-1"]
    issue.update(title="host7-controlled-trial", originKind="manual", originId=None)
    assert runner_mod.main() == 1
    assert not (tmp_path / "workspace" / "output").exists()
    monkeypatch.setenv("CM_CONTROLLED_TRIAL_TITLE", "host7-controlled-trial")
    assert runner_mod.main() == 0
    artifact = json.loads(
        (tmp_path / "workspace" / "output" / "trial-issue-1-run-1.json").read_text()
    )
    assert artifact["metrics"]["uptime_sec"] > 0
    assert artifact["metrics"]["disk_free_bytes"] > 0
    assert artifact["run_id"] == "run-1"
    assert statuses(calls)[-1] == "done"


def test_missing_artifact_does_not_pass_exit_zero(runner_mod, tmp_path, monkeypatch, api):
    configure_job(tmp_path)
    launch = MagicMock(return_value=(None, 0))
    monkeypatch.setattr(runner_mod, "run_owned_process", launch)
    assert execute(runner_mod, tmp_path) == 1
    launch.assert_called_once()
    assert statuses(api[0]) == ["in_progress", "blocked"]


@pytest.mark.parametrize(
    "changes",
    [
        {"written_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat()},
        {"written_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()},
        {"written_at": "2026-10-01T00:00:00"},
        {"status": "failed"},
        {"dry_run": True},
        {"result_text": ""},
        {"provider": None},
    ],
)
def test_artifact_guard_rejects_stale_future_and_non_result(
    runner_mod, tmp_path, monkeypatch, api, changes
):
    task = configure_job(tmp_path)
    launch = artifact_execution(runner_mod, monkeypatch, task, changes)
    assert execute(runner_mod, tmp_path) == 1
    launch.assert_called_once()
    assert statuses(api[0])[-1] == "blocked"
    assert "done" not in statuses(api[0])


def test_fresh_ops_saved_completely_and_never_uploaded(runner_mod, tmp_path, monkeypatch, api):
    task = configure_job(tmp_path)
    artifact_execution(runner_mod, monkeypatch, task)
    assert execute(runner_mod, tmp_path) == 0
    saved = task / "output" / "paperclip-runs" / "run-1.json"
    data = json.loads(saved.read_text())
    assert data["artifact"]["result_text"] == "PRIVATE_FULL_RESULT_正文"
    assert data["started_at"] <= data["artifact"]["written_at"] <= data["finished_at"]
    assert saved.stat().st_mode & 0o777 == 0o600
    assert statuses(api[0]) == ["in_progress", "done"]
    assert "PRIVATE_FULL_RESULT" not in json.dumps(api[0])
    assert "risk_judgment_unverified" in json.dumps(api[0])


@pytest.mark.parametrize(
    ("notify", "publish"),
    [
        ("always", {"enabled": False}),
        ("anomaly", {"enabled": True, "mode": "direct_result", "require_review": False}),
    ],
)
def test_business_generation_is_preserved_but_not_fake_delivered(
    runner_mod, tmp_path, monkeypatch, api, notify, publish
):
    task = configure_job(tmp_path, notify, publish)
    launch = artifact_execution(runner_mod, monkeypatch, task)
    assert execute(runner_mod, tmp_path) == 1
    launch.assert_called_once()
    data = json.loads((task / "output" / "paperclip-runs" / "run-1.json").read_text())
    assert data["artifact"]["result_text"] == "PRIVATE_FULL_RESULT_正文"
    assert statuses(api[0]) == ["in_progress", "blocked"]
    assert "business_delivery_pending" in json.dumps(api[0])
    assert "PRIVATE_FULL_RESULT" not in json.dumps(api[0])


@pytest.mark.parametrize(
    ("notify", "publish"),
    [
        (None, {"enabled": False}),
        ("always", {"enabled": True, "mode": "external", "require_review": False}),
        ("always", {"enabled": True, "mode": "direct_result", "require_review": True}),
    ],
)
def test_unknown_policy_and_external_publish_fail_before_model(
    runner_mod, tmp_path, monkeypatch, api, notify, publish
):
    configure_job(tmp_path, notify, publish)
    launch = MagicMock()
    monkeypatch.setattr(runner_mod, "run_owned_process", launch)
    assert execute(runner_mod, tmp_path) == 1
    launch.assert_not_called()
    assert statuses(api[0]) == ["blocked"]


def test_quiet_skip_precedes_model_and_preserves_watermark(runner_mod, tmp_path, monkeypatch, api):
    configure_job(tmp_path, notify=None)
    launch = MagicMock()
    monkeypatch.setattr(runner_mod, "run_owned_process", launch)
    monkeypatch.setattr(runner_mod, "is_in_quiet_hours", lambda *_args: True)
    assert execute(runner_mod, tmp_path) == 0
    launch.assert_not_called()
    assert statuses(api[0]) == ["done"]
    assert (
        json.loads((tmp_path / "cron_jobs.json").read_text())["jobs"][0]["last_run_status"]
        == "skipped_quiet_hours"
    )


def test_comment_error_cannot_prevent_blocked_or_expose_raw_output(
    runner_mod, tmp_path, monkeypatch, capsys
):
    configure_job(tmp_path)
    calls = []

    def api_call(method, path, payload=None, **kwargs):
        calls.append((method, path, payload))
        if method == "POST":
            raise RuntimeError("PRIVATE_EXCEPTION_BODY")
        return {}

    monkeypatch.setattr(runner_mod, "api_call", api_call)
    monkeypatch.setattr(runner_mod, "run_owned_process", lambda *_args: ("process_timeout", None))
    assert execute(runner_mod, tmp_path) == 1
    assert statuses(calls) == ["in_progress", "blocked"]
    assert "PRIVATE" not in json.dumps(calls) + capsys.readouterr().err


def test_spawn_oserror_has_terminal_failure(runner_mod, tmp_path, api):
    configure_job(tmp_path)
    assert (
        runner_mod.execute_cron_job(
            "job-1", "issue-1", "run-1", tmp_path, tmp_path / "missing-cli", "http://local", None
        )
        == 1
    )
    assert statuses(api[0]) == ["in_progress", "blocked"]
    assert "process_spawn_failed" in json.dumps(api[0])


def test_done_patch_failure_attempts_independent_blocked(runner_mod, tmp_path, monkeypatch):
    calls = []

    def api_call(method, path, payload=None, **kwargs):
        calls.append((method, path, payload))
        if method == "PATCH" and payload["status"] == "done":
            raise RuntimeError("PRIVATE_RESPONSE_BODY")
        return {}

    monkeypatch.setattr(runner_mod, "api_call", api_call)
    task = configure_job(tmp_path)
    artifact_execution(runner_mod, monkeypatch, task)
    assert execute(runner_mod, tmp_path) == 1
    assert statuses(calls) == ["in_progress", "done", "blocked"]
    assert "PRIVATE_RESPONSE_BODY" not in json.dumps(calls)


def test_fresh_failed_artifact_preserved_without_acceptance(runner_mod, tmp_path, monkeypatch, api):
    task = configure_job(tmp_path)
    artifact_execution(runner_mod, monkeypatch, task, {"status": "error:quota_exhausted"})
    assert execute(runner_mod, tmp_path) == 1
    copy = json.loads((task / "output" / "paperclip-runs" / "run-1.json").read_text())
    assert copy["artifact"]["status"] == "error:quota_exhausted"
    assert statuses(api[0])[-1] == "blocked"


def test_pid_reuse_never_signals_replacement(runner_mod, monkeypatch):
    monkeypatch.setattr(runner_mod, "collect_owned", lambda *_args: None)
    monkeypatch.setattr(runner_mod, "proc_identity", lambda _pid: (123, 999, "S"))
    kill = MagicMock()
    monkeypatch.setattr(runner_mod.os, "kill", kill)
    runner_mod.kill_owned(555555, {555555: 100}, b"owned-marker")
    kill.assert_not_called()


def test_check_quiet_never_calls_api_or_executes(runner_mod, tmp_path, monkeypatch, api):
    configure_job(tmp_path)
    native_env(monkeypatch, tmp_path, ["--job", "job-1", "--check-quiet"])
    launch = MagicMock()
    monkeypatch.setattr(runner_mod, "execute_cron_job", launch)
    assert runner_mod.main() == 0
    assert not api[0]
    launch.assert_not_called()


def nested_command(tmp_path, orphan=False, clean_env=False):
    env_arg = ",env={}" if clean_env else ""
    leaf = (
        "import os,time; from pathlib import Path; "
        f"Path({str(tmp_path / 'leaf.pid')!r}).write_text(str(os.getpid())); time.sleep(60)"
    )
    middle = (
        "import os,subprocess,sys,time; from pathlib import Path; "
        f"Path({str(tmp_path / 'middle.pid')!r}).write_text(str(os.getpid())); "
        f"p=subprocess.Popen([sys.executable,'-c',{leaf!r}],start_new_session=True{env_arg}); "
        + ("time.sleep(0.15)" if orphan else "time.sleep(60)")
    )
    root = (
        "import subprocess,sys,time; "
        f"p=subprocess.Popen([sys.executable,'-c',{middle!r}],start_new_session=True{env_arg}); "
        + ("p.wait()" if orphan else "time.sleep(60)")
    )
    return [sys.executable, "-c", root]


def assert_nested_gone(runner_mod, tmp_path):
    for name in ("middle.pid", "leaf.pid"):
        path = tmp_path / name
        assert path.exists(), f"test never launched {name}"
        pid = int(path.read_text())
        identity = runner_mod.proc_identity(pid)
        assert identity is None or identity[2] == "Z", f"owned descendant {pid} survived"


@pytest.mark.parametrize(("orphan", "clean_env"), [(False, False), (True, False), (False, True)])
def test_real_nested_sessions_cleaned_and_unrelated_survives(
    runner_mod, tmp_path, orphan, clean_env
):
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True
    )
    try:
        error, rc = runner_mod.run_owned_process(
            nested_command(tmp_path, orphan, clean_env), timeout_seconds=0.6
        )
        assert (error == "process_timeout") if not orphan else (error is None and rc == 0)
        assert_nested_gone(runner_mod, tmp_path)
        assert unrelated.poll() is None
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


@pytest.mark.parametrize("signum", [signal.SIGTERM, signal.SIGINT])
def test_real_native_runner_interrupt_cleans_nested_sessions(runner_mod, tmp_path, signum):
    result = tmp_path / "result.json"
    script = (
        "from importlib.machinery import SourceFileLoader; "
        "import json,types; from pathlib import Path; "
        "m=types.ModuleType('runner'); "
        f"SourceFileLoader('runner',{str(SCRIPT_PATH)!r}).exec_module(m); "
        f"r=m.run_owned_process({nested_command(tmp_path)!r}, timeout_seconds=10); "
        f"Path({str(result)!r}).write_text(json.dumps(r))"
    )
    proc = subprocess.Popen([sys.executable, "-c", script], start_new_session=True)
    try:
        deadline = time.monotonic() + 5
        while not (tmp_path / "leaf.pid").exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert (tmp_path / "leaf.pid").exists()
        proc.send_signal(signum)
        assert proc.wait(timeout=5) == 0
        assert json.loads(result.read_text())[0] == "process_interrupted"
        assert_nested_gone(runner_mod, tmp_path)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
