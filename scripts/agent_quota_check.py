#!/usr/bin/env python3
"""Probe Qoder/AGY before dispatch; retain explicit CBC support."""
import argparse
import json
import re
import secrets
import subprocess
import sys
from pathlib import Path


def classify(stdout, stderr, returncode, marker):
    """CLI errors can appear on stderr even when the exit code is zero."""
    try:
        payload = json.loads(stdout)
    except ValueError:
        payload = stdout.strip()
    decoded = json.dumps(payload, ensure_ascii=False) + "\n" + stderr
    if re.search(r"quota.{0,30}(exhaust|exceed)|(?:no available|insufficient) credits|credit.{0,20}exhaust|额度.{0,15}(用尽|耗尽|不足)|余额不足", decoded, re.I):
        return "quota_blocked"
    if re.search(r"\b429\b|rate.?limit|too many requests|限流", decoded, re.I):
        return "rate_limited"
    answer = payload.get("result", payload.get("text", "")) if isinstance(payload, dict) else payload
    if isinstance(payload, dict) and (payload.get("is_error") or payload.get("error")):
        return "unavailable"
    if returncode == 0 and isinstance(answer, str) and answer.strip() == marker:
        return "ready"
    return "unknown" if returncode == 0 else "unavailable"


def check(agent, profile, timeout):
    marker = "quota_probe_" + secrets.token_hex(8)
    try:
        command = [profile["command"]]
        if agent == "agy":
            # AGY has no --tools/--no-session-persistence flags. Keep its native CLI.
            command += ["--output-format", "text", "--mode", "plan", "--sandbox",
                        "--disable-slash-commands", "--print"]
        else:
            command += ["--print", "--tools", "", "--no-session-persistence"]
            if agent == "qoder":
                command += ["--output-format", "text", "--max-output-tokens", "32", "--max-model-request-retries", "0"]
            else:
                command += ["--output-format", "json", "--max-turns", "1"]
        command.append("Reply with exactly " + marker + ". Do not use tools.")
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, cwd="/tmp")
        status = classify(result.stdout, result.stderr, result.returncode, marker)
    except subprocess.TimeoutExpired:
        status = "timeout"
    except (OSError, KeyError):
        status = "unavailable"
    return {"agent": agent, "status": status, "usable": status == "ready"}


def pick(results):
    """Prefer ready candidates in input order; both-failed still gets one attempt."""
    ready = next((item for item in results if item["usable"]), None)
    fallback = next((item for item in results if item["status"] != "unconfigured"), results[0])
    return {"selected": (ready or fallback)["agent"], "degraded": ready is None,
            "checks": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agents", nargs="*", metavar="CLI")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--pick", action="store_true", help="Select once; both-failed falls back without claiming readiness")
    args = parser.parse_args()
    agents = list(dict.fromkeys(args.agents or ["qoder", "agy"]))
    if any(agent not in ("qoder", "agy", "cbc") for agent in agents):
        parser.error("CLI must be qoder, agy or cbc")
    try:
        profiles = json.loads((Path.home() / ".agent-link/config.json").read_text())["agents"]
    except (OSError, ValueError, KeyError):
        profiles = {}
    results = []
    for agent in agents:
        profile = profiles.get(agent)
        results.append(check(agent, profile, args.timeout) if profile else {"agent": agent, "status": "unconfigured", "usable": False})
    output = pick(results) if args.pick else results
    if args.pick and output["degraded"]:
        print("WARNING: No probe-ready CLI; select once with degraded=true, without retrying probes.", file=sys.stderr)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
