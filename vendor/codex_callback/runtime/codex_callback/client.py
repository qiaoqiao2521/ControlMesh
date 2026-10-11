"""A small JSON-RPC client for the existing local Codex daemon."""

import json
import time
from collections import deque
from pathlib import Path

from .transport import UnixWebSocket


class RpcError(RuntimeError):
    """An explicit error returned by Codex, distinct from a lost connection."""

    def __init__(self, method, error):
        self.method = method
        self.error = error
        super().__init__(f"{method}: {error}")


class CodexClient:
    """Connect to the user's running daemon without launching another server."""

    def __init__(self, socket_path, timeout=20):
        self.socket_path = Path(socket_path)
        self.timeout = timeout
        self.ws = None
        self.sequence = 0
        self.events = deque()

    def __enter__(self):
        try:
            self.ws = UnixWebSocket(self.socket_path, self.timeout)
            self.server = self.request(
                "initialize",
                {
                    "clientInfo": {"name": "codex_local_callback", "version": "0.1.0"},
                    "capabilities": {
                        "experimentalApi": True,
                        "requestAttestation": False,
                    },
                },
            )
            self.ws.send(json.dumps({"method": "initialized"}))
            return self
        except BaseException:
            if self.ws is not None:
                self.ws.close()
            raise

    def __exit__(self, *args):
        self.ws.close()

    def _receive(self, timeout):
        raw = self.ws.recv(timeout)
        if not raw:
            raise ConnectionError("Codex disconnected")
        return json.loads(raw)

    def request(self, method, params):
        """Wait for one response; leave notifications for the event waiter."""
        self.sequence += 1
        request_id = self.sequence
        deadline = time.monotonic() + self.timeout
        self.ws.send(json.dumps({"id": request_id, "method": method, "params": params}))
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(method)
            message = self._receive(remaining)
            if message.get("id") == request_id and "method" not in message:
                if "error" in message:
                    raise RpcError(method, message["error"])
                return message["result"]
            # Only retain state changes. Never collect token deltas or answer approvals.
            if message.get("method") in {
                "turn/completed",
                "thread/status/changed",
                "thread/queue/changed",
            }:
                self.events.append(message)

    def read_thread(self, thread_id):
        return self.request(
            "thread/read", {"threadId": thread_id, "includeTurns": False}
        )["thread"]

    def queue_items(self, thread_id):
        """Read the pending queue, including all pages."""
        cursor = None
        while True:
            page = self.request(
                "thread/queue/list",
                {"threadId": thread_id, "cursor": cursor, "limit": 100},
            )
            yield from page["data"]
            cursor = page.get("nextCursor")
            if not cursor:
                return

    def find_turn(self, thread_id, event_id, created_at):
        """Find a receipt in recent turns without sending history to a model."""
        cursor = None
        while True:
            page = self.request(
                "thread/turns/list",
                {
                    "threadId": thread_id,
                    "cursor": cursor,
                    "limit": 20,
                    "sortDirection": "desc",
                    "itemsView": "full",
                },
            )
            for turn in page["data"]:
                for item in turn.get("items", []):
                    if (
                        item.get("type") == "userMessage"
                        and item.get("clientId") == event_id
                    ):
                        return turn["id"]
                started = turn.get("startedAt")
                if started is not None and started < created_at - 60:
                    return None
            cursor = page.get("nextCursor")
            if not cursor:
                return None

    def wait_for_change(self, thread_id, timeout=30):
        """Wait locally for a task event; timeout only causes a local status read."""
        deadline = time.monotonic() + timeout
        while True:
            if self.events:
                message = self.events.popleft()
            else:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
                try:
                    message = self._receive(remaining)
                except TimeoutError:
                    return
            if message.get("params", {}).get("threadId") == thread_id and message.get(
                "method"
            ) in {"turn/completed", "thread/status/changed", "thread/queue/changed"}:
                return
