#!/usr/bin/env python3
"""ControlMesh cron judgment layer (watchdog).

Judges the host's ControlMesh cron registry instead of blindly repeating:
- tracks per-job consecutive failures; N consecutive failures -> auto-pause + alert
- stalled detection: no run for 1.5x expected interval after a grace period
- artifact specs (artifacts.json): stale/undersized outputs alert independently of exit codes
- every job alerts at most once per day; --daily records a local-only host digest

State lives in ~/.controlmesh/cron-judgment/. All stdlib, no third-party deps.
"""

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home()
CM_HOME = HOME / ".controlmesh"
REGISTRY = CM_HOME / "cron_jobs.json"
STATE_DIR = CM_HOME / "cron-judgment"
STATE_DIR.mkdir(parents=True, exist_ok=True)
(STATE_DIR / "state").mkdir(exist_ok=True)
(STATE_DIR / "heartbeat").mkdir(exist_ok=True)
STATE = STATE_DIR / "state"
ARTIFACTS = STATE_DIR / "artifacts.json"
EVENTS = STATE_DIR / "events.log"
NOTIFICATION_CONFIG = CM_HOME / "config" / "cron-notification.json"
FAIL_THRESHOLD = int(os.environ.get("CM_JUDGE_FAILS", "2"))
GRACE_FACTOR = 1.5
HOST = socket.gethostname()


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def save_state(job_id, st):
    (STATE / (re.sub(r"[^A-Za-z0-9_.-]", "_", job_id) + ".json")).write_text(
        json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def notify_alert(text, event_key):
    config = load_json(NOTIFICATION_CONFIG, {})
    chat_id = config.get("chat_id") if isinstance(config, dict) else None
    if not isinstance(chat_id, str) or not chat_id.startswith("oc_"):
        log_event("NOTIFY_FAILED feishu missing_or_invalid_chat_id")
        return False
    key = hashlib.sha256(f"{HOST}:{iso(now())[:10]}:{event_key}".encode()).hexdigest()[:32]
    command = [
        "/usr/sbin/runuser", "-u", "agent436", "--", "/usr/bin/env", "-i",
        "HOME=/var/lib/agent436",
        "PATH=/opt/agent-tools/node-v24.21.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin",
        "/opt/cm-tools/node_modules/.bin/lark-cli", "--profile", "cm436",
        "im", "+messages-send", "--as", "bot", "--chat-id", chat_id,
        "--text", text[:3500], "--idempotency-key", "cm436-" + key,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            log_event(f"NOTIFY_FAILED feishu cli_exit={result.returncode}")
            return False
        payload = json.loads(result.stdout)
        for _ in range(3):
            if not isinstance(payload, dict):
                break
            if payload.get("ok") is False or ("code" in payload and payload["code"] not in (0, "0")):
                break
            message_id = payload.get("message_id")
            if isinstance(message_id, str) and message_id.startswith("om_"):
                return True
            payload = payload.get("data")
        log_event("NOTIFY_FAILED feishu missing_message_receipt")
    except (OSError, subprocess.TimeoutExpired, ValueError):
        log_event("NOTIFY_FAILED feishu cli_or_response_error")
    return False


def log_event(msg):
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(f"{iso(now())} {msg}\n")


def cron_interval_seconds(expr):
    """Heuristic max-gap estimate for the cron forms used in this fleet."""
    f = expr.split()
    if len(f) != 5:
        return 86400
    minute, hour, dom, mon, dow = f
    if minute.startswith("*/"):
        return max(600, int(minute[2:]) * 60)
    if hour.startswith("*/"):
        return max(600, int(hour[2:]) * 3600)
    if dow != "*":
        return 604800
    if dom != "*" or mon != "*":
        return 86400
    return 86400


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def judge_job(job, dry):
    jid = job.get("id", "?")
    spath = STATE / (re.sub(r"[^A-Za-z0-9_.-]", "_", jid) + ".json")
    st = load_json(spath, {})
    actions = []
    if "enabled_since" not in st:
        st["enabled_since"] = iso(now())
        st.setdefault("consecutive_failures", 0)
        st.setdefault("seen_last_run_at", None)
        save_state(jid, st)
        return actions  # grace: first observation only records the watermark

    last_run = parse_ts(job.get("last_run_at"))
    seen = st.get("seen_last_run_at")
    if job.get("last_run_at") != seen:
        # a new run happened since we last looked
        if job.get("last_run_status") == "success":
            st["consecutive_failures"] = 0
            st["last_success_at"] = job.get("last_run_at")
        else:
            st["consecutive_failures"] = st.get("consecutive_failures", 0) + 1
        st["seen_last_run_at"] = job.get("last_run_at")
        save_state(jid, st)

    cf = st.get("consecutive_failures", 0)
    today = iso(now())[:10]
    already_alerted = st.get("last_alert_date") == today

    if cf >= FAIL_THRESHOLD and job.get("enabled"):
        if not dry:
            registry_pause(jid)
        st["paused_by"] = "watchdog"
        save_state(jid, st)
        msg = (f"[{HOST}] cron auto-paused: {jid}\n"
               f"{cf} consecutive failures, last status: {job.get('last_run_status')}")
        actions.append(("pause", msg))
        if not already_alerted and not dry and notify_alert(msg, f"pause:{jid}"):
            st["last_alert_date"] = today
            save_state(jid, st)
        log_event(f"PAUSE {jid} cf={cf}")
        return actions

    interval = cron_interval_seconds(job.get("schedule", "* * * * *"))
    enabled_since = parse_ts(st["enabled_since"]) or now()
    reference = last_run if (last_run and last_run > enabled_since) else enabled_since
    if now() - reference > timedelta(seconds=GRACE_FACTOR * interval):
        msg = (f"[{HOST}] cron stalled: {jid}\n"
               f"no successful run since {st.get('last_success_at') or st['enabled_since']} "
               f"(schedule {job.get('schedule')})")
        actions.append(("stalled", msg))
        if not already_alerted and not dry and notify_alert(msg, f"stalled:{jid}"):
            st["last_alert_date"] = today
            save_state(jid, st)
        log_event(f"STALL {jid}")
    return actions


def registry_pause(job_id):
    """Flip enabled=false via atomic replace; ControlMesh's file watcher reschedules."""
    data = load_json(REGISTRY, None)
    if not data:
        return False
    for j in data.get("jobs", []):
        if j.get("id") == job_id:
            j["enabled"] = False
            break
    else:
        return False
    tmp = REGISTRY.with_suffix(".json.tmp-watchdog")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, REGISTRY)
    return True


def check_artifacts(dry):
    actions = []
    specs = load_json(ARTIFACTS, {})
    for name, spec in specs.items():
        p = Path(spec["path"])
        max_age = spec.get("max_age_hours", 24)
        min_bytes = spec.get("min_bytes", 0)
        ok = False
        detail = ""
        if not p.exists():
            detail = "missing"
        else:
            age_h = (now().timestamp() - p.stat().st_mtime) / 3600
            size = p.stat().st_size
            if age_h > max_age:
                detail = f"stale {age_h:.1f}h > {max_age}h"
            elif size < min_bytes:
                detail = f"too small {size} < {min_bytes}"
            else:
                ok = True
        key = f"artifact:{name}"
        spath = STATE / (re.sub(r"[^A-Za-z0-9_.-]", "_", key) + ".json")
        st = load_json(spath, {})
        today = iso(now())[:10]
        if not ok:
            actions.append(("artifact", f"[{HOST}] artifact problem: {name}\n{spec['path']}\n{detail}"))
            if st.get("last_alert_date") != today and not dry:
                if notify_alert(actions[-1][1], key):
                    st["last_alert_date"] = today
                    save_state(key, st)
                log_event(f"ARTIFACT {name}: {detail}")
        else:
            if st:
                st["last_alert_date"] = None
                save_state(key, st)
    return actions


def run_once(dry):
    if not REGISTRY.exists():
        print("no registry, nothing to judge")
        return
    data = load_json(REGISTRY, {})
    all_actions = []
    for job in data.get("jobs", []):
        if job.get("enabled"):
            all_actions += judge_job(job, dry)
    all_actions += check_artifacts(dry)
    for kind, msg in all_actions:
        print(f"[{kind}] {msg}")
    if not all_actions:
        print(f"{iso(now())} pass clean")


def run_daily(dry):
    data = load_json(REGISTRY, {})
    jobs = data.get("jobs", [])
    enabled = [j for j in jobs if j.get("enabled")]
    paused_today, failing, stalled = [], [], []
    for j in enabled:
        spath = STATE / (re.sub(r"[^A-Za-z0-9_.-]", "_", j["id"]) + ".json")
        st = load_json(spath, {})
        if st.get("consecutive_failures", 0) >= 1:
            failing.append(f"{j['id']}(cf={st['consecutive_failures']})")
        if st.get("last_alert_date") == iso(now())[:10]:
            (paused_today if st.get("paused_by") == "watchdog" else stalled).append(j["id"])
    art = check_artifacts(dry)
    line = (f"[{HOST}] cron daily: {len(enabled)}/{len(jobs)} enabled, "
            f"failing: {failing or 'none'}, auto-paused: {paused_today or 'none'}, "
            f"artifact issues: {len(art) or 'none'}")
    print(line)
    # The daily digest stays local; abnormal conditions notify through their own paths.


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="run one judgment pass")
    ap.add_argument("--daily", action="store_true", help="record a local-only one-line digest")
    ap.add_argument("--dry-run", action="store_true", help="no pause or notification (observation state may still update)")
    args = ap.parse_args()
    if args.daily:
        run_daily(args.dry_run)
    else:
        run_once(args.dry_run)


if __name__ == "__main__":
    main()
