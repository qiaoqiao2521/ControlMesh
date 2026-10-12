#!/usr/bin/env python3
"""Human-only credential repair for Moon's existing encrypted bot record.

No registration, OAuth, message send, polling, model call or listener starts here.
The controller must fence the event subscriber and active tasks before use.
"""

import contextlib
import fcntl
import getpass
import hashlib
import json
import logging
import os
import resource
import stat
import sys
import warnings
from pathlib import Path

APP_ID = "cli_a96fb3b784b8dbdd"
BOT_NAME = "月神"
CONFIG = Path("/opt/cm-feishu-moonrise/host-binding.json")
STATE = Path("/var/lib/cm-feishu-moonrise")


class RebindError(Exception):
    def __init__(self, stage):
        self.stage = stage
        super().__init__()


def require(condition, stage):
    if not condition:
        raise RebindError(stage)


def pinned_identity(config):
    require(
        config.get("app_id") == APP_ID
        and config.get("brand") == "feishu"
        and config.get("state_dir") == str(STATE)
        and isinstance(config.get("owner_open_id"), str)
        and bool(config["owner_open_id"])
        and isinstance(config.get("private_chat_id"), str)
        and bool(config["private_chat_id"]),
        "host_identity",
    )
    return config


def verify_records(bot, binding, identity):
    for key in ("app_id", "owner_open_id", "brand"):
        require(bot.get(key) == identity[key], "store_identity")
    for key in ("app_id", "owner_open_id", "private_chat_id"):
        require(binding.get(key) == identity[key], "binding_identity")
    require(binding.get("version") == 1 and binding.get("verified") is True,
            "binding_unverified")
    require(bot.get("owner_source") in {
        "registration", "authenticated_app_info", "host_profile"
    }, "owner_unverified")


def validate_candidate(auth, session, identity):
    info = auth.get_app_info(force_refresh=True)
    require(info.app_id == APP_ID
            and info.effective_owner_open_id == identity["owner_open_id"],
            "platform_app_identity")
    # The kit's existing client supplies tenant auth; this endpoint is read-only.
    token = auth.get_tenant_access_token().token
    response = session.request(
        "GET", auth.domains.open_base + "/open-apis/bot/v3/info",
        headers={"Authorization": "Bearer " + token},
    )
    require(response.status_code == 200, "platform_bot_http")
    payload = response.json()
    require(isinstance(payload, dict) and payload.get("code") == 0,
            "platform_bot_rejected")
    bot = payload.get("bot")
    require(isinstance(bot, dict)
            and isinstance(bot.get("open_id"), str) and bool(bot["open_id"])
            and bot.get("app_name") == BOT_NAME, "platform_bot_identity")
    return bot["open_id"]


def update_records(store, identity, secret, bot_open_id):
    """Caller holds listener, binding and tenant-cache locks throughout.

    Cache invalidation comes first. Credential state can become unknown if a
    later bot write fails, including after an atomic replacement.
    """
    bot = store.read("bot")
    binding = store.read("binding")
    verify_records(bot, binding, identity)
    if bot.get("bot_open_id"):
        require(bot["bot_open_id"] == bot_open_id, "stored_bot_identity")
    if store.exists("tenant_tokens"):
        cache = store.read("tenant_tokens")
        cache_key = hashlib.sha256(
            ("https://open.feishu.cn\0" + APP_ID).encode()
        ).hexdigest()
        if cache_key in cache:
            cache.pop(cache_key)
            store.write("tenant_tokens", cache)
    replacement = dict(bot)
    replacement["app_secret"] = secret
    try:
        store.write("bot", replacement)
    except BaseException:
        # Atomic replace may have happened before a directory-fsync failure.
        # Never assert unchanged credentials or overwrite them with a rollback.
        raise RebindError("bot_write_unknown") from None


@contextlib.contextmanager
def private_lock(path):
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        meta = os.fstat(fd)
        require(stat.S_ISREG(meta.st_mode)
                and stat.S_IMODE(meta.st_mode) == 0o600
                and meta.st_uid == os.getuid(), "unsafe_lock")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RebindError("runtime_busy") from None
        yield
    finally:
        os.close(fd)


def load_config():
    fd = os.open(CONFIG, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as handle:
        meta = os.fstat(handle.fileno())
        require(stat.S_ISREG(meta.st_mode)
                and stat.S_IMODE(meta.st_mode) == 0o600
                and meta.st_uid == os.getuid(), "unsafe_config")
        return pinned_identity(json.load(handle))


def verify_state_paths():
    for path in (STATE, STATE / "private", STATE / "private" / "keys",
                 STATE / "private" / "records", STATE / "private" / "realtime"):
        meta = path.lstat()
        require(stat.S_ISDIR(meta.st_mode)
                and stat.S_IMODE(meta.st_mode) == 0o700
                and meta.st_uid == os.getuid(), "unsafe_state_directory")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    stage, saved = "preflight", False
    secret, auth = None, None
    try:
        require(not argv, "unexpected_arguments")
        require(os.getuid() == 1000 and os.geteuid() == 1000, "user_must_be_cm_agent")
        require(sys.stdin.isatty() and sys.stderr.isatty(), "tty_required")
        os.umask(0o077)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        logging.disable(logging.CRITICAL)
        identity = load_config()
        verify_state_paths()
        import requests
        from feishu_auth_kit.client import FeishuAuthClient
        from feishu_auth_kit.transport.cloud_bridge import EncryptedStore

        class BoundedSession(requests.Session):
            def request(self, method, url, **kwargs):
                require((method.upper(), url) in {
                    ("POST", "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"),
                    ("GET", "https://open.feishu.cn/open-apis/application/v6/applications/me"),
                    ("GET", "https://open.feishu.cn/open-apis/bot/v3/info"),
                }, "unexpected_endpoint")
                kwargs.update(timeout=(10, 20), allow_redirects=False)
                return super().request(method, url, **kwargs)

        store = EncryptedStore(STATE)
        with private_lock(store.private / "realtime" / "listener.lock"), \
                private_lock(store.private / "chat.lock"), \
                private_lock(store.private / "tenant-token.lock"):
            # Reads use the kit's existing encrypted store; nothing is exported.
            verify_records(store.read("bot"), store.read("binding"), identity)
            stage = "secret_input"
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                secret = getpass.getpass("Moon 原 App 当前 Secret（隐藏输入）: ")
            require(bool(secret) and secret == secret.strip(), "empty_or_padded_secret")
            stage = "platform_validation"
            with BoundedSession() as session:
                session.trust_env = False
                auth = FeishuAuthClient(APP_ID, secret, brand="feishu", session=session)
                bot_open_id = validate_candidate(auth, session, identity)
            stage = "save"
            # An interrupt can arrive after write() returns and before the next
            # statement. Once saving begins, never claim credentials unchanged.
            saved = "unknown"
            update_records(store, identity, secret, bot_open_id)
            saved = True
        print(json.dumps({"status": "credentials_updated", "app_id": APP_ID,
                          "credentials_saved": True, "listener_started": False}))
        return 0
    except BaseException as exc:
        # Never format exception args, response bodies, secrets or issued tokens.
        if isinstance(exc, RebindError):
            stage = exc.stage
        if stage == "bot_write_unknown":
            saved = "unknown"
        print(json.dumps({"status": "failed", "stage": stage,
                          "credentials_saved": saved}))
        return 1
    finally:
        if auth is not None:
            auth.app_secret = ""
            auth._tenant_token = None
        secret = None


if __name__ == "__main__":
    raise SystemExit(main())
