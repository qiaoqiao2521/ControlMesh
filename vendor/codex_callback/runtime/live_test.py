"""Run one short job and send one real callback to the current Codex task."""

import sys
from pathlib import Path

from codex_callback import start_job

COMMAND = [
    sys.executable,
    "-c",
    "import time; time.sleep(10); print('CODEX_CALLBACK_LIVE_TEST_OK')",
]
WORKING_DIRECTORY = Path(__file__).resolve().parent
FOLLOWUP = (
    "This is a Codex Callback acceptance-test event. Read status.json and "
    "job.log, report whether the marker CODEX_CALLBACK_LIVE_TEST_OK is present, "
    "then stop. Do not rerun the job or create another callback."
)
TIMEOUT_SECONDS = 60


def main():
    """Launch one bounded acceptance job for the current Codex task."""
    directory = start_job(
        COMMAND,
        cwd=WORKING_DIRECTORY,
        followup=FOLLOWUP,
        timeout_seconds=TIMEOUT_SECONDS,
    )
    print(f"Live test record: {directory}")


if __name__ == "__main__":
    main()
