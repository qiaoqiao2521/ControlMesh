"""Executable consultation gates; fake API is not live Paperclip acceptance."""

# ruff: noqa: INP001 -- isolated standalone adapter tests, no legacy runtime imports
import copy
from importlib.machinery import SourceFileLoader
import json
from pathlib import Path
import subprocess
import types

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/paperclip/cm-consult"
m = types.ModuleType("consult")
SourceFileLoader("consult", str(SCRIPT)).exec_module(m)


class Native:
    def __init__(self):
        self.issues = {
            "parent": {
                "id": "parent",
                "companyId": "company",
                "assigneeAgentId": "coordinator",
                "status": "in_progress",
            }
        }
        self.comments = {}
        self.runs = {}
        self.calls = []
        self.lose_create_response = False

    def __call__(self, method, path, body=None):
        self.calls.append((method, path, copy.deepcopy(body)))
        parts = path.split("/")
        item = parts[3]
        if parts[2] == "heartbeat-runs":
            return copy.deepcopy(self.runs[item])
        if method == "POST":
            child_id = f"child-{len(self.issues)}"
            issue = {**body, "id": child_id, "companyId": "company", "parentId": item}
            self.issues[child_id] = issue
            self.comments[child_id] = []
            if self.lose_create_response:
                raise ValueError("api_transport_failed_reconcile_before_retry")
            return copy.deepcopy(issue)
        if method == "PATCH":
            self.issues[item].update({k: v for k, v in body.items() if k != "comment"})
            if "comment" in body:
                self.comments[item].append(
                    {
                        "body": body["comment"],
                        "issueId": item,
                        "companyId": "company",
                        "authorAgentId": self.issues[item]["assigneeAgentId"],
                        "createdByRunId": f"run-{item}",
                    }
                )
            return copy.deepcopy(self.issues[item])
        if path.endswith("/comments"):
            return copy.deepcopy(self.comments[item])
        if path.endswith("/runs"):
            return [
                {"runId": key, "createdAt": value.get("createdAt", "2026-10-01T00:00:00Z")}
                for key, value in self.runs.items()
                if value["contextSnapshot"]["issueId"] == item
            ]
        return copy.deepcopy(self.issues[item])


@pytest.fixture
def setup(tmp_path, monkeypatch):
    for name in (
        "PAPERCLIP_AGENT_ID",
        "PAPERCLIP_RUN_ID",
        "PAPERCLIP_TASK_ID",
        "PAPERCLIP_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    spec = {
        "company_id": "company",
        "parent_id": "parent",
        "coordinator_id": "coordinator",
        "workers": ["agy", "zcode"],
        "question": "Which minimal approach?",
        "baseline": "commit-123",
        "facts": "[S1] example.py at commit-123",
        "initial_judgment": "PRIVATE INITIAL OPINION",
        "constraints": "No implementation",
    }
    root = tmp_path / "private"
    m.initialize(root, spec)
    native = Native()
    return m.Consultation(root, native), native


def result(consult, slot="initial-1", completeness="complete"):
    return {
        "revision": m.read(consult.path)["revision"],
        "slot": slot,
        "completeness": completeness,
        "recommendation": "Keep alternative B",
        "evidence": ["source.py@revision#L1"],
        "uncertainties": ["not measured"],
        "usage_tokens": None,
        "session_id": "native-session",
    }


def finish(consult, native, slot="initial-1", completeness="complete"):
    data = m.read(consult.path)
    entry = data["slots"][slot]
    child = entry["issue_id"]
    native.issues[child]["status"] = "done"
    native.runs[f"run-{child}"] = {
        "companyId": "company",
        "agentId": entry["agent_id"],
        "status": "succeeded",
        "contextSnapshot": {"issueId": child},
    }
    native.comments[child] = [
        {
            "companyId": "company",
            "issueId": child,
            "authorAgentId": entry["agent_id"],
            "createdByRunId": f"run-{child}",
            "body": "CM-CONSULT-RESULT-V1\n"
            + json.dumps(result(consult, slot, completeness), sort_keys=True, ensure_ascii=False),
        }
    ]


def decision(consult, outcome="recommend"):
    return {
        "snapshot_digest": consult.collect()["snapshot_digest"],
        "outcome": outcome,
        "rationale": "Compared actual evidence",
        "dissent": "B remains defensible",
        "next_action": "Run one bounded test",
        "verified_evidence": ["test ref"],
    }


def test_dispatch_independence_wait_order_and_replay(setup):
    consult, native = setup
    consult.dispatch()
    assert len(native.issues) == 3
    writes = [c for c in native.calls if c[0] != "GET"]
    assert [c[2]["status"] for c in writes] == ["backlog", "backlog", "blocked", "todo", "todo"]
    assert all(c[2]["blockParentUntilDone"] for c in writes[:2])
    assert "PRIVATE INITIAL OPINION" not in json.dumps(writes)
    n = len(writes)
    consult.dispatch()
    assert len([c for c in native.calls if c[0] != "GET"]) == n
    assert consult.path.stat().st_mode & 0o777 == 0o600


def test_unknown_creation_is_never_retried_and_can_bind(setup):
    consult, native = setup
    native.lose_create_response = True
    with pytest.raises(ValueError, match="transport"):
        consult.dispatch()
    with pytest.raises(ValueError, match="unknown"):
        consult.dispatch()
    assert len(native.issues) == 2
    consult.bind("initial-1", "child-1")
    native.lose_create_response = False
    consult.dispatch()
    assert len(native.issues) == 3


