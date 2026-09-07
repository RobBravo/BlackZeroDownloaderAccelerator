### Task 3: Build the reliable HTTP transfer engine

**Files:** Create `blackzero/downloader.py` and `tests/test_downloader.py` only.

**Interfaces:**
- `download(url: str, options: DownloadOptions, progress: Callable[[int, int | None], None] | None = None) -> DownloadResult`.
- `parse_checksum(value: str | None) -> tuple[str, str] | None`.
- Consume `blackzero.files.finalize_part(part, destination, overwrite)` and the Task 1 models/errors.

Write tests first and watch them fail. Use a local HTTP server fixture with no external network. Cover streamed writes, known/unknown content length, timeout propagation, response closure, retries on 503/429/408, no retries on permanent 4xx, `.part` cleanup, `Range`/206 resume, fallback to fresh download on 200, `--keep-partial`, SHA-256 success, and mismatch deletion. Implement `requests.Session`, `timeout=(timeout, timeout)`, response context management, 64 KiB chunks, bounded exponential backoff, numeric `Retry-After`, incremental hashing, and `finally` cleanup. Run `pytest tests/test_downloader.py -q` and `pytest -q`. Commit and write the full report to `C:\Users\ingmo\OneDrive\Documentos\GitHub\BlackZeroDownloaderAccelerator\.worktrees\blackzero-cli-improvements\.superpowers\sdd\2026-09-03-blackzero-cli-improvements\task-3-report.md`. Do not modify other files or delegate.
