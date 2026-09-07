# SDD ledger — plan: docs/superpowers/plans/2026-09-03-blackzero-cli-improvements.md

## Pre-flight scan

| Scope | Finding | Ruling |
|---|---|---|
| Task 1 ↔ Task 2 | Task 1 defines models/errors; Task 2 consumes them only conceptually and owns file helpers. No shared file conflict. | Proceed in order. |
| Task 2 ↔ Task 3 | Task 3 consumes destination/part/finalization helpers from Task 2. Signatures match. | Task 3 waits for Task 2. |
| Task 3 ↔ Task 4 | Task 4 consumes `download`, `DownloadOptions`, `DownloadResult`, and `DownloadError`. Signatures match. | Task 4 waits for Task 3. |
| Task 4 ↔ Task 5 | Task 5 delegates to `main`; Task 4 owns its implementation. No conflicting implementation requirement. | Preserve the existing launcher as a thin adapter. |
| Task 5 ↔ Task 6 | Task 6 documents the packaging and commands produced by Task 5. | Task 6 waits for Task 5. |
| Task 6 ↔ Task 7 | Task 7 may correct README only if smoke validation finds an actual mismatch. | Keep corrections narrow. |
| Task 1 | Tests and files align with the typed contract. | Proceed. |
| Task 2 | Tests cover the listed path and filename behaviors; files are self-contained. | Proceed. |
| Task 3 | Local-server tests cover the transfer behaviors listed; downloader consumes Task 1/2 interfaces. | Proceed. |
| Task 4 | Parser/execution tests cover the listed CLI contract; CLI consumes Task 3. | Proceed. |
| Task 5 | Compatibility tests cover both launcher forms; packaging owns the entry point. | Proceed. |
| Task 6 | README, requirements, and changelog changes are documentation-only and match the spec. | Proceed. |
| Task 7 | Quality gates cover tests, syntax, lint, smoke behavior, and generated files. | Proceed. |

## Rulings

- Ruling: keep the existing `gitignore` file content while adding a correctly named `.gitignore` for worktree and generated-file rules — why: Git only honors `.gitignore`, and the requested isolation requires the worktree path to be ignored — cost if wrong: one additional tracked ignore file.
- Ruling: execute tasks sequentially because each task's public interfaces feed the next task — why: parallel edits would create contract conflicts — cost if wrong: less parallel speed, but lower integration risk.

## Status

- Worktree: `feature/blackzero-cli-improvements`
- Base: `352d5c5`
- Task 1: complete — commit ec75b7e; review approved with no findings.
- Task 2: fix round 1 — review found A-1 high (finalize_part overwrites without authorization) and M-1 medium (incomplete RFC 5987 filename* parsing).
- Ruling: fix both findings before Task 2 can complete — why: A-1 violates the global no-overwrite safety contract and M-1 is a concrete standards-compliance gap — cost if wrong: a small API/test adjustment now instead of data loss or incorrect names later.
- Task 2: complete — commits f5c8582, cc54907; correction review approved with no findings.
- Task 3: fix round 1 — review found two high findings: unvalidated Content-Range offset and checksum failure deleting the previous destination under overwrite.
- Ruling: validate Range responses before appending and verify checksum before replacing an existing final file — why: both findings can corrupt or destroy user data — cost if wrong: additional temporary/verification logic.
- Task 3: complete — commits 72b87f8, c828851; correction review approved with no findings.
- Task 4: complete — commit 9986314; parser, output, and exit-code tests pass.
- Task 5: complete — commit 1f5f0d4; launcher compatibility, packaging metadata, and `python -m blackzero` entry point are present.
- Task 6: complete — commit 15edd32; README, requirements, changelog, and compatibility limitations documented.
- Task 7: complete — 47 tests pass, compileall passes, diff check passes, and local CLI smoke checks return 0/1/2 as specified. `ruff` was not available in the environment and was not executed.
