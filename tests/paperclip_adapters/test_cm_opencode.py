"""Regression checks for the local shim; every executable is a temporary fake."""

import copy
import json
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import time

import pytest


SHIM = Path(__file__).resolve().parents[2] / "scripts/paperclip/cm-opencode"


@pytest.fixture(scope="module")
def final_events():
    return runpy.run_path(str(SHIM), run_name="cm_opencode_test")["final_events"]


def observed(*extra):
    start = {"type": "step_start", "sessionID": "ses-current", "part": {"messageID": "msg-current"}}
    return "\n".join(json.dumps(event) for event in (start, *extra)) + "\n"


def exported():
    return {
        "info": {"id": "ses-current"},
        "messages": [{
            "info": {"id": "msg-current", "role": "assistant", "finish": "stop"},
            "parts": [{"type": "text", "messageID": "msg-current", "text": "final answer"}],
        }],
    }


def text_event(text="final answer"):
    return {"type": "text", "sessionID": "ses-current", "part": {"type": "text", "messageID": "msg-current", "text": text}}


@pytest.mark.parametrize("mismatch", ["old_session", "old_message", "no_stop", "error", "missing_message"])
def test_rejects_untrusted_or_unfinished_final(final_events, mismatch):
    result = exported()
    info = result["messages"][0]["info"]
    if mismatch == "old_session":
        result["info"]["id"] = "ses-old"
    elif mismatch == "old_message":
        info["id"] = "msg-old"
    elif mismatch == "no_stop":
        info["finish"] = "tool-calls"
    elif mismatch == "error":
        info["error"] = {"name": "ProviderError"}
    else:
        info.pop("id")
    with pytest.raises(ValueError):
        final_events(observed(), result)


def test_rejects_partial_delivered_text(final_events):
    with pytest.raises(ValueError, match="Partial final text"):
        final_events(observed(text_event("final")), exported())


def test_complete_text_is_not_duplicated(final_events):
    assert final_events(observed(text_event()), exported()) == []


def test_recovers_only_observed_current_message(final_events):
    result = exported()
    old = copy.deepcopy(result["messages"][0])
    old["info"]["id"] = "msg-old"
    old["parts"][0].update(messageID="msg-old", text="old answer must not appear")
    result["messages"].insert(0, old)
    assert final_events(observed(), result) == [text_event()]


FAKE_CLI = r'''
import json
import os
from pathlib import Path
import signal
import stat
import sys
import time

root = Path(os.environ["CMO_TEST_ROOT"])
mode = os.environ["CMO_TEST_MODE"]
args = sys.argv[1:]
action = args[0] if args else "empty"
(root / (action + ".pid")).write_text(str(os.getpid()))
with (root / "calls.jsonl").open("a") as stream:
    stream.write(json.dumps(args) + "\n")
if stat.S_ISREG(os.fstat(1).st_mode):
    stdout_path = Path(os.readlink("/proc/self/fd/1"))
    (root / (action + ".mode.json")).write_text(json.dumps({
        "file": stat.S_IMODE(os.fstat(1).st_mode),
        "directory": stat.S_IMODE(stdout_path.parent.stat().st_mode),
    }))

def wait_forever():
    def terminated(signum, frame):
        (root / (action + ".terminated")).write_text(str(signum))
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, terminated)
    (root / (action + ".ready")).touch()
    while True:
        time.sleep(0.05)

answer = "recovered answer" if mode != "large" else "A" * 150000
info = {"id": "msg-current", "role": "assistant", "finish": "stop"}
part = {"type": "text", "messageID": "msg-current", "text": answer}
if action == "run" and ("--help" in args or "-h" in args):
    print("FAKE_RUN_HELP")
elif action == "run" and not ("--format=json" in args or "--format" in args):
    print("FAKE_PLAIN_OUTPUT")
elif action == "run":
    print(json.dumps({"type": "step_start", "sessionID": "ses-current", "part": {"messageID": "msg-current"}}), flush=True)
    if mode == "wait_run":
        wait_forever()
    if mode == "truncate":
        sys.stdout.write('{"type":"text","sessionID":"ses-current","part":{"text":"cut')
        sys.stdout.flush()
    elif mode == "complete":
        print(json.dumps({"type": "text", "sessionID": "ses-current", "part": part}))
elif action == "export":
    if mode == "wait_export":
        wait_forever()
    print(json.dumps({"info": {"id": "ses-current"}, "messages": [{"info": info, "parts": [part]}]}))
else:
    print("FAKE_OTHER_OUTPUT")
'''


