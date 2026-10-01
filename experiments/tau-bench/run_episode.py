#!/usr/bin/env python3
"""One bounded native retail task 88 episode, followed by offline strict replay.

Run with the tau2 virtualenv Python and --output-root pointing at an ignored
directory. This script does not install dependencies. --replay RUN_DIRECTORY
independently evaluates an existing episode without making model calls.
Raw HTTP/provider logs and raw_data are deliberately excluded from artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import uuid

UPSTREAM_COMMIT = "fc0055dc4e0a316c3f83133267fbd6faaa770992"
MODEL = "anthropic/MiniMax-M3"
TASK_ID = "88"
HARD_TIMEOUT_SECONDS = 180
REPLAY_TIMEOUT_SECONDS = 30
BOUNDS = {"episodes": 1, "max_steps": 32, "max_errors": 2,
          "simulation_timeout_seconds": 160, "request_timeout_seconds": 30,
          "num_retries": 0, "max_tokens": 1024, "seed": 0}


def _write_json(path: Path, payload: dict) -> None:
    # Exclusive creation prevents accidental replacement of existing evidence.
    with path.open("x", encoding="utf-8") as stream:
        os.chmod(path, 0o600)
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_report(path: Path) -> dict:
    # A hard deadline can interrupt a worker while it writes its report.
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _finite_number(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if math.isfinite(value) else None
    return None


def _silence() -> None:
    # The parent also routes OS-level stdout/stderr to DEVNULL. Do not retain
    # raw exceptions: HTTP errors can contain private endpoint/authentication.
    logging.disable(logging.CRITICAL)
    from loguru import logger
    logger.remove()


def _error_category(exc: BaseException) -> str:
    categories = {"AuthenticationError": "authentication_error",
                  "RateLimitError": "rate_limit", "Timeout": "request_timeout",
                  "APITimeoutError": "request_timeout",
                  "APIConnectionError": "connection_error",
                  "BadRequestError": "request_rejected",
                  "ImportError": "dependency_missing",
                  "ModuleNotFoundError": "dependency_missing"}
    return categories.get(type(exc).__name__, "worker_error")


def _load_task():
    from tau2.runner import get_tasks
    tasks = get_tasks(task_set_name="retail", task_split_name="base",
                      task_ids=[TASK_ID])
    if len(tasks) != 1 or tasks[0].id != TASK_ID:
        raise RuntimeError("Unexpected task selection")
    task = tasks[0]
    # ALL remains offline for this task because its NL assertions are empty.
    if task.evaluation_criteria is None or task.evaluation_criteria.nl_assertions:
        raise RuntimeError("Task requires a different evaluation contract")
    return task


def _configure_endpoint() -> None:
    # Called only in the model worker. Never place either value in config,
    # kwargs, command arguments, summary, exceptions or persisted logs.
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    base = os.environ.get("ANTHROPIC_BASE_URL")
    if not token or not base:
        raise RuntimeError("Missing endpoint configuration")
    base = base.rstrip("/")
    if base.endswith("/v1/messages"):
        endpoint = base
    elif base.endswith("/v1"):
        endpoint = base + "/messages"
    else:
        endpoint = base + "/v1/messages"
    os.environ["ANTHROPIC_API_KEY"] = token
    os.environ["ANTHROPIC_API_BASE"] = endpoint


def _episode_stats(simulation) -> dict:
    counts = {"assistant": 0, "user": 0}
    tokens = {"assistant": {"prompt_tokens": 0, "completion_tokens": 0},
              "user": {"prompt_tokens": 0, "completion_tokens": 0}}
    missing_usage = {"assistant": 0, "user": 0}
    tool_calls = 0
    tool_errors = 0
    for message in simulation.messages:
        tool_calls += len(getattr(message, "tool_calls", None) or [])
        if message.role == "tool" and message.error:
            tool_errors += 1
        role = message.role
        # UserSimulator copies usage/cost/raw_data into UserMessage but does
        # not propagate generation_time_seconds in this stable release.
        generated = (getattr(message, "generation_time_seconds", None) is not None
                     or getattr(message, "usage", None) is not None
                     or getattr(message, "raw_data", None) is not None)
        if role not in counts or not generated:
            continue
        counts[role] += 1
        usage = getattr(message, "usage", None) or {}
        if any(not isinstance(usage.get(key), int) or isinstance(usage.get(key), bool)
               or usage[key] < 0 for key in tokens[role]):
            missing_usage[role] += 1
        else:
            for key in tokens[role]:
                tokens[role][key] += usage[key]
    return {"message_count": len(simulation.messages), "tool_call_count": tool_calls,
            "tool_error_count": tool_errors, "llm_response_counts": counts,
            "token_usage": tokens, "responses_missing_usage": missing_usage,
            "usage_scope": "completed_responses_only",
            "framework_reported_agent_cost_usd": _finite_number(simulation.agent_cost),
            "framework_reported_user_cost_usd": _finite_number(simulation.user_cost),
            "cost_usd": None, "cost_status": "unknown_custom_model_pricing"}


def _model_worker(output_dir: Path) -> int:
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    stage = "setup"
    try:
        _configure_endpoint()
        _silence()
        from tau2.data_model.simulation import TextRunConfig
        from tau2.runner import run_single_task
        task = _load_task()
        llm_args = {"temperature": 0.0, "timeout": 30, "num_retries": 0,
                    "max_tokens": 1024}
        config = TextRunConfig(
            domain="retail", task_set_name="retail", task_split_name="base",
            task_ids=[TASK_ID], num_trials=1, max_concurrency=1,
            agent="llm_agent", user="user_simulator", llm_agent=MODEL,
            llm_user=MODEL, llm_args_agent=dict(llm_args),
            llm_args_user=dict(llm_args), max_steps=32, max_errors=2,
            timeout=160, seed=0, max_retries=0, hallucination_retries=0,
            auto_review=False, verbose_logs=False,
        )
        _write_json(output_dir / "task.json", task.model_dump(mode="json"))
        stage = "episode"
        simulation = run_single_task(config, task, seed=0, auto_review=False,
                                     verbose_logs=False)
        stats = _episode_stats(simulation)
        # Retain every real message, tool call/result, timestamp and policy
        # needed for replay; provider raw_data is unnecessary and may leak
        # response headers or other endpoint metadata.
        retained = simulation.model_copy(deep=True)
        for message in retained.messages:
            if hasattr(message, "raw_data"):
                message.raw_data = None
        trajectory_path = output_dir / "simulation.json"
        _write_json(trajectory_path, retained.model_dump(mode="json"))
        live_reward = _finite_number(simulation.reward_info.reward) if simulation.reward_info else None
        _write_json(output_dir / "worker_summary.json", {
            "status": "episode_completed", "task_id": TASK_ID,
            "upstream_commit": UPSTREAM_COMMIT, "model": MODEL, "bounds": BOUNDS,
            "termination_reason": simulation.termination_reason.value,
            "live_reward": live_reward, "duration_seconds": _finite_number(simulation.duration),
            "simulation_sha256": _sha256(trajectory_path),
            "task_sha256": _sha256(output_dir / "task.json"),
            "raw_data_retained": False, **stats,
        })
        return 0
    except BaseException as exc:
        _write_json(output_dir / "worker_summary.json", {
            "status": "episode_error", "stage": stage,
            "error_category": _error_category(exc), "task_id": TASK_ID,
            "upstream_commit": UPSTREAM_COMMIT, "model": MODEL, "bounds": BOUNDS,
            "partial_trajectory_available": False,
            "cost_usd": None, "cost_status": "unknown_failed_request_charges",
        })
        return 2


def _replay_worker(output_dir: Path, report_name: str) -> int:
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    try:
        _silence()
        from tau2.data_model.simulation import SimulationRun
        from tau2.evaluator.evaluator import EvaluationType, evaluate_simulation
        from tau2.utils import llm_utils

        def no_model_calls(*args, **kwargs):
            raise RuntimeError("Model calls forbidden during replay")

        llm_utils.completion = no_model_calls
        task = _load_task()
        stored_task = json.loads((output_dir / "task.json").read_text(encoding="utf-8"))
        if stored_task != task.model_dump(mode="json"):
            raise RuntimeError("Task snapshot mismatch")
        trajectory_path = output_dir / "simulation.json"
        simulation = SimulationRun.model_validate_json(trajectory_path.read_text(encoding="utf-8"))
        if simulation.task_id != TASK_ID:
            raise RuntimeError("Trajectory task mismatch")
        reward = evaluate_simulation(simulation=simulation, task=task,
                                     evaluation_type=EvaluationType.ALL,
                                     solo_mode=False, domain="retail", strict_replay=True)
        _write_json(output_dir / report_name, {
            "status": "replay_completed", "task_id": TASK_ID,
            "strict_replay": True, "model_calls_allowed": False,
            "database_replay_executed": simulation.termination_reason.value in {"agent_stop", "user_stop"},
            "reward": _finite_number(reward.reward),
            "reward_basis": [item.value for item in reward.reward_basis or []],
            "db_match": reward.db_check.db_match if reward.db_check else None,
            "task_success": reward.reward == 1.0 and simulation.termination_reason.value in {"agent_stop", "user_stop"},
            "clean_tool_episode": _episode_stats(simulation)["tool_error_count"] == 0,
            "termination_reason": simulation.termination_reason.value,
            "simulation_sha256": _sha256(trajectory_path),
            "task_sha256": _sha256(output_dir / "task.json"),
            "tool_error_count": _episode_stats(simulation)["tool_error_count"],
        })
        return 0
    except BaseException as exc:
        _write_json(output_dir / report_name, {
            "status": "replay_error", "error_category": _error_category(exc),
            "strict_replay": True, "model_calls_allowed": False,
        })
        return 2


def _subprocess(mode: str, output_dir: Path, timeout: int, report_name: str | None = None) -> dict:
    command = [sys.executable, str(Path(__file__).resolve()), mode,
               "--output-dir", str(output_dir)]
    if report_name:
        command.extend(["--report-name", report_name])
    started = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        return_code = process.wait(timeout=timeout)
        return {"return_code": return_code, "hard_timeout": False,
                "wall_seconds": round(time.monotonic() - started, 3)}
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        return {"return_code": process.returncode, "hard_timeout": True,
                "wall_seconds": round(time.monotonic() - started, 3)}


def _parent(output_root: Path) -> int:
    output_root.mkdir(parents=True, exist_ok=True)
    output_dir = Path(tempfile.mkdtemp(prefix="task88-", dir=output_root))
    run = _subprocess("--worker", output_dir, HARD_TIMEOUT_SECONDS)
    worker_path = output_dir / "worker_summary.json"
    worker = _read_report(worker_path)
    summary = {"status": "failed", "task_id": TASK_ID, "model": MODEL,
               "upstream_commit": UPSTREAM_COMMIT, "bounds": BOUNDS,
               "run_process": run, "episode": worker, "accepted": False}
    if run["return_code"] == 0 and not run["hard_timeout"] and worker.get("status") == "episode_completed":
        replay_name = "strict_replay.json"
        replay_process = _subprocess("--replay-worker", output_dir, REPLAY_TIMEOUT_SECONDS, replay_name)
        report_path = output_dir / replay_name
        replay = _read_report(report_path)
        summary.update({"replay_process": replay_process, "replay": replay})
        summary["accepted"] = bool(
            replay_process["return_code"] == 0 and not replay_process["hard_timeout"]
            and replay.get("status") == "replay_completed"
            and replay.get("database_replay_executed") is True
            and worker.get("termination_reason") in {"agent_stop", "user_stop"}
            and worker.get("live_reward") == replay.get("reward") == 1.0
            and worker.get("simulation_sha256") == replay.get("simulation_sha256")
            and worker.get("task_sha256") == replay.get("task_sha256")
            and worker.get("tool_error_count") == replay.get("tool_error_count") == 0
            and worker.get("llm_response_counts", {}).get("assistant", 0) > 0
            and worker.get("llm_response_counts", {}).get("user", 0) > 0)
        summary["status"] = "accepted" if summary["accepted"] else "not_accepted"
        summary["task_success"] = replay.get("task_success", False)
        summary["clean_tool_episode"] = replay.get("clean_tool_episode", False)
    elif run["hard_timeout"]:
        summary["status"] = "hard_timeout"
    summary["acceptance_scope"] = "one_task_database_goal_and_strict_replay"
    summary["output_directory"] = str(output_dir)
    _write_json(output_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return 0 if summary["accepted"] else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    mode.add_argument("--replay-worker", action="store_true", help=argparse.SUPPRESS)
    mode.add_argument("--replay", type=Path, help="Independently replay an existing run directory")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--output-dir", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--report-name", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker or args.replay_worker:
        if args.output_dir is None:
            return 2
        if args.replay_worker:
            if not args.report_name or Path(args.report_name).name != args.report_name:
                return 2
            return _replay_worker(args.output_dir, args.report_name)
        return _model_worker(args.output_dir)
    if args.replay is not None:
        report_name = "strict_replay_" + uuid.uuid4().hex + ".json"
        process = _subprocess("--replay-worker", args.replay.resolve(), REPLAY_TIMEOUT_SECONDS, report_name)
        report_path = args.replay / report_name
        report = _read_report(report_path)
        print(json.dumps({"process": process, "replay": report}, allow_nan=False))
        return 0 if process["return_code"] == 0 and report.get("status") == "replay_completed" else 2
    if args.output_root is None:
        parser.error("--output-root is required for a new episode")
    return _parent(args.output_root.expanduser().resolve())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        # Parent filesystem/process failures are also reported without raw text.
        print('{"status":"entrypoint_error","accepted":false}')
        raise SystemExit(2)
