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
from urllib.parse import urlsplit
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
    lark = config.get("lark")
    if lark is None and "native_clock" not in config:
        lark = {"user": "agent436", "home": "/var/lib/agent436",
                "path": "/opt/agent-tools/node-v24.21.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin",
                "cli": "/opt/cm-tools/node_modules/.bin/lark-cli", "profile": "cm436"}
    if (not isinstance(lark, dict)
            or not all(isinstance(lark.get(k), str) and lark[k] for k in ("user", "home", "path", "cli", "profile"))
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", lark["user"])
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", lark["profile"])
            or not Path(lark["home"]).is_absolute() or not Path(lark["cli"]).is_absolute()
            or not all(Path(p).is_absolute() for p in lark["path"].split(":"))):
        log_event("NOTIFY_FAILED feishu missing_or_invalid_lark_route")
        return False
    key = hashlib.sha256(f"{HOST}:{lark['profile']}:{iso(now())[:10]}:{event_key}".encode()).hexdigest()[:32]
    command = [
        "/usr/sbin/runuser", "-u", lark["user"], "--", "/usr/bin/env", "-i",
        "HOME=" + lark["home"], "PATH=" + lark["path"],
        lark["cli"], "--profile", lark["profile"],
        "im", "+messages-send", "--as", "bot", "--chat-id", chat_id,
        "--text", text[:3500], "--idempotency-key", lark["profile"][:17] + "-" + key,
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


def native_cli(clock, *args):
    result = subprocess.run([clock["bin"], *args, "--context", clock["context"],
                             "--profile", clock["profile"], "--json"],
                            capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        raise ValueError("native_cli_failed")
    payload = json.loads(result.stdout)
    if isinstance(payload, dict) and "data" in payload:
        if payload.get("ok") is False or payload.get("code", 0) not in (0, "0"):
            raise ValueError("native_cli_rejected")
        payload = payload["data"]
    return payload


def observed_jobs(data):
    """Use the declared native clock; an unknown snapshot never falls back to legacy."""
    config = load_json(NOTIFICATION_CONFIG, None)
    legacy = data.get("jobs", [])
    if NOTIFICATION_CONFIG.exists() and not isinstance(config, dict):
        log_event("NATIVE_CLOCK_UNKNOWN invalid_notification_config")
        return [], "native clock unknown: invalid notification configuration"
    if config is None or "native_clock" not in config:
        return legacy, None
    try:
        clock = config["native_clock"]
        if not isinstance(clock, dict):
            raise ValueError("invalid_clock")
        for key in ("bin", "context", "profile", "company_id", "activated_at"):
            if not isinstance(clock.get(key), str) or not clock[key]:
                raise ValueError("invalid_clock")
        if not all(Path(clock[key]).is_absolute() for key in ("bin", "context")):
            raise ValueError("invalid_clock")
        activated = parse_ts(clock["activated_at"])
        expected = clock.get("expected_job_ids")
        if (not activated or activated.tzinfo is None or activated > now()
                or not isinstance(expected, list) or not expected
                or not all(isinstance(jid, str) and jid for jid in expected)
                or len(set(expected)) != len(expected)):
            raise ValueError("invalid_clock")
        context = load_json(clock["context"], {})
        profile = context.get("profiles", {}).get(clock["profile"], {})
        endpoint = urlsplit(profile.get("apiBase", ""))
        if (profile.get("companyId") != clock["company_id"] or endpoint.scheme != "http"
                or endpoint.hostname not in ("127.0.0.1", "localhost", "::1")):
            raise ValueError("context_company_mismatch")
        routines = native_cli(clock, "routine", "list", "-C", clock["company_id"])
        if not isinstance(routines, list):
            raise ValueError("invalid_snapshot")
        registry = {j.get("id"): j for j in legacy if isinstance(j, dict)}
        mapped = {}
        for routine in routines:
            variables = routine.get("variables") if isinstance(routine, dict) else None
            bindings = [v.get("defaultValue") for v in variables or []
                        if isinstance(v, dict) and v.get("name") == "cmJobId"]
            if not any(jid in expected for jid in bindings if isinstance(jid, str)):
                continue
            if (len(bindings) != 1 or bindings[0] in mapped
                    or routine.get("companyId") != clock["company_id"]):
                raise ValueError("invalid_mapping")
            jid = bindings[0]
            if jid not in registry or not routine.get("id"):
                raise ValueError("missing_registry_mapping")
            triggers = [t for t in routine.get("triggers", [])
                        if isinstance(t, dict) and t.get("kind") == "schedule"]
            if (not triggers or routine.get("status") not in ("active", "paused")
                    or any(not t.get("id") or not isinstance(t.get("enabled"), bool) for t in triggers)):
                raise ValueError("invalid_schedule")
            job = dict(registry[jid])
            job.update(enabled=routine["status"] == "active" and any(t["enabled"] for t in triggers),
                       last_run_at=None, last_run_status=None,
                       _native_clock=clock, _native_routine_id=routine["id"],
                       _native_triggers=[t["id"] for t in triggers if t["enabled"]])
            receipt = parse_ts(job.get("manual_run_at"))
            status = job.get("manual_run_status")
            if receipt is not None and receipt.tzinfo is not None and activated <= receipt <= now():
                if status not in ("success", "error", "failed", "timeout", "cancelled", "skipped_quiet_hours", "quiet_skipped"):
                    raise ValueError("unknown_receipt_status")
                job.update(last_run_at=job["manual_run_at"], last_run_status=status)
            mapped[jid] = job
        if set(mapped) != set(expected):
            raise ValueError("missing_native_mapping")
        jobs = [mapped[jid] for jid in expected]
        for job in jobs:
            if not job["enabled"]:
                spath = STATE / (re.sub(r"[^A-Za-z0-9_.-]", "_", job["id"]) + ".json")
                st = load_json(spath, {})
                st["native_paused_at"] = iso(now())
                save_state(job["id"], st)
        return jobs, "native schedules: %s active, %s paused" % (
            sum(j["enabled"] for j in jobs), sum(not j["enabled"] for j in jobs))
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, AttributeError, KeyError):
        log_event("NATIVE_CLOCK_UNKNOWN snapshot_or_mapping_unavailable")
        return [], "native clock unknown: snapshot or mapping unavailable"


def judge_job(job, dry):
    jid = job.get("id", "?")
    spath = STATE / (re.sub(r"[^A-Za-z0-9_.-]", "_", jid) + ".json")
    st = load_json(spath, {})
    actions = []
    native = job.get("_native_clock")
    if native and (st.get("native_clock_epoch") != native["activated_at"] or st.get("native_paused_at")):
        activated = parse_ts(native["activated_at"])
        paused_at = parse_ts(st.get("native_paused_at"))
        resume = paused_at if paused_at and paused_at.tzinfo is not None and paused_at <= now() else activated
        st = {"enabled_since": iso(max(activated, resume)), "consecutive_failures": 0,
              "seen_last_run_at": None, "native_clock_epoch": native["activated_at"]}
        save_state(jid, st)
    if "enabled_since" not in st:
        st["enabled_since"] = iso(now())
        st.setdefault("consecutive_failures", 0)
        st.setdefault("seen_last_run_at", None)
        save_state(jid, st)
        return actions  # grace: first observation only records the watermark

    last_run = parse_ts(job.get("last_run_at"))
    if native and last_run and last_run < parse_ts(st["enabled_since"]):
        job = dict(job, last_run_at=None, last_run_status=None)
        last_run = None
    seen = st.get("seen_last_run_at")
    if job.get("last_run_at") != seen:
        # a new run happened since we last looked
        if job.get("last_run_status") == "success":
            st["consecutive_failures"] = 0
            st["last_success_at"] = job.get("last_run_at")
        elif job.get("last_run_status") not in ("skipped_quiet_hours", "quiet_skipped"):
            st["consecutive_failures"] = st.get("consecutive_failures", 0) + 1
        st["seen_last_run_at"] = job.get("last_run_at")
        save_state(jid, st)

    cf = st.get("consecutive_failures", 0)
    today = iso(now())[:10]
    already_alerted = st.get("last_alert_date") == today

    if (cf >= FAIL_THRESHOLD and job.get("enabled")
            and job.get("last_run_status") not in ("skipped_quiet_hours", "quiet_skipped")):
        if not dry:
            paused = registry_pause(jid, job) if native else registry_pause(jid)
            if native and not paused:
                msg = f"[{HOST}] cron pause failed: {jid}; native schedule state unconfirmed"
                actions.append(("pause_failed", msg))
                if not already_alerted and notify_alert(msg, f"pause_failed:{jid}"):
                    st["last_alert_date"] = today
                    save_state(jid, st)
                log_event(f"PAUSE_FAILED {jid}")
                return actions
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


def registry_pause(job_id, native_job=None):
    """Flip enabled=false via atomic replace; ControlMesh's file watcher reschedules."""
    if native_job is not None:
        clock = native_job["_native_clock"]
        trigger_ids = native_job["_native_triggers"]
        try:
            for trigger_id in trigger_ids:
                native_cli(clock, "routine", "trigger:update", trigger_id,
                           "--payload-json", '{"enabled":false}')
            # Verify the native mutation; the preserved legacy registry is not its clock.
            routines = native_cli(clock, "routine", "list", "-C", clock["company_id"])
            routine = next((r for r in routines if r.get("id") == native_job["_native_routine_id"]
                            and r.get("companyId") == clock["company_id"]), None)
            observed = {t.get("id"): t.get("enabled") for t in routine.get("triggers", [])
                        if t.get("kind") == "schedule"} if routine else {}
            return bool(trigger_ids) and all(observed.get(tid) is False for tid in trigger_ids)
        except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, AttributeError, KeyError):
            return False
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
    config = load_json(NOTIFICATION_CONFIG, None)
    if not REGISTRY.exists() and (not NOTIFICATION_CONFIG.exists()
            or isinstance(config, dict) and "native_clock" not in config):
        print("no registry, nothing to judge")
        return
    data = load_json(REGISTRY, {})
    all_actions = []
    jobs, observation = observed_jobs(data)
    if observation:
        print(observation)
    for job in jobs:
        if job.get("enabled"):
            all_actions += judge_job(job, dry)
    all_actions += check_artifacts(dry)
    for kind, msg in all_actions:
        print(f"[{kind}] {msg}")
    if not all_actions and not observation:
        print(f"{iso(now())} pass clean")


def run_daily(dry):
    data = load_json(REGISTRY, {})
    jobs, observation = observed_jobs(data)
    if observation:
        print(observation)
    enabled = [j for j in jobs if j.get("enabled")]
    paused_today, failing, stalled = [], [], []
    for j in enabled:
        spath = STATE / (re.sub(r"[^A-Za-z0-9_.-]", "_", j["id"]) + ".json")
        st = load_json(spath, {})
        if j.get("_native_clock") and st.get("native_clock_epoch") != j["_native_clock"]["activated_at"]:
            continue
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
