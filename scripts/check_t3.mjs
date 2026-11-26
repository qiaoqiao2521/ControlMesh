// Exercise the pinned application without requesting a model turn.
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { once } from "node:events";
import { chmod, mkdir, mkdtemp, readFile, rm } from "node:fs/promises";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const readJson = async (file) => JSON.parse(await readFile(path.join(root, file), "utf8"));
const project = await readJson("package.json");
const lock = await readJson("package-lock.json");
const source = await readJson("t3-upstream.json");
const installed = await readJson("node_modules/t3/package.json");
assert.equal(project.dependencies.t3, source.version);
assert.equal(lock.packages["node_modules/t3"].version, source.version);
assert.equal(installed.version, source.version);
assert.match(source.commit, /^[0-9a-f]{40}$/);

// Reuse only the runtime cache; the server receives a fresh T3 base directory.
const cache = process.env.CM_T3_TEST_CACHE || path.join(os.tmpdir(), "controlmesh-t3-test-cache");
await mkdir(cache, { recursive: true, mode: 0o700 });
await chmod(cache, 0o700);
// Upstream opt-outs keep smoke tests from exporting analytics or OTLP data.
const environment = {
  ...process.env, T3CODE_HOME: cache, T3CODE_TELEMETRY_ENABLED: "false",
  DO_NOT_TRACK: "1", T3CODE_OTEL_SDK_DISABLED: "true", OTEL_SDK_DISABLED: "true",
};
const launcher = path.join(root, "node_modules/t3/bin/t3.mjs");
function invoke(args) {
  const result = spawnSync(process.execPath, [launcher, ...args], {
    cwd: root, env: environment, encoding: "utf8", timeout: 60_000,
    stdio: ["ignore", "pipe", "pipe"], maxBuffer: 1024 * 1024,
  });
  if (result.error) throw result.error;
  const diagnostic = result.stderr.replace(/https?:\/\/\S+/g, "<url>").slice(-1500);
  assert.equal(result.status, 0, `T3 ${args[0]} exited ${result.status}: ${diagnostic}`);
  return result.stdout.trim();
}

const version = invoke(["--version"]);
assert.ok(version.includes(source.version), "Native runtime version differs from the pinned launcher");
const help = invoke(["thread", "--help"]);
for (const command of ["start", "send", "show", "list"]) assert.ok(help.includes(command));

const temporary = await mkdtemp(path.join(os.tmpdir(), "cm-t3-server-"));
const reservation = net.createServer();
reservation.listen(0, "127.0.0.1");
await once(reservation, "listening");
const port = reservation.address().port;
await new Promise((resolve) => reservation.close(resolve));
const server = spawn(process.execPath, [
  launcher, "--base-dir", temporary, "--host", "127.0.0.1",
  "--port", String(port), "--no-browser", "--auto-bootstrap-project-from-cwd",
], {
  cwd: temporary, env: environment,
  stdio: ["ignore", "ignore", "ignore"], detached: process.platform !== "win32",
});
let spawnError;
server.on("error", (error) => { spawnError = error; });
try {
  const address = `http://127.0.0.1:${port}`;
  let html;
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (spawnError) throw spawnError;
    assert.equal(server.exitCode, null, "T3 server exited before becoming ready");
    try {
      const response = await fetch(address, { signal: AbortSignal.timeout(1000) });
      if (response.ok) {
        html = await response.text();
        if (html.includes("<html")) break;
      }
    } catch { /* Startup may not have bound the port yet. */ }
    await delay(200);
  }
  assert.ok(html?.includes("<html"), "T3 did not serve its Web application within 30 seconds");
  const script = html.match(/<script[^>]+src="([^"]+)"/);
  assert.ok(script, "T3 Web response has no application script");
  const assetUrl = new URL(script[1], address);
  assert.equal(assetUrl.origin, address, "Unexpected external application script");
  const asset = await fetch(assetUrl, { signal: AbortSignal.timeout(5000) });
  assert.equal(asset.status, 200, "T3 Web application bundle is missing");
  assert.ok((await asset.text()).length > 0);
  const threads = JSON.parse(invoke(["thread", "list", "--project", temporary, "--base-dir", temporary, "--json"]));
  assert.ok(Array.isArray(threads), "Thread RPC did not return its documented array");
  // First-run project bootstrap may create one empty draft, without a model turn.
  assert.ok(threads.length <= 1, "Unexpected threads in a freshly bootstrapped environment");
  for (const thread of threads) {
    const detail = JSON.parse(invoke(["thread", "show", thread.threadId, "--base-dir", temporary, "--json"]));
    assert.equal(detail.error, null);
    assert.deepEqual(detail.messages, []);
    assert.equal(detail.thread.latestRunId, null);
    assert.equal(detail.thread.activeRunId, null);
  }
  console.log(JSON.stringify({
    version: source.version, upstream_commit: source.commit,
    checks: ["locked package", "native version", "thread CLI", "HTTP Web app", "application bundle", "thread read RPC"],
    model_turns_requested: 0, isolated_t3_base_dir: true, telemetry_disabled_by_env: true,
  }, null, 2));
} finally {
  if (server.pid && server.exitCode === null) {
    const exited = once(server, "exit").catch(() => undefined);
    server.kill("SIGTERM");
    await Promise.race([exited, delay(8000)]);
    if (server.exitCode === null && server.signalCode === null) {
      try {
        if (process.platform !== "win32") process.kill(-server.pid, "SIGKILL");
        else server.kill("SIGKILL");
      } catch (error) { if (error.code !== "ESRCH") throw error; }
      await exited;
    }
  }
  await rm(temporary, { recursive: true, force: true });
}
