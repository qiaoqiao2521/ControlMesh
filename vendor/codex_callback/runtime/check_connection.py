"""Read the original desktop task without starting a model turn."""

import os
from pathlib import Path

from codex_callback.client import CodexClient

THREAD_ID = None  # Set an explicit UUID when running outside a Codex task.
SOCKET_PATH = (
    Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    / "app-server-control/app-server-control.sock"
)


def main():
    """Print connection and queue metadata, never task conversation content."""
    thread_id = THREAD_ID or os.environ["CODEX_THREAD_ID"]
    with CodexClient(SOCKET_PATH) as client:
        thread = client.read_thread(thread_id)
        print(client.server["userAgent"])
        print(f"Task: {thread.get('name')} ({thread['id']})")
        print(f"Status: {thread['status']}")
        print(f"Queue length: {len(list(client.queue_items(thread_id)))}")


if __name__ == "__main__":
    main()