@pytest.mark.parametrize("field", ["companyId", "parentId", "assigneeAgentId", "description"])
def test_identity_drift_rejected(setup, field):
    consult, native = setup
    consult.dispatch()
    native.issues["child-1"][field] = "wrong"
    with pytest.raises(ValueError, match="identity"):
        consult.collect()


@pytest.mark.parametrize("failure", ["author", "run", "revision", "conflict", "missing_run"])
def test_evidence_fail_closed(setup, failure):
    consult, native = setup
    consult.dispatch()
    finish(consult, native)
    c = native.comments["child-1"][0]
    if failure == "author":
        c["authorAgentId"] = "other"
    elif failure == "run":
        native.runs["run-child-1"]["contextSnapshot"]["issueId"] = "other"
    elif failure == "missing_run":
        c["createdByRunId"] = None
    elif failure == "revision":
        c["body"] = c["body"].replace(m.read(consult.path)["revision"], "old")
    else:
        native.comments["child-1"].append({**c, "body": c["body"].replace("Keep", "Reject")})
    with pytest.raises(ValueError, match=r"mismatch|invalid_identity|conflicting"):
        consult.collect()


def test_partial_unknown_cost_and_single_supplement(setup):
    consult, native = setup
    consult.dispatch()
    finish(consult, native, completeness="partial")
    finish(consult, native, "initial-2")
    assert not consult.collect()["reported_usage_complete"]
    with pytest.raises(ValueError, match="incomplete"):
        consult.decide(decision(consult))
    consult.followup("agy", "Recover missing answer; counts against shared budget")
    consult.dispatch()
    finish(consult, native, "followup")
    # Reopening receipt cannot reset the supplement budget.
    reopened = m.Consultation(consult.root, native)
    with pytest.raises(ValueError, match="budget"):
        reopened.followup("zcode", "One more")
    assert reopened.decide(decision(reopened))["recorded"] == "recommend"
    assert native.issues["parent"]["status"] == "blocked"  # no automatic promotion


def test_freshness_and_disagreement(setup):
    consult, native = setup
    consult.dispatch()
    finish(consult, native)
    finish(consult, native, "initial-2")
    d = decision(consult)
    native.comments["child-2"][0]["body"] = native.comments["child-2"][0]["body"].replace(
        "Keep", "Reject"
    )
    with pytest.raises(ValueError, match="stale"):
        consult.decide(d)
    d = decision(consult)
    assert consult.decide(d) == {"recorded": "recommend", "published": False}
    assert consult.decide(d)["recorded"] == "recommend"
    with pytest.raises(ValueError, match="closed"):
        consult.dispatch()


def test_old_result_cannot_survive_new_native_run(setup):
    consult, native = setup
    consult.dispatch()
    finish(consult, native)
    native.runs["new-run"] = {
        "companyId": "company",
        "agentId": "agy",
        "status": "running",
        "contextSnapshot": {"issueId": "child-1"},
        "createdAt": "2026-10-01T01:00:00Z",
    }
    with pytest.raises(ValueError, match="stale_result"):
        consult.collect()


@pytest.mark.parametrize("kind", ["cancelled", "run_failed", "no_result"])
def test_failures_allow_checkpoint_not_recommend(setup, kind):
    consult, native = setup
    consult.dispatch()
    finish(consult, native)
    finish(consult, native, "initial-2")
    if kind == "cancelled":
        native.issues["child-1"]["status"] = "cancelled"
    elif kind == "run_failed":
        native.runs["run-child-1"]["status"] = "failed"
    else:
        native.comments["child-1"] = []
    with pytest.raises(ValueError, match="incomplete"):
        consult.decide(decision(consult))
    assert consult.decide(decision(consult, "checkpoint"))["recorded"] == "checkpoint"


def test_submit_requires_real_context_and_preserves_idempotency(setup, monkeypatch):
    consult, native = setup
    consult.dispatch()
    with pytest.raises(ValueError, match="invalid_identity"):
        consult.submit("initial-1", result(consult))
    for name, value in {
        "PAPERCLIP_AGENT_ID": "agy",
        "PAPERCLIP_RUN_ID": "run-child-1",
        "PAPERCLIP_TASK_ID": "child-1",
        "PAPERCLIP_API_KEY": "test-only",
    }.items():
        monkeypatch.setenv(name, value)
    native.runs["run-child-1"] = {
        "companyId": "company",
        "agentId": "agy",
        "status": "running",
        "contextSnapshot": {"issueId": "child-1"},
    }
    consult.submit("initial-1", result(consult))
    assert consult.submit("initial-1", result(consult))["replayed"]
    assert len(native.comments["child-1"]) == 1
    changed = result(consult)
    changed["recommendation"] = "new payload"
    with pytest.raises(ValueError, match="conflicting"):
        consult.submit("initial-1", changed)


def test_cli_help_and_frozen_spec(setup):
    consult, _ = setup
    wrapper = SCRIPT.with_name("cm-paperclip")
    proc = subprocess.run(
        ["sh", str(wrapper), "consult", "--help"], capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0
    assert "followup" in proc.stdout
    data = m.read(consult.path)
    data["spec"]["question"] = "changed"
    m.write(consult.path, data)
    with pytest.raises(ValueError, match="frozen"):
        consult.collect()


@pytest.mark.parametrize(
    "url", ["https://example.com", "http://localhost@evil.test", "http://127.0.0.1/path"]
)
def test_auth_never_sent_to_remote(monkeypatch, url):
    monkeypatch.setenv("PAPERCLIP_API_URL", url)
    with pytest.raises(ValueError, match="local"):
        m.API()