@pytest.fixture
def fake_cli(tmp_path):
    fake = tmp_path / "fake-opencode"
    fake.write_text("#!" + sys.executable + "\n" + FAKE_CLI)
    fake.chmod(0o700)
    shim = tmp_path / "cm-opencode"
    source = SHIM.read_text()
    original = 'REAL = "/usr/local/bin/opencode"'
    assert source.count(original) == 1, "Refuse to run without replacing the real CLI"
    shim.write_text(source.replace(original, "REAL = " + repr(str(fake))))
    env = dict(os.environ, CMO_TEST_ROOT=str(tmp_path), CMO_TEST_MODE="recover", PYTHONDONTWRITEBYTECODE="1")
    return shim, env, tmp_path


def invoke(fake_cli, args, mode="recover"):
    shim, env, _ = fake_cli
    return subprocess.run([sys.executable, str(shim), *args], env=dict(env, CMO_TEST_MODE=mode), capture_output=True, text=True, timeout=10)


def valid_events(stdout):
    events = []
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass  # The upstream fragment may remain, but recovery must be a separate line.
    return events


@pytest.mark.parametrize("args,expected", [
    (["run", "hello"], "FAKE_PLAIN_OUTPUT"),
    (["run", "--help"], "FAKE_RUN_HELP"),
    (["run", "--format", "json", "--help"], "FAKE_RUN_HELP"),
    (["models"], "FAKE_OTHER_OUTPUT"),
])
def test_non_json_help_and_other_commands_are_passthrough(fake_cli, args, expected):
    result = invoke(fake_cli, args)
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected + "\n"
    calls = [json.loads(line) for line in (fake_cli[2] / "calls.jsonl").read_text().splitlines()]
    assert calls == [args]


@pytest.mark.parametrize("format_args", [["--format", "json"], ["--format=json"]])
def test_truncated_tail_does_not_swallow_recovered_answer(fake_cli, format_args):
    result = invoke(fake_cli, ["run", *format_args, "hello"], mode="truncate")
    assert result.returncode == 0, result.stderr
    texts = [event["part"]["text"] for event in valid_events(result.stdout) if event.get("type") == "text"]
    assert texts == ["recovered answer"], repr(result.stdout)


def test_complete_cli_text_is_not_duplicated(fake_cli):
    result = invoke(fake_cli, ["run", "--format", "json", "hello"], mode="complete")
    assert result.returncode == 0, result.stderr
    texts = [event["part"]["text"] for event in valid_events(result.stdout) if event.get("type") == "text"]
    assert texts == ["recovered answer"]


def test_large_export_is_complete_and_temporary_files_are_private(fake_cli):
    result = invoke(fake_cli, ["run", "--format", "json", "hello"], mode="large")
    assert result.returncode == 0, result.stderr
    texts = [event["part"]["text"] for event in valid_events(result.stdout) if event.get("type") == "text"]
    assert texts == ["A" * 150000]
    for action in ("run", "export"):
        modes = json.loads((fake_cli[2] / (action + ".mode.json")).read_text())
        assert modes == {"file": 0o600, "directory": 0o700}


def test_direct_export_preserves_complete_json(fake_cli):
    result = invoke(fake_cli, ["export", "ses-current"], mode="large")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["messages"][0]["parts"][0]["text"] == "A" * 150000


@pytest.mark.parametrize("action", ["run", "export"])
def test_terminating_only_shim_pid_reaps_active_child(fake_cli, action):
    shim, env, root = fake_cli
    process = subprocess.Popen(
        [sys.executable, str(shim), "run", "--format", "json", "hello"],
        env=dict(env, CMO_TEST_MODE="wait_" + action),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        ready = root / (action + ".ready")
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.02)
        assert ready.exists(), "Fake child did not reach the intended phase"
        child_pid = int((root / (action + ".pid")).read_text())
        process.send_signal(signal.SIGTERM)  # Deliberately not a process-group signal.
        stdout, stderr = process.communicate(timeout=8)
        assert process.returncode == 128 + signal.SIGTERM, (stdout, stderr)
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        # A failed regression must not leave its own fake process behind.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate(timeout=3)
