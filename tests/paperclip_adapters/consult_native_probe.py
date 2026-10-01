"""Opt-in native probe: isolated company, process agents, zero model calls.

Run explicitly with a private output directory. Never collected by pytest.
"""

# ruff: noqa: INP001 -- standalone opt-in executable
import argparse
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import sys
import time
import types
import uuid


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/paperclip/cm-consult"
m = types.ModuleType("consult")
SourceFileLoader("consult", str(SCRIPT)).exec_module(m)


def worker(directory, role) -> None:
    # Coordinator process intentionally does nothing: observe native event wakes only.
    if role == "coordinator":
        return
    consult = m.Consultation(directory)
    data = m.read(consult.path)
    slot = next(
        s
        for s, item in data["slots"].items()
        if item["agent_id"] == os.environ["PAPERCLIP_AGENT_ID"]
    )
    result = {
        "revision": data["revision"],
        "slot": slot,
        "completeness": "complete",
        "recommendation": "Synthetic protocol probe, not a model opinion",
        "evidence": ["deterministic probe version 1"],
        "uncertainties": ["no model exercised"],
        "usage_tokens": None,
        "session_id": None,
    }
    # Never fake task/run variables. submit verifies native contextSnapshot ownership.
    consult.submit(slot, result)


def probe(root) -> None:
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    api = m.API()
    company = api("POST", "/api/companies", {"name": f"CM consult probe {uuid.uuid4().hex[:8]}"})
    company_id = company["id"]
    agents = []
    summary = {"company_id": company_id, "model_calls": 0, "agents": agents}
    m.write(root / "probe.json", summary)
    try:
        for role in ("coordinator", "worker-1", "worker-2"):
            agent = api(
                "POST",
                f"/api/companies/{company_id}/agents",
                {
                    "name": role,
                    "role": "general",
                    "adapterType": "process",
                    "adapterConfig": {
                        "command": sys.executable,
                        "args": [
                            str(Path(__file__).resolve()),
                            "worker",
                            str(root / "consult"),
                            role,
                        ],
                        "cwd": str(root),
                        "timeoutSec": 30,
                        "graceSec": 2,
                    },
                    "runtimeConfig": {"heartbeat": {"enabled": False}},
                },
            )
            agents.append(agent["id"])
            m.write(root / "probe.json", summary)
        parent = api(
            "POST",
            f"/api/companies/{company_id}/issues",
            {
                "title": "CM consultation protocol acceptance (no models)",
                "assigneeAgentId": agents[0],
                "status": "backlog",
            },
        )
        summary["parent_id"] = parent["id"]
        m.write(root / "probe.json", summary)
        spec = {
            "company_id": company_id,
            "parent_id": parent["id"],
            "coordinator_id": agents[0],
            "workers": agents[1:],
            "question": "Does native handoff preserve identity?",
            "baseline": "synthetic-v1",
            "facts": "No model, no domain code modifications",
            "initial_judgment": "Verify native receipts",
            "constraints": "Protocol test only",
        }
        m.initialize(root / "consult", spec)
        consult = m.Consultation(root / "consult")
        summary["dispatch"] = consult.dispatch()
        m.write(root / "probe.json", summary)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            snapshot = consult.collect()
            if snapshot["ready"] and all(
                r["submission"] and r["submission"]["run_status"] == "succeeded"
                for r in snapshot["results"].values()
            ):
                break
            time.sleep(1)  # Bounded acceptance observer, not product scheduler/model loop.
        else:
            raise RuntimeError("native_probe_timeout")
        summary["snapshot"] = snapshot
        summary["decision"] = consult.decide(
            {
                "snapshot_digest": snapshot["snapshot_digest"],
                "outcome": "recommend",
                "rationale": "Synthetic native handoff verified",
                "dissent": "No real model opinions exercised",
                "next_action": "Stop test agents",
                "verified_evidence": ["native comments and run identities read back"],
            }
        )
        summary["parent_runs"] = []
        for row in api("GET", f"/api/issues/{parent['id']}/runs"):
            run = api("GET", f"/api/heartbeat-runs/{row['runId']}")
            summary["parent_runs"].append(
                {
                    "id": run["id"],
                    "status": run["status"],
                    "wake_reason": (run.get("contextSnapshot") or {}).get("wakeReason"),
                }
            )
        if not any(r["wake_reason"] == "issue_children_completed" for r in summary["parent_runs"]):
            raise RuntimeError("native_completion_wake_not_observed")
        summary["passed"] = True
    finally:
        for agent_id in agents:
            api("POST", f"/api/agents/{agent_id}/pause", {})
        summary["agents_paused"] = True
        m.write(root / "probe.json", summary)
    print(
        json.dumps(
            {
                "passed": summary.get("passed", False),
                "company_id": company_id,
                "agents_paused": True,
                "model_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["probe", "worker"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("role", nargs="?")
    args = parser.parse_args()
    if args.mode == "worker":
        worker(args.directory, args.role)
    else:
        probe(args.directory)
