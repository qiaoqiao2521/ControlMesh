# Progress

## Current

Implementation and local acceptance are complete for 0.44.0 on 2026-11-24. CM now has a directly executable, standard-library task path and a package that matches the retained product. The former platform source and active navigation have been retired.

The user authorized a direct `main` update. The corresponding GitHub commit and check results are the remote delivery record; this change does not create a release tag, upload to PyPI or deploy a service.

## Completed

- Replaced the default `cm` / `controlmesh` entry with `run`, `workflow` and `closeout`; retained the standalone `cm-workflow` and `cm-closeout` aliases.
- Added one explicit execution, verification commands, artifact hashes, private logs/report, shared time budget and advisory next action. No automatic retry, model request, daemon or new database is introduced.
- Removed the former Python / TypeScript runtime, dashboard, schemas, Paperclip / Orca integrations, root Node workspace, obsolete tests and platform documentation. The tracked source file count falls from 2,030 to 97; Git history remains available at `851d78b8989d07281d0082a5105f878a99f589c8`.
- Preserved independent SpecMesh handoff, Markdown closeout, CLI guidance and quota checks, the OpenCode adapter, optional Codex callback and optional DSH companion memory. Callback and adapter regressions moved out of the retired Paperclip test directory.
- Reduced production Python dependencies to zero. The built wheel contains only the five retained `controlmesh` modules; vendor callback and DSH remain optional source components.
- Replaced the obsolete platform CI with retained-product checks, including Python 3.11 / 3.12, an independent pinned SpecMesh checkout, a clean installed-wheel task check and the independent DSH store tests.
- Rewrote current entry documentation and retained selected independent capability history with fixed baseline links. Old source was not copied into an archive directory.

## Validation

All of the following were run against this change, not inherited from historical results.

| Check | Observed result |
| --- | --- |
| Retained Python tests plus callback upstream DeliveryTests | 111 passed, 20 subtests passed; no skips |
| Execution tests under `python3 -B -S` | 28 passed without site packages |
| Workflow tests under `python3 -B -S` with independent SpecMesh | 10 passed, including 4 real upstream contract cases |
| Independent SpecMesh version | `1e19bdf8093b57326cbadfa7cd9026b033c000ba` |
| DSH companion store, `node --test` | 12 passed; no SDK or model calls |
| Ruff across retained source | Passed |
| Build from source distribution | Wheel and source archive built successfully |
| Fresh-venv wheel install with `--no-index --no-deps` | Passed; 0 production dependencies, 4 actual installed commands |
| Installed wheel: correct worker plus explicit verification | `completed`, exit 0 |
| Installed wheel: exit-zero worker with incorrect artifact | `needs_repair`, exit 1 |
| Verified implementation wheel size | 19,511 bytes; subsequent documentation-only corrections do not change runtime code |
| Current Markdown links | 43 files scanned, 0 missing local file targets |
| GitHub workflow syntax and expressions | actionlint 1.7.12 passed; downloaded binary checksum verified |
| Workflow security check at the CI threshold | zizmor offline, medium severity / medium confidence: no findings |
| Diff whitespace validation | Passed |

The integrated Python command was:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=vendor/codex_callback/runtime CM_SPECMESH_TEST_ROOT=/absolute/path/to/pinned-specmesh uv run --frozen pytest -q tests vendor/codex_callback/tests/test_callback.py::DeliveryTests
```

## Independent review

Read-only review exercised argument forwarding, previous-report identity matching, clean-wheel installation and actual result verification. It found and reproduced a detached child with an empty environment that could overwrite an accepted artifact after the report.

The fix assigns each command a short-lived dedicated supervisor. Independent black-box replay confirmed that the artifact remains unchanged after the delayed-write window, unrelated children of the embedding host remain alive, and the host's subreaper and signal handlers are unchanged. A final TERM-handler fork regression also requires confirmed child exhaustion before success. Unexpected supervisor failure remains an explicit cleanup diagnostic, never a successful report.

## Limits

- `cm run` currently requires Linux and Python 3.11 or newer. Other platforms reject execution before starting the selected command.
- Verification covers only the caller's declared checks and artifacts. The task file records identity and does not automatically provide a CLI prompt; artifact declarations are not an operating-system sandbox.
- Previous-report comparison covers recorded outcomes and artifact summaries, not complete logs or verification-source semantics. It gives advice and never reruns a paid command itself.
- Callback queue tests do not prove that the user's current Codex thread/socket is reachable. DSH store tests do not prove its SDK or real-model integration. No live external CLI authentication, quota, model, server, deployment or production data was exercised.
- This is a source delivery. Install from the current checkout for this entry; an older PyPI package does not contain it.

## Remote delivery verification

The implementation was published directly to `main` as [41be4ed](https://github.com/qiaoqiao2521/ControlMesh/commit/41be4edfb1063be852335eddb066021d112d15cc), using a non-forced expected-parent update. Its remote tree exactly matched the locally verified index, and a fresh Git fetch confirmed the same commit with a clean worktree.

At read-back, GitHub showed successful Dependabot checks for that commit, but no `CI` or `Workflow checks` run. The public workflow listing described the workflows as active; the browser's workflow page returned 404 and the repository page had no Actions navigation. The cause was not established, and repository-level settings were not changed. Local verification above is complete; remote product CI is not claimed as passed.

The documentation example uses `--task task.md` relative to `--cwd`, matching the enforced requirement that the task file remain inside the selected project.
