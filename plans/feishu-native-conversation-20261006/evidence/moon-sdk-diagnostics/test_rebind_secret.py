import copy
import contextlib
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location(
    "rebind_secret", Path(__file__).with_name("rebind_secret.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def identity():
    return dict(app_id=m.APP_ID, brand="feishu", state_dir=str(m.STATE),
                owner_open_id="fixture_owner", private_chat_id="fixture_chat")


class Store:
    def __init__(self):
        cfg = identity()
        self.records = {
            "bot": dict(app_id=m.APP_ID, brand="feishu", owner_open_id=cfg["owner_open_id"],
                        owner_source="registration", app_secret="fixture_old", extra="preserved"),
            "binding": dict(app_id=m.APP_ID, owner_open_id=cfg["owner_open_id"],
                            private_chat_id=cfg["private_chat_id"], version=1, verified=True,
                            chat_seen_ids=["fixture_seen"], pending_receipts={"fixture": "unknown"}),
            "registration": {"status": "completed"},
            "tenant_tokens": {cache_key(): {"token": "fixture_cache"},
                              "unrelated_app": {"token": "fixture_other"}},
        }
        self.writes = []

    def read(self, name):
        return copy.deepcopy(self.records[name])

    def exists(self, name):
        return name in self.records

    def write(self, name, value):
        self.writes.append(name)
        self.records[name] = copy.deepcopy(value)


def cache_key():
    return hashlib.sha256(("https://open.feishu.cn\0" + m.APP_ID).encode()).hexdigest()


def test_preserves_binding_ledger_and_other_credentials():
    store = Store()
    before = copy.deepcopy(store.records)
    m.update_records(store, identity(), "fixture_new", "fixture_bot")
    assert store.writes == ["tenant_tokens", "bot"]
    assert store.records["binding"] == before["binding"]
    assert store.records["registration"] == before["registration"]
    assert store.records["bot"] == {**before["bot"], "app_secret": "fixture_new"}
    assert store.records["tenant_tokens"] == {"unrelated_app": {"token": "fixture_other"}}


@pytest.mark.parametrize("record,key,value", [
    ("bot", "app_id", "another_app"), ("bot", "owner_open_id", "another_owner"),
    ("binding", "private_chat_id", "another_chat"), ("binding", "verified", False),
    ("bot", "bot_open_id", "another_bot"),
])
def test_identity_mismatch_never_writes(record, key, value):
    store = Store()
    store.records[record][key] = value
    with pytest.raises(m.RebindError):
        m.update_records(store, identity(), "fixture_new", "fixture_bot")
    assert store.writes == []


def test_write_failure_preserves_old_bot_after_cache_invalidation():
    store = Store()
    original_write = store.write
    def fail_bot(name, value):
        if name == "bot":
            raise OSError("fixture_not_output")
        return original_write(name, value)
    store.write = fail_bot
    with pytest.raises(m.RebindError, match="") as result:
        m.update_records(store, identity(), "fixture_new", "fixture_bot")
    assert result.value.stage == "bot_write_unknown"
    assert store.records["bot"]["app_secret"] == "fixture_old"
    assert cache_key() not in store.records["tenant_tokens"]
    assert store.writes == ["tenant_tokens"]


def test_post_replace_failure_reports_unknown_and_never_rolls_back():
    store = Store()
    original_write = store.write
    def fail_after_replace(name, value):
        original_write(name, value)
        if name == "bot":
            raise OSError("fixture_after_replace")
    store.write = fail_after_replace
    with pytest.raises(m.RebindError) as result:
        m.update_records(store, identity(), "fixture_new", "fixture_bot")
    assert result.value.stage == "bot_write_unknown"
    assert store.records["bot"]["app_secret"] == "fixture_new"
    assert store.writes == ["tenant_tokens", "bot"]


def validation_fixtures(app_id=None, owner=None, name=None):
    auth = SimpleNamespace(
        get_app_info=lambda **kw: SimpleNamespace(
            app_id=app_id or m.APP_ID, effective_owner_open_id=owner or "fixture_owner"),
        get_tenant_access_token=lambda: SimpleNamespace(token="fixture_tenant"),
        domains=SimpleNamespace(open_base="https://open.feishu.cn"),
    )
    calls = []
    def request(method, url, **kw):
        calls.append((method, url))
        return SimpleNamespace(status_code=200, json=lambda: {
            "code": 0, "bot": {"open_id": "fixture_bot", "app_name": name or m.BOT_NAME}
        })
    return auth, SimpleNamespace(request=request), calls


def test_only_reads_platform_bot_identity():
    auth, session, calls = validation_fixtures()
    assert m.validate_candidate(auth, session, identity()) == "fixture_bot"
    assert calls == [("GET", "https://open.feishu.cn/open-apis/bot/v3/info")]


@pytest.mark.parametrize("field", ["app_id", "owner", "name"])
def test_platform_identity_rejected(field):
    auth, session, calls = validation_fixtures(**{field: "another_identity"})
    with pytest.raises(m.RebindError):
        m.validate_candidate(auth, session, identity())
    if field in {"app_id", "owner"}:
        assert calls == []


def test_failure_does_not_format_exception(monkeypatch, capsys):
    class UnsafeException(Exception):
        def __str__(self):
            raise AssertionError("must never format upstream exception")
    monkeypatch.setattr(m.os, "getuid", lambda: 1000)
    monkeypatch.setattr(m.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(m.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(m.sys.stderr, "isatty", lambda: True)
    monkeypatch.setattr(m.os, "umask", lambda value: 0o077)
    monkeypatch.setattr(m.resource, "setrlimit", lambda *a: None)
    monkeypatch.setattr(m.logging, "disable", lambda *a: None)
    monkeypatch.setattr(m, "load_config", lambda: (_ for _ in ()).throw(UnsafeException("fixture_sensitive")))
    assert m.main([]) == 1
    result = capsys.readouterr()
    assert "fixture_sensitive" not in result.out + result.err
    assert '"stage": "preflight"' in result.out


def test_noninteractive_run_rejected_before_store_read(monkeypatch, capsys):
    monkeypatch.setattr(m.os, "getuid", lambda: 1000)
    monkeypatch.setattr(m.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(m.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(m, "load_config", lambda: pytest.fail("must not read private store"))
    assert m.main([]) == 1
    assert '"stage": "tty_required"' in capsys.readouterr().out


def test_interrupt_after_successful_write_reports_unknown(monkeypatch, capsys):
    store = Store()
    monkeypatch.setattr(m.os, "getuid", lambda: 1000)
    monkeypatch.setattr(m.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(m.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(m.sys.stderr, "isatty", lambda: True)
    monkeypatch.setattr(m.os, "umask", lambda value: 0o077)
    monkeypatch.setattr(m.resource, "setrlimit", lambda *a: None)
    monkeypatch.setattr(m.logging, "disable", lambda *a: None)
    monkeypatch.setattr(m, "load_config", identity)
    monkeypatch.setattr(m, "verify_state_paths", lambda: None)
    monkeypatch.setattr(m, "private_lock", lambda path: contextlib.nullcontext())
    monkeypatch.setattr(m.getpass, "getpass", lambda prompt: "fixture_new")
    monkeypatch.setattr(m, "validate_candidate", lambda *a: "fixture_bot")
    auth = SimpleNamespace(app_secret="fixture_new", _tenant_token="fixture_token")
    monkeypatch.setitem(sys.modules, "feishu_auth_kit.client",
                        SimpleNamespace(FeishuAuthClient=lambda *a, **kw: auth))
    monkeypatch.setitem(sys.modules, "feishu_auth_kit.transport.cloud_bridge",
                        SimpleNamespace(EncryptedStore=lambda root: store))
    store.private = Path("/fixture/private")
    original_update = m.update_records

    def interrupted(*args):
        original_update(*args)
        raise KeyboardInterrupt()

    monkeypatch.setattr(m, "update_records", interrupted)
    assert m.main([]) == 1
    result = capsys.readouterr()
    assert '"credentials_saved": "unknown"' in result.out
    assert '"stage": "save"' in result.out
    assert store.records["bot"]["app_secret"] == "fixture_new"
    assert "fixture_new" not in result.out + result.err
