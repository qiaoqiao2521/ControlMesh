"""Exercise the small runtime gate through transport and filesystem boundaries."""
import contextlib
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import pwd
import tempfile
import threading
from types import SimpleNamespace
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/paperclip/cm-feishu-runtime"
loader = importlib.machinery.SourceFileLoader("feishu_runtime_gate", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
gate = importlib.util.module_from_spec(spec)
loader.exec_module(gate)
COMPANY, PLUGIN = "company-1", "plugin-1"
VERSION = "0.3.11-connector-feishu.cm-compat.9"


class Host:
    def __init__(self, package):
        self.package, self.deadline, self.calls = str(package), None, []
        self.config = {"enableEventSubscriber": True,
                       "routes": [{"companyId": COMPANY}],
                       "nativeConversation": {"bindings": [{"companyId": COMPANY}]},
                       "secret": "DO-NOT-OUTPUT"}
        self.stored = True
        self.value = self.healthy()
        self.plugin_key, self.version = gate.KEY, VERSION
        self.live, self.upgrades, self.change_after_upgrade = [], 0, False
        self.upgrade_error, self.change_on_read, self.reads = None, None, 0

    def healthy(self):
        now = datetime.now(timezone.utc).isoformat()
        return {"schema": "cm.feishu.runtime-health.v1", "companyId": COMPANY,
                "configApplied": True, "configHash": gate.fingerprint(self.config),
                "eventSubscriberEnabled": True, "expectedSubscribers": 1,
                "activeSubscribers": 1, "watchdogActive": True, "status": "healthy",
                "lastWatchdogAt": now, "lastConfigAppliedAt": now}

    def __call__(self, method, path, body=None, upgrade=False):
        self.calls.append((method, path, body, upgrade))
        if path == "/health":
            return {"status": "ok", "deploymentMode": "local_trusted"}
        if path == "/plugins/" + PLUGIN:
            return {"id": PLUGIN, "pluginKey": self.plugin_key, "status": "ready",
                    "version": self.version, "packagePath": self.package}
        if "/config?" in path:
            self.reads += 1
            if self.change_on_read == self.reads:
                self.config["newSetting"] = True
            return {"pluginId": PLUGIN, "companyId": COMPANY,
                    "configJson": deepcopy(self.config)} if self.stored else None
        if "/live-runs?" in path:
            return deepcopy(self.live)
        if path.endswith("/bridge/data"):
            assert body == {"companyId": COMPANY, "key": "runtime-health", "params": {}}
            return {"data": deepcopy(self.value)}
        if path.endswith("/upgrade"):
            assert method == "POST" and body == {} and upgrade is True
            self.upgrades += 1
            if self.upgrade_error:
                raise self.upgrade_error
            self.version, self.value = VERSION, self.healthy()
            if self.change_after_upgrade:
                self.config["newSetting"] = True
            return {"status": "ready"}
        raise AssertionError("Unapproved API operation")


class RuntimeGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.package = Path(self.temporary.name) / "plugin"
        self.package.mkdir()
        (self.package / "dist").mkdir()
        self.package.chmod(0o755)
        (self.package / "dist").chmod(0o755)
        (self.package / "package.json").write_text(json.dumps({"version": VERSION}))
        (self.package / "dist/native-runtime.mjs").write_text("// candidate\n")
        self.sidecar = self.package / "dist/cm-company-binding.json"
        self.host = Host(self.package)

    def args(self, action="check"):
        return SimpleNamespace(action=action, api_base="http://127.0.0.1:3100",
                               plugin_id=PLUGIN, company_id=COMPANY, package_dir=None)

    def rejection(self, reason, action="check", code=1):
        with self.assertRaises(gate.Rejected) as caught:
            gate.run(self.args(action), self.host)
        self.assertEqual((caught.exception.reason, caught.exception.code), (reason, code))

    def install_binding(self, company=COMPANY):
        self.sidecar.write_text(json.dumps({"schema": gate.SCHEMA,
                                           "pluginKey": gate.KEY, "companyId": company}))
        self.sidecar.chmod(0o644)

    def test_check_has_no_writes_or_secret_output(self):
        before = {str(p): p.read_bytes() for p in self.package.rglob("*") if p.is_file()}
        value = gate.run(self.args(), self.host)
        self.assertEqual(value["state"], "healthy")
        self.assertFalse(value["deliveryVerified"])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.package.rglob("*") if p.is_file()})
        self.assertEqual([c[1] for c in self.host.calls if c[0] == "POST"],
                         ["/plugins/" + PLUGIN + "/bridge/data"])
        self.assertNotIn("DO-NOT-OUTPUT", json.dumps(value))
        self.assertFalse(self.sidecar.exists())

    def test_false_ready_and_unapplied_are_not_success(self):
        for patch, reason in [({"configApplied": False}, "config_not_applied"),
                              ({"activeSubscribers": 0}, "runtime_degraded"),
                              ({"watchdogActive": False}, "runtime_degraded"),
                              ({"companyId": "foreign"}, "config_not_applied")]:
            with self.subTest(patch=patch):
                self.host.value = {**self.host.healthy(), **patch}
                self.rejection(reason)

    def test_hash_mismatch_and_missing_schema_rejected(self):
        self.host.value["configHash"] = "stale"
        self.rejection("runtime_config_hash_mismatch")
        self.host.value = self.host.healthy()
        del self.host.value["activeSubscribers"]
        self.rejection("runtime_schema_invalid")

    def test_startup_window_allows_no_tick_only_for_sixty_seconds(self):
        self.host.value["lastWatchdogAt"] = None
        self.assertEqual(gate.run(self.args(), self.host)["state"], "healthy")
        self.host.value["lastConfigAppliedAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=61)).isoformat()
        self.rejection("watchdog_stale")

    def test_stalled_or_invalid_watchdog_is_not_ready(self):
        self.host.value["lastWatchdogAt"] = (
            datetime.now(timezone.utc) - timedelta(seconds=91)).isoformat()
        self.rejection("watchdog_stale")
        self.host.value["lastWatchdogAt"] = "invalid-secret-no-output"
        self.rejection("runtime_clock_invalid")

    def test_null_and_empty_config_are_unconfigured(self):
        self.host.stored = False
        self.rejection("unconfigured", code=3)
        self.host.stored, self.host.config = True, {}
        self.rejection("unconfigured", "sync", 3)
        self.assertFalse(self.sidecar.exists())

    def test_disabled_has_explicit_non_success_state(self):
        self.host.config["enableEventSubscriber"] = False
        self.host.value = {**self.host.healthy(), "status": "disabled",
                           "eventSubscriberEnabled": False,
                           "expectedSubscribers": 0, "activeSubscribers": 0}
        self.rejection("disabled")

    def test_foreign_route_and_binding_rejected(self):
        for field in ("routes", "nativeConversation"):
            with self.subTest(field=field):
                self.host = Host(self.package)
                entry = self.host.config[field] if field == "routes" else self.host.config[field]["bindings"]
                entry[0]["companyId"] = "foreign"
                self.rejection("foreign_company_config", "sync")
                self.assertFalse(self.sidecar.exists())

    def test_native_binding_cannot_implicitly_pick_a_company(self):
        del self.host.config["nativeConversation"]["bindings"][0]["companyId"]
        self.rejection("foreign_company_config", "sync")
        self.assertFalse(self.sidecar.exists())

    def test_healthy_listener_cannot_hide_missing_enabled_route_target(self):
        for match_type, field in (("chat", "chatId"), ("user", "userId")):
            for missing in (None, "", "  ", 123):
                with self.subTest(match_type=match_type, missing=missing):
                    self.host.config["routes"] = [{"companyId": COMPANY,
                        "matchType": match_type, field: missing}]
                    self.host.value = self.host.healthy()
                    self.rejection("enabled_route_target_missing")
                    self.assertFalse(self.sidecar.exists())

    def test_disabled_incomplete_route_draft_is_retained(self):
        self.host.config["routes"] = [{"companyId": COMPANY, "matchType": "chat",
                                      "enabled": False}]
        original = deepcopy(self.host.config)
        self.host.value = self.host.healthy()
        self.assertEqual(gate.run(self.args(), self.host)["state"], "healthy")
        self.assertEqual(self.host.config, original)

    def test_sync_writes_only_public_sidecar_then_one_native_upgrade(self):
        before = (self.package / "package.json").read_bytes()
        self.host.version = VERSION.replace(".9", ".8")
        self.host.value = {"status": "unbound", "companyId": None}
        value = gate.run(self.args("sync"), self.host)
        self.assertTrue(value["changed"])
        self.assertEqual(self.host.upgrades, 1)
        self.assertEqual(json.loads(self.sidecar.read_text()),
                         {"schema": gate.SCHEMA, "pluginKey": gate.KEY, "companyId": COMPANY})
        self.assertEqual(before, (self.package / "package.json").read_bytes())
        self.assertEqual(self.sidecar.stat().st_mode & 0o777, 0o644)
        self.assertNotIn("DO-NOT-OUTPUT", self.sidecar.read_text())
        self.assertTrue(all(c[1].endswith(("/bridge/data", "/upgrade"))
                            for c in self.host.calls if c[0] == "POST"))
        self.assertFalse(any("/config" in c[1] for c in self.host.calls if c[0] == "POST"))

    def test_healthy_binding_and_matching_version_are_noop_even_during_work(self):
        self.install_binding()
        self.host.live = [{"id": "running"}]
        before = self.sidecar.stat().st_mtime_ns
        value = gate.run(self.args("sync"), self.host)
        self.assertFalse(value["changed"])
        self.assertEqual(self.host.upgrades, 0)
        self.assertEqual(before, self.sidecar.stat().st_mtime_ns)

    def test_live_work_prevents_sidecar_and_reload(self):
        self.host.live = [{"id": "running"}]
        self.rejection("live_work_present", "sync")
        self.assertFalse(self.sidecar.exists())
        self.assertEqual(self.host.upgrades, 0)

    def test_foreign_sidecar_and_runtime_are_not_overwritten(self):
        self.install_binding("foreign")
        original = self.sidecar.read_bytes()
        self.rejection("foreign_or_invalid_binding", "sync")
        self.assertEqual(original, self.sidecar.read_bytes())
        self.assertEqual(self.host.upgrades, 0)
        self.sidecar.unlink()
        self.host.value["companyId"] = "foreign"
        self.rejection("foreign_runtime_company", "sync")
        self.assertFalse(self.sidecar.exists())

    def test_config_changes_before_any_write_abort(self):
        self.host.change_on_read = 2
        self.rejection("config_changed", "sync")
        self.assertFalse(self.sidecar.exists())
        self.assertEqual(self.host.upgrades, 0)

    def test_config_changes_after_upgrade_abort_without_second_upgrade(self):
        self.host.change_after_upgrade = True
        self.rejection("config_changed", "sync")
        self.assertEqual(self.host.upgrades, 1)

    def test_unknown_upgrade_is_not_retried(self):
        self.host.upgrade_error = gate.Rejected("upgrade_outcome_unknown", 4)
        self.rejection("upgrade_outcome_unknown", "sync", 4)
        self.assertEqual(self.host.upgrades, 1)
        self.assertTrue(self.sidecar.exists())

    def test_sidecar_symlink_fifo_oversize_and_permissions_fail_closed(self):
        self.sidecar.symlink_to(self.package / "package.json")
        with self.assertRaises(OSError):
            gate.run(self.args("sync"), self.host)
        self.sidecar.unlink()
        os.mkfifo(self.sidecar)
        self.rejection("unsafe_binding_file", "sync")
        self.sidecar.unlink()
        self.sidecar.write_bytes(b" " * 4097)
        self.rejection("unsafe_binding_file", "sync")
        self.sidecar.unlink()
        self.install_binding()
        self.sidecar.chmod(0o666)
        self.rejection("unsafe_binding_file", "sync")
        self.assertEqual(self.host.upgrades, 0)

    def test_package_argument_mismatch_is_readonly_rejected(self):
        args = self.args("sync")
        args.package_dir = "/other/plugin"
        with self.assertRaises(gate.Rejected) as caught:
            gate.run(args, self.host)
        self.assertEqual(caught.exception.reason, "package_path_mismatch")
        self.assertFalse(self.sidecar.exists())

    def test_real_primary_group_775_directories_are_allowed_without_chmod(self):
        primary_gid = pwd.getpwuid(os.geteuid()).pw_gid
        for path in (self.package, self.package / "dist"):
            os.chown(path, -1, primary_gid)
            path.chmod(0o775)
        before = {p: p.stat().st_mode for p in (self.package, self.package / "dist")}
        value = gate.run(self.args("sync"), self.host)
        self.assertEqual(value["state"], "healthy")
        self.assertEqual(before, {p: p.stat().st_mode for p in before})
        self.assertEqual(self.sidecar.stat().st_mode & 0o777, 0o644)
        self.sidecar.chmod(0o664)
        self.rejection("unsafe_binding_file", "sync")

    def test_world_writable_application_directory_is_still_rejected(self):
        self.package.chmod(0o777)
        self.rejection("writable_package_path", "sync")
        self.assertFalse(self.sidecar.exists())
        self.assertEqual(self.host.upgrades, 0)

    def test_old_package_and_symlink_package_are_rejected(self):
        (self.package / "package.json").write_text(json.dumps({"version": VERSION.replace(".9", ".8")}))
        self.rejection("compat9_package_required", "sync")
        (self.package / "package.json").unlink()
        (self.package / "package.json").symlink_to(self.package / "dist/native-runtime.mjs")
        with self.assertRaises(OSError):
            gate.run(self.args("sync"), self.host)
        self.assertFalse(self.sidecar.exists())


class TransportBoundaryTests(unittest.TestCase):
    def test_nonloopback_authenticated_url_and_redirect_are_refused(self):
        for url in ("https://127.0.0.1", "http://10.0.0.1", "http://u:p@127.0.0.1",
                    "http://127.0.0.1/api", "http://127.0.0.1?token=secret"):
            with self.subTest(url=url), self.assertRaises(gate.Rejected):
                gate.API(url)
        with self.assertRaises(gate.Rejected):
            gate.NoRedirect().redirect_request(None, None, 302, "", {}, "http://other")

    def test_bounded_json_duplicate_keys_nan_and_number_fingerprints(self):
        for raw in (b" " * (gate.LIMIT + 1), b'{"a":1,"a":2}', b'{"a":NaN}'):
            with self.subTest(size=len(raw)), self.assertRaises(gate.Rejected):
                gate.parse(raw)
        fixture = gate.parse(b'{"a":1e-7,"b":0.000001,"c":-0.0,"d":0.3,"e":1e21}')
        expected = '{"a":1e-7,"b":0.000001,"c":0,"d":0.3,"e":1e+21}'
        self.assertEqual(gate.canonical(fixture), expected)
        self.assertEqual(gate.fingerprint(fixture), hashlib.sha256(expected.encode()).hexdigest())
        self.assertEqual(gate.canonical({"\ue000": 1, "😀": 2}), '{"😀":2,"\ue000":1}')
        self.assertEqual(gate.canonical({"x": Decimal("-1.2300e-8")}), '{"x":-1.23e-8}')

    def test_actual_http_error_body_is_private_and_upgrade_unknown(self):
        class Handler(BaseHTTPRequestHandler):
            calls = 0
            def do_POST(self):
                type(self).calls += 1
                self.send_response(502)
                self.end_headers()
                self.wfile.write(b'{"error":"secret-token-no-log"}')
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            api = gate.API("http://127.0.0.1:" + str(server.server_port))
            with self.assertRaises(gate.Rejected) as caught:
                api("POST", "/plugins/p/upgrade", {}, upgrade=True)
            self.assertEqual((caught.exception.reason, caught.exception.code),
                             ("upgrade_outcome_unknown", 4))
            self.assertNotIn("secret-token", str(caught.exception))
            self.assertEqual(Handler.calls, 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_parser_error_prints_fixed_json_without_raw_arguments(self):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            with self.assertRaises(SystemExit) as caught:
                gate.main(["secret-bad-action"])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(json.loads(output.getvalue())["state"], "invalid_arguments")
        self.assertEqual(errors.getvalue(), "")
        self.assertNotIn("secret-bad-action", output.getvalue())


if __name__ == "__main__":
    unittest.main()
