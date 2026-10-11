"""Persisted callback delivery with queue reconciliation before retries."""

import time

from .client import CodexClient, RpcError


class UncertainDelivery(RuntimeError):
    """Delivery cannot be proved; manual inspection is safer than duplicating it."""


def callback_text(state):
    """Send paths and exit status, keeping the potentially large logs on disk."""
    return (
        f"[codex-callback:{state['id']}]\n"
        "This is the local background job callback configured in this task.\n"
        f"Outcome: {state['outcome']}; exit code: {state.get('returncode')}\n"
        f"Working directory: {state['cwd']}\n"
        f"Status file: {state['directory']}/status.json\n"
        f"Job log: {state['directory']}/job.log\n"
        f"Follow-up instructions: {state['followup']}"
    )


def wait_for_receipt(client, state, deadline):
    """Allow queue consumption and persisted turn history to become consistent."""
    receipt_deadline = min(deadline, time.monotonic() + 10)
    delay = 0.1
    while True:
        turn_id = client.find_turn(state["thread_id"], state["id"], state["created_at"])
        if turn_id:
            return turn_id
        remaining = receipt_deadline - time.monotonic()
        if remaining <= 0:
            raise UncertainDelivery(
                "No queue entry or matching client-message receipt after waiting. "
                "The callback will not be submitted again automatically."
            )
        time.sleep(min(delay, remaining))
        delay = min(1, delay * 2)


def deliver(state, save, client_factory=CodexClient, *, deadline=None):
    """Queue one message, then start it when the original task becomes idle.

    A callback marked started is a receipt for a new model turn, not a claim that
    the agent has completed the user's follow-up work.
    """
    callback = state["callback"]
    if callback["status"] == "started":
        return
    if deadline is None:
        deadline = time.monotonic() + state["callback_wait_seconds"]
    thread_id = state["thread_id"]
    with client_factory(state["socket_path"]) as client:
        thread = client.read_thread(thread_id)
        if thread.get("canAcceptDirectInput") is False:
            raise ValueError("The target task does not accept direct input")
        # Rejoin the existing desktop task and subscribe to its lifecycle events.
        # No model, directory, instruction, or permission overrides are sent.
        client.request("thread/resume", {"threadId": thread_id, "excludeTurns": True})
        items = list(client.queue_items(thread_id))
        existing = next(
            (item for item in items if item["clientUserMessageId"] == state["id"]), None
        )
        if existing:
            callback.update(status="queued", queue_id=existing["id"])
            save(state)
        elif callback["status"] != "pending":
            turn_id = wait_for_receipt(client, state, deadline)
            callback.update(
                status="started",
                turn_id=turn_id,
                delivered_at=time.time(),
                receipt_source="history",
            )
            save(state)
            return
        else:
            callback["status"] = "sending"
            save(state)
            result = client.request(
                "thread/queue/add",
                {
                    "threadId": thread_id,
                    "clientUserMessageId": state["id"],
                    "input": [{"type": "text", "text": callback_text(state)}],
                },
            )
            callback.update(status="queued", queue_id=result["queuedSubmission"]["id"])
            save(state)

        while time.monotonic() < deadline:
            thread = client.read_thread(thread_id)
            pending = list(client.queue_items(thread_id))
            if not any(item["id"] == callback["queue_id"] for item in pending):
                turn_id = wait_for_receipt(client, state, deadline)
                callback.update(
                    status="started",
                    turn_id=turn_id,
                    delivered_at=time.time(),
                    receipt_source="history",
                )
                save(state)
                return
            if thread["status"]["type"] == "idle":
                try:
                    result = client.request(
                        "thread/queue/start",
                        {
                            "threadId": thread_id,
                            "queuedSubmissionId": callback["queue_id"],
                        },
                    )
                except RpcError:
                    # The desktop may consume and finish the turn before this read.
                    if not any(
                        item["id"] == callback["queue_id"]
                        for item in client.queue_items(thread_id)
                    ):
                        turn_id = wait_for_receipt(client, state, deadline)
                        callback.update(
                            status="started",
                            turn_id=turn_id,
                            delivered_at=time.time(),
                            receipt_source="history",
                        )
                        save(state)
                        return
                    current = client.read_thread(thread_id)
                    if current["status"]["type"] != "active":
                        raise
                else:
                    callback.update(
                        status="started",
                        turn_id=result["turn"]["id"],
                        delivered_at=time.time(),
                        receipt_source="queue_start",
                    )
                    save(state)
                    return
            elif thread["status"]["type"] == "systemError":
                raise RuntimeError("The original Codex task is in systemError state")
            client.wait_for_change(
                thread_id, min(30, max(0, deadline - time.monotonic()))
            )
        raise TimeoutError(
            "Callback remains queued: original task did not become idle in time"
        )
