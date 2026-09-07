# Task 2 Fix Round 1

Read the existing `blackzero/files.py` and `tests/test_files.py` in the isolated worktree.

Fix the two review findings:

1. `finalize_part` must never replace an existing destination unless overwrite authorization is explicit. Preserve the existing destination and raise a clear filesystem error when overwrite is false. Keep an atomic publication path; the downloader will pass overwrite explicitly in a later task.
2. Parse valid RFC 5987 `filename*` values of the form `charset'language'encoded-payload`, including a non-empty language such as `UTF-8'en'caf%C3%A9.txt`; decode bytes using the declared charset and fall back safely for invalid values.

Follow TDD: add regression tests first, run them failing, implement the minimum correction, run the focused and full suites. Keep changes limited to `blackzero/files.py` and `tests/test_files.py`. Commit with a fix message and write the full report to:

`C:\Users\ingmo\OneDrive\Documentos\GitHub\BlackZeroDownloaderAccelerator\.worktrees\blackzero-cli-improvements\.superpowers\sdd\2026-09-03-blackzero-cli-improvements\task-2-fix-report.md`
