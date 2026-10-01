#!/usr/bin/env python3
"""Offline gold-replay controls for official tau2-bench (stable v1.0.1) retail 88/90.

This is a *controls* script, not an Agent episode. It makes no model/API call.

What it does, per task:
  1. Loads the official retail ``base`` task (88, 90).
  2. Enforces safety guards: no initial state, no NL assertions, and exactly one
     non-empty ``cancel_pending_order`` reference action. A changed task fails loudly.
  3. Executes the reference action through a real
     ``Environment.get_response(ToolCall)`` and checks ``error=False``.
  4. Builds a synthetic half-duplex history from the real
     ``AssistantMessage`` tool call plus the actual returned ``ToolMessage``.
  5. Scores that gold history and an empty no-op history with the official
     ``evaluate_simulation`` using the task's unchanged ``reward_basis`` and
     ``EvaluationType.ALL``, ``solo_mode=False``, ``strict_replay=True``.
  6. Asserts gold reward 1.0 / DB match, no-op reward 0.0 / DB mismatch, a real
     DB-hash change, and the order status transition to ``cancelled``.

The saved trajectories are synthetic scorer inputs, not an autonomous Agent
episode. Run with the isolated tau2 interpreter; see README.md.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
logging.disable(logging.CRITICAL)
from loguru import logger
logger.remove()

from tau2.data_model.message import AssistantMessage, ToolCall
from tau2.data_model.simulation import SimulationRun, TerminationReason
from tau2.data_model.tasks import RewardType, Task
from tau2.domains.retail.environment import get_environment, get_tasks
from tau2.evaluator.evaluator import EvaluationType, evaluate_simulation
from tau2.utils.utils import get_now, get_tau2_version
from tau2.utils import llm_utils


def forbid_model_call(*args, **kwargs):
    raise ControlFailure("Model calls are forbidden during offline controls")


llm_utils.completion = forbid_model_call

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "output" / "controls"

DOMAIN = "retail"
TASK_SPLIT = "base"
TASK_IDS = ("88", "90")
GOLD_ACTION_NAME = "cancel_pending_order"
EXPECTED_INITIAL_STATUS = "pending"
EXPECTED_FINAL_STATUS = "cancelled"

EVALUATION_TYPE = EvaluationType.ALL
SOLO_MODE = False
STRICT_REPLAY = True

EPSILON = 1e-9


class ControlFailure(Exception):
    """Raised when a control precondition or assertion is not met."""


def load_base_tasks(task_ids: tuple[str, ...]) -> list[Task]:
    """Load the requested tasks from the official retail ``base`` split."""
    by_id = {task.id: task for task in get_tasks(TASK_SPLIT)}
    missing = [task_id for task_id in task_ids if task_id not in by_id]
    if missing:
        raise ControlFailure(
            f"retail/{TASK_SPLIT} is missing task ids {missing}; "
            f"available ids include {sorted(by_id)[:10]}..."
        )
    return [by_id[task_id] for task_id in task_ids]


def validate_control_task(task: Task) -> object:
    """Guard the fixed control assumptions; fail clearly if the task changed."""
    criteria = task.evaluation_criteria
    if criteria is None:
        raise ControlFailure(f"task {task.id}: missing evaluation_criteria")

    if task.initial_state is not None:
        raise ControlFailure(
            f"task {task.id}: unexpected initial_state; controls assume a clean env"
        )
    if criteria.nl_assertions:
        raise ControlFailure(
            f"task {task.id}: unexpected nl_assertions; "
            "controls must not invoke an LLM judge"
        )
    if not criteria.actions:
        raise ControlFailure(f"task {task.id}: expected a non-empty reference action list")

    cancel_actions = [a for a in criteria.actions if a.name == GOLD_ACTION_NAME]
    if len(criteria.actions) != 1 or len(cancel_actions) != 1:
        raise ControlFailure(
            f"task {task.id}: expected exactly one {GOLD_ACTION_NAME} reference action, "
            f"got {len(criteria.actions)} action(s): {[a.name for a in criteria.actions]}"
        )
    if RewardType.DB not in criteria.reward_basis:
        raise ControlFailure(
            f"task {task.id}: reward_basis {criteria.reward_basis} lacks DB"
        )
    return cancel_actions[0]


def order_status(env, order_id: str) -> str:
    """Read the current order status through a real (read-only) tool call."""
    order = env.make_tool_call("get_order_details", requestor="assistant", order_id=order_id)
    return order.status


def replay_gold_action(env, action) -> list:
    """Execute one reference action and return [AssistantMessage, ToolMessage]."""
    tool_call = ToolCall(
        id=f"call_{action.action_id}",
        name=action.name,
        arguments=dict(action.arguments),
        requestor=action.requestor,
    )
    assistant_message = AssistantMessage(
        role="assistant", content=None, tool_calls=[tool_call]
    )
    tool_message = env.get_response(tool_call)
    if tool_message.error:
        raise ControlFailure(
            f"gold action {action.name} returned error=True: {tool_message.content}"
        )
    return [assistant_message, tool_message]


def make_simulation(task_id: str, kind: str, messages: list, duration: float) -> SimulationRun:
    start_time = get_now()
    end_time = get_now()
    return SimulationRun(
        id=f"controls_retail_{task_id}_{kind}",
        task_id=task_id,
        start_time=start_time,
        end_time=end_time,
        duration=max(0.0, round(duration, 6)),
        termination_reason=TerminationReason.AGENT_STOP,
        messages=messages,
        trial=0,
    )


def score(simulation: SimulationRun, task: Task):
    return evaluate_simulation(
        simulation=simulation,
        task=task,
        evaluation_type=EVALUATION_TYPE,
        solo_mode=SOLO_MODE,
        domain=DOMAIN,
        strict_replay=STRICT_REPLAY,
    )


def reward_summary(reward_info) -> dict:
    db_check = reward_info.db_check
    action_checks = reward_info.action_checks or []
    return {
        "reward": reward_info.reward,
        "db_match": None if db_check is None else db_check.db_match,
        "db_reward": None if db_check is None else db_check.db_reward,
        "action_checks_matched": sum(1 for c in action_checks if c.action_match),
        "action_checks_total": len(action_checks),
        "nl_assertions_evaluated": len(reward_info.nl_assertions or []),
        "reward_basis": [b.value for b in (reward_info.reward_basis or [])],
    }


def assert_scoring(task_id: str, kind: str, reward_info, expected_reward: float, expected_db_match: bool) -> None:
    if reward_info.db_check is None:
        raise ControlFailure(f"task {task_id} {kind}: reward info has no db_check")
    if reward_info.db_check.db_match is not expected_db_match:
        raise ControlFailure(
            f"task {task_id} {kind}: db_match={reward_info.db_check.db_match}, "
            f"expected {expected_db_match}"
        )
    if abs(reward_info.reward - expected_reward) > EPSILON:
        raise ControlFailure(
            f"task {task_id} {kind}: reward={reward_info.reward}, "
            f"expected {expected_reward}"
        )


def run_task_controls(task: Task) -> dict:
    action = validate_control_task(task)
    order_id = action.arguments["order_id"]

    env = get_environment()
    db_hash_before = env.get_db_hash()
    status_before = order_status(env, order_id)
    if status_before != EXPECTED_INITIAL_STATUS:
        raise ControlFailure(
            f"task {task.id}: order starts as {status_before!r}, "
            f"expected {EXPECTED_INITIAL_STATUS!r}"
        )

    started = time.perf_counter()
    gold_messages = replay_gold_action(env, action)
    elapsed = time.perf_counter() - started

    db_hash_after = env.get_db_hash()
    status_after = order_status(env, order_id)

    if db_hash_before == db_hash_after:
        raise ControlFailure(
            f"task {task.id}: real {action.name} left the DB hash unchanged"
        )
    if status_after != EXPECTED_FINAL_STATUS:
        raise ControlFailure(
            f"task {task.id}: order status {status_before}->{status_after}, "
            f"expected {EXPECTED_FINAL_STATUS!r}"
        )

    gold_sim = make_simulation(task.id, "gold", gold_messages, elapsed)
    noop_sim = make_simulation(task.id, "noop", [], elapsed)

    gold_reward = score(gold_sim, task)
    noop_reward = score(noop_sim, task)

    assert_scoring(task.id, "gold", gold_reward, 1.0, True)
    assert_scoring(task.id, "noop", noop_reward, 0.0, False)

    # Tasks 88/90 list NL_ASSERTION in reward_basis but carry no nl_assertions, so the
    # official judge returns without a model call. Assert nothing was judged.
    if gold_reward.nl_assertions or noop_reward.nl_assertions:
        raise ControlFailure(
            f"task {task.id}: NL assertions were evaluated, but this control "
            "must not invoke an LLM judge"
        )

    return {
        "task_id": task.id,
        "reward_basis": [b.value for b in task.evaluation_criteria.reward_basis],
        "guards": {
            "initial_state_absent": task.initial_state is None,
            "nl_assertions_absent": not task.evaluation_criteria.nl_assertions,
            "actions_nonempty": bool(task.evaluation_criteria.actions),
            "single_cancel_action": True,
        },
        "action": {
            "name": action.name,
            "order_id": order_id,
            "reason": action.arguments.get("reason"),
        },
        "order_status_before": status_before,
        "order_status_after": status_after,
        "db_hash_before": db_hash_before,
        "db_hash_after": db_hash_after,
        "db_hash_changed": db_hash_before != db_hash_after,
        "gold": {
            "simulation_id": gold_sim.id,
            "trajectory_file": f"trajectories/{gold_sim.id}.json",
            **reward_summary(gold_reward),
        },
        "noop": {
            "simulation_id": noop_sim.id,
            "trajectory_file": f"trajectories/{noop_sim.id}.json",
            **reward_summary(noop_reward),
        },
        "_gold_simulation": gold_sim,
        "_noop_simulation": noop_sim,
    }


def write_outputs(output_dir: Path, results: list[dict], failures: list[dict], summary_meta: dict) -> None:
    """Write only script-owned files: summary.json and trajectories/<sim id>.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    trajectory_dir = output_dir / "trajectories"
    trajectory_dir.mkdir(parents=True, exist_ok=True)

    public_results = []
    for result in results:
        for key in ("_gold_simulation", "_noop_simulation"):
            simulation = result[key]
            (trajectory_dir / f"{simulation.id}.json").write_text(
                simulation.model_dump_json(indent=2), encoding="utf-8"
            )
        public_results.append(
            {k: v for k, v in result.items() if not k.startswith("_")}
        )

    summary = {
        **summary_meta,
        "results": public_results,
        "failures": failures,
        "ok": not failures and len(public_results) == len(TASK_IDS),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline gold-replay controls for tau2 retail tasks 88/90 (no model calls)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Directory for summary.json and trajectories/. "
            "Default: experiments/tau-bench/output/controls (git-ignored)."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    failures: list[dict] = []
    results: list[dict] = []

    try:
        tasks = load_base_tasks(TASK_IDS)
    except Exception as exc:  # noqa: BLE001 - fatal, reported to caller
        print(f"[tb-controls] FATAL: {exc}", file=sys.stderr)
        return 2

    for task in tasks:
        try:
            results.append(run_task_controls(task))
        except Exception as exc:  # noqa: BLE001 - collect and keep going
            failures.append({"task_id": task.id, "error": str(exc)})
            print(f"[tb-controls] task {task.id} FAIL: {exc}", file=sys.stderr)

    meta = {
        "control": "tau2-retail-gold-replay",
        "generated_at": get_now(),
        "tau2_version": get_tau2_version(),
        "domain": DOMAIN,
        "task_split": TASK_SPLIT,
        "task_ids": list(TASK_IDS),
        "evaluation_type": EVALUATION_TYPE.value,
        "solo_mode": SOLO_MODE,
        "strict_replay": STRICT_REPLAY,
        "model_calls": False,
        "provenance": "synthetic gold-action replay; not an autonomous Agent episode",
    }

    try:
        write_outputs(args.output_dir, results, failures, meta)
    except Exception as exc:  # noqa: BLE001
        failures.append({"task_id": "output", "error": str(exc)})
        print(f"[tb-controls] could not write outputs: {exc}", file=sys.stderr)

    print(
        f"[tb-controls] tau2={meta['tau2_version']} domain={DOMAIN} "
        f"split={TASK_SPLIT} eval={EVALUATION_TYPE.value} "
        f"solo_mode={SOLO_MODE} strict_replay={STRICT_REPLAY} model_calls=False"
    )
    for result in results:
        print(
            f"[tb-controls] task {result['task_id']} "
            f"action={result['action']['name']} "
            f"status={result['order_status_before']}->{result['order_status_after']} "
            f"db_hash_changed={result['db_hash_changed']}"
        )
        print(
            f"[tb-controls] task {result['task_id']} gold "
            f"reward={result['gold']['reward']} db_match={result['gold']['db_match']} "
            f"action_checks={result['gold']['action_checks_matched']}/"
            f"{result['gold']['action_checks_total']}"
        )
        print(
            f"[tb-controls] task {result['task_id']} noop "
            f"reward={result['noop']['reward']} db_match={result['noop']['db_match']}"
        )

    if failures:
        print(f"[tb-controls] controls FAIL ({len(failures)} failure(s))", file=sys.stderr)
        return 1

    print(f"[tb-controls] controls PASS ({len(results)} task(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
