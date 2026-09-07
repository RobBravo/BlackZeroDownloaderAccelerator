# Task 3 Fix Round 1

Read `blackzero/downloader.py` and `tests/test_downloader.py`.

Fix only these high-severity findings:

- When resuming, accept HTTP 206 only if `Content-Range` starts exactly at the requested local offset; otherwise restart safely from byte zero and do not append mismatched data.
- Never replace an existing final destination before checksum verification. Verify the completed temporary file first; on mismatch delete only the temporary file and preserve the old destination, including when overwrite is enabled.

Add regression tests first, run them failing, implement the minimum correction, run focused and full suites, commit, and write the report to:
`C:\Users\ingmo\OneDrive\Documentos\GitHub\BlackZeroDownloaderAccelerator\.worktrees\blackzero-cli-improvements\.superpowers\sdd\2026-09-03-blackzero-cli-improvements\task-3-fix-report.md`
Modify only `blackzero/downloader.py` and `tests/test_downloader.py`.
