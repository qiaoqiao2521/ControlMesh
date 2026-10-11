# Codex Callback upstream and local patch

Source: [LawrentChen/codex_callback](https://github.com/LawrentChen/codex_callback).
Pinned commit: [`5193e2ece5caf2ac1805800575e5567a972f657c`](https://github.com/LawrentChen/codex_callback/commit/5193e2ece5caf2ac1805800575e5567a972f657c).
License: [MIT](LICENSE), including the upstream copyright notice.
Remote source and the local acceptance reference matched on 2026-10-11.

`runtime/` comes from upstream `skills/codex-callback/scripts/runtime/`.
`tests/test_callback.py` is the unchanged upstream test file.
No Python environment, global skill, daemon, or service is installed by this copy.

## Patch scope

Only `runtime/codex_callback/delivery.py` differs from upstream.
The desktop can consume a submission between `queue/list` and `queue/start`.
Its turn may finish before the callback worker reads the thread status again.
Upstream then raises `RpcError` because the thread has already returned to `idle`.

After a `queue/start` error, the patch rereads the original submission's queue entry.
If that entry has disappeared, existing history reconciliation checks the same event and thread.
A matching receipt records `started` with `receipt_source=history`.
A missing receipt remains `UncertainDelivery`; it never adds another submission.
If the queue entry remains, existing active-thread waiting and error propagation are preserved.

The patch does not change event IDs, `notify()`, transport, worker startup, or native task configuration.
CM completion handling and origin-thread binding belong to the external adapter.

## Source hashes

These SHA256 values describe the imported upstream files before the patch.
The original nine-file acceptance manifest remains unchanged.
Its SHA256 is `ced20a085f76bccc774f091d18a57ae152139a32e0e128a02b5f7ff0712328f8`.

| File in this directory | Upstream SHA256 |
| --- | --- |
| `LICENSE` | `32bbfd8dfb071d1d618f344c3f5ed4d5cb2761db6e39c03c6fc3e145c11973dd` |
| `runtime/live_test.py` | `2312815dff1ea5f2978fce010176e654e7c26ad55381af9409c60f4dfe5154d8` |
| `runtime/check_connection.py` | `a2d5900af828eaec9c90a686546307abfc1a0d7fec4b132974c98341e18018e2` |
| `runtime/codex_callback/delivery.py` | `78342d14c45ad1c144e84ba43392a7244aa8fff47be74bfcdf233d7ebf7e5c0d` |
| `runtime/codex_callback/transport.py` | `679ebbb72511950fc5598bf057a7c33329840866fe9e96764c7ed4e5b1f759d4` |
| `runtime/codex_callback/jobs.py` | `a9b6b458a1d581c05e831e2ec6a4ac3efafbce7b1034c8eefb17f7844a7a7743` |
| `runtime/codex_callback/__init__.py` | `122cd7ce36c49e93b0e1401c612d700f3774dc846c8d1b68cf153af5237ef53e` |
| `runtime/codex_callback/client.py` | `fb1b115771a1c06e2ee408a44767351ac27052cafe48bb2e9ac951b2ae7a1f2e` |
| `runtime/codex_callback/worker.py` | `e311875fec17dba6a4a9b42c295f1b3cda74ea0d989b1a93c3298315c1044517` |
| `tests/test_callback.py` | `e5f7c91ba0ff73094c4d23d09693849c87116d357c5666628b689c2d8f8b3427` |

Patched `runtime/codex_callback/delivery.py` SHA256:
`4334bd5e4b4ebcb17e7a8619035d0c7718d8695623e2b95fcd05632047457636`.

Local [race tests](../../tests/paperclip_adapters/test_codex_callback_delivery.py) SHA256:
`62172b782bc8e8faeb77e13cece6534e289c593c2728b90bcff4d2a371e239dc`.

## Verification

Run from the repository root:

```sh
env PYTHONPATH="$PWD/vendor/codex_callback/runtime:$PWD/vendor/codex_callback/tests:$PWD/tests/paperclip_adapters" \
  python3 -B -S -m unittest test_callback.DeliveryTests test_codex_callback_delivery.DeliveryRaceTests -v
```

Before the patch, the five new tests produced one failure, three errors, and one pass.
After the patch, nine upstream delivery tests and five local race tests passed.
The local tests use a fake queue peer and temporary receipt files.
Upstream delivery tests mock worker spawning.

This check excludes upstream `ProcessTests`, transport/worker integration, and live callback tests.
It starts no callback worker and connects to no Codex or Paperclip service.
