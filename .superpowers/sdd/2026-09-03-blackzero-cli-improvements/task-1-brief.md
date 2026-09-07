### Task 1: Establish package and typed contracts

**Files:**
- Create: `blackzero/__init__.py`
- Create: `blackzero/models.py`
- Create: `blackzero/errors.py`
- Create: `tests/test_models.py`

**Interfaces:**
- `DownloadOptions(output_dir: Path, filename: str | None, overwrite: bool, resume: bool, retries: int, timeout: float, checksum: str | None, quiet: bool, keep_partial: bool)`.
- `DownloadResult(url: str, path: Path, bytes_written: int, resumed: bool, checksum_verified: bool)`.
- `DownloadError` with `message`, `kind`, and optional `cause`.

**Requirements:**
- Write tests first and run them failing before production implementation.
- Test model construction, default option values, and error fields.
- Implement dataclasses and typed errors with validation for positive timeout/retries and normalized paths.
- Run `pytest tests/test_models.py -q` and report the output.
- Do not modify files outside the listed scope.
