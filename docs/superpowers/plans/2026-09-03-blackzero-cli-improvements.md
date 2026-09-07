# BlackZero CLI Improvements Implementation Plan

> Estado: completado. Todas las tareas del plan fueron implementadas y validadas en `main`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert BlackZero into a reliable, scriptable HTTP/HTTPS terminal downloader while preserving the current interactive command.

**Architecture:** Keep `DownloadFiles.py` as a compatibility launcher and introduce a focused `blackzero` package. The CLI parses options and renders output; the downloader performs transfers; file utilities own names, paths, temporary files, and finalization; typed models/errors connect the layers.

**Tech Stack:** Python 3.10+, `requests`, `tqdm`, `pytest`, `pyproject.toml`.

**Spec:** `docs/superpowers/specs/2026-09-03-blackzero-cli-improvements-design.md`

## Global Constraints

- Support only HTTP and HTTPS URLs with a hostname.
- Preserve `python DownloadFiles.py` interactive behavior and accept `python DownloadFiles.py URL`.
- Default destination is the user's Downloads directory; create it when missing.
- Never overwrite existing files unless `--overwrite` is specified.
- Completed files are finalized atomically from a `.part` path.
- Default timeout is 30 seconds and default retries is 3.
- Exit `0` means success, `1` means download/checksum failure, and `2` means invalid CLI input.
- Tests must not require external network access.
- Do not add a GUI, persistent configuration, authentication profiles, or parallel transfers.

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

- [ ] **Step 1: Write failing tests** for model construction, default option values, and error fields.
- [ ] **Step 2: Run** `pytest tests/test_models.py -q`; confirm the new imports/contracts fail.
- [ ] **Step 3: Implement** the dataclasses and typed error classes with validation for positive timeout/retries and normalized paths.

```python
@dataclass(frozen=True)
class DownloadResult:
    url: str
    path: Path
    bytes_written: int
    resumed: bool
    checksum_verified: bool
```
- [ ] **Step 4: Run** `pytest tests/test_models.py -q`; expect all tests to pass.
- [ ] **Step 5: Commit** with `git add blackzero tests/test_models.py; git commit -m "refactor: define downloader contracts"`.

### Task 2: Implement safe filename and path handling

**Files:**
- Create: `blackzero/files.py`
- Create: `tests/test_files.py`

**Interfaces:**
- `default_download_dir() -> Path`.
- `sanitize_filename(candidate: str, fallback: str = "archivo_descargado") -> str`.
- `filename_from_response(url: str, headers: Mapping[str, str]) -> str`.
- `choose_destination(directory: Path, filename: str, overwrite: bool) -> Path`.
- `part_path(destination: Path) -> Path`.
- `finalize_part(part: Path, destination: Path, overwrite: bool = False) -> None`.

- [ ] **Step 1: Write failing tests** for URL fallback names, `Content-Disposition`, invalid Windows characters, reserved names, collisions, overwrite, and atomic rename.
- [ ] **Step 2: Run** `pytest tests/test_files.py -q`; confirm failures.
- [ ] **Step 3: Implement** sanitization with `pathlib`, `re`, and `urllib.parse`; reject path separators and ensure resolved output stays below the destination directory.
- [ ] **Step 4: Run** the focused tests and confirm pass.
- [ ] **Step 5: Commit** with `git add blackzero/files.py tests/test_files.py; git commit -m "feat: add safe download paths"`.

### Task 3: Build the reliable HTTP transfer engine

**Files:**
- Create: `blackzero/downloader.py`
- Create: `tests/test_downloader.py`

**Interfaces:**
- `download(url: str, options: DownloadOptions, progress: Callable[[int, int | None], None] | None = None) -> DownloadResult`.
- `parse_checksum(value: str | None) -> tuple[str, str] | None`.

- [ ] **Step 1: Write failing local-server tests** for streamed writes, unknown content length, timeout propagation, filesystem cleanup, and response closure.
- [ ] **Step 2: Add tests** for retries on 503/429/408 and no retries on permanent 4xx responses.
- [ ] **Step 3: Add tests** for `.part` creation, `Range`/206 resume, fallback to a fresh download when the server returns 200, and `--keep-partial` behavior.
- [ ] **Step 4: Add tests** for SHA-256 success and mismatch deletion.
- [ ] **Step 5: Run** `pytest tests/test_downloader.py -q`; confirm failures before implementation.
- [ ] **Step 6: Implement** a `requests.Session` transfer with `timeout=(timeout, timeout)`, response context management, 64 KiB chunks, bounded exponential backoff, `Retry-After` handling where numeric, incremental hashing, and cleanup in `finally`.

```python
with session.get(url, stream=True, headers=headers,
                 timeout=(options.timeout, options.timeout)) as response:
    response.raise_for_status()
    with part.open(mode) as stream:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if chunk:
                stream.write(chunk)
                hasher.update(chunk)
```
- [ ] **Step 7: Run** the focused tests and confirm pass.
- [ ] **Step 8: Commit** with `git add blackzero/downloader.py tests/test_downloader.py; git commit -m "feat: add reliable streamed downloads"`.

### Task 4: Add CLI parsing, output, and exit codes

**Files:**
- Create: `blackzero/cli.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- `build_parser() -> argparse.ArgumentParser`.
- `main(argv: Sequence[str] | None = None) -> int`.
- `run_downloads(urls: Sequence[str], options: DownloadOptions, stdout: TextIO, stderr: TextIO) -> int`.

- [ ] **Step 1: Write failing parser tests** for positional URLs, all options, defaults, `--filename` with multiple URLs, invalid timeout/retries, and help/version.
- [ ] **Step 2: Write failing execution tests** for quiet output, per-URL result reporting, stderr errors, and return codes `0`, `1`, and `2`.
- [ ] **Step 3: Implement** `argparse` parsing and map parser errors to code `2` without traceback.

```python
parser.add_argument("urls", nargs="+")
parser.add_argument("-o", "--output-dir", type=Path)
parser.add_argument("-n", "--filename")
parser.add_argument("--retries", type=positive_int, default=3)
parser.add_argument("--timeout", type=positive_float, default=30.0)
```
- [ ] **Step 4: Implement** `run_downloads` with `tqdm` only when stdout is a TTY and `quiet` is false; pass a progress callback into `download`.
- [ ] **Step 5: Run** `pytest tests/test_cli.py -q`; expect pass.
- [ ] **Step 6: Commit** with `git add blackzero/cli.py tests/test_cli.py; git commit -m "feat: add scriptable CLI"`.

### Task 5: Preserve the legacy launcher and add package entry point

**Files:**
- Modify: `DownloadFiles.py`
- Create: `pyproject.toml`
- Create: `tests/test_compatibility.py`

- [ ] **Step 1: Write failing compatibility tests** proving no-argument execution requests one URL and URL-argument execution delegates without prompting.
- [ ] **Step 2: Implement** `DownloadFiles.py` as a thin launcher; retain the Spanish banner/prompt only when no URL arguments are supplied.
- [ ] **Step 3: Configure** `pyproject.toml` with package discovery, Python version floor, `requests`/`tqdm` runtime dependencies, `pytest` and `ruff` test/dev dependencies, and console script `blackzero = "blackzero.cli:main"`.

```toml
[project.scripts]
blackzero = "blackzero.cli:main"

[project.optional-dependencies]
dev = ["pytest>=8,<9", "ruff>=0.6,<1"]
```
- [ ] **Step 4: Run** `pytest tests/test_compatibility.py -q` and `python -m blackzero --help`; expect pass/help output.
- [ ] **Step 5: Commit** with `git add DownloadFiles.py pyproject.toml tests/test_compatibility.py; git commit -m "build: package blackzero CLI"`.

### Task 6: Complete documentation and operational examples

**Files:**
- Modify: `README.md`
- Modify: `requirements.txt`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Document** installation with `python -m pip install -e .` and direct execution with `python DownloadFiles.py`.
- [ ] **Step 2: Document** positional URLs and every supported option with Windows PowerShell and POSIX examples.
- [ ] **Step 3: Document** exit codes, `.part` cleanup, resume limitations, checksum syntax, and collision behavior.
- [ ] **Step 4: Align** `requirements.txt` with the runtime dependencies declared in `pyproject.toml`: `requests>=2.31,<3` and `tqdm>=4.66,<5`.
- [ ] **Step 5: Add** a changelog entry describing the CLI contract and compatibility guarantee.
- [ ] **Step 6: Run** the README commands in a temporary output directory using a local HTTP fixture; correct any mismatch.
- [ ] **Step 7: Commit** with `git add README.md CHANGELOG.md requirements.txt pyproject.toml; git commit -m "docs: document blackzero CLI"`.

### Task 7: Run full quality gates and record limitations

**Files:**
- Modify: `README.md` only if validation reveals an incorrect command.

- [ ] **Step 1: Run** `pytest -q`.
- [ ] **Step 2: Run** `python -m compileall -q blackzero DownloadFiles.py` and `ruff check blackzero DownloadFiles.py tests` using the dev dependency declared in `pyproject.toml`.
- [ ] **Step 3: Run** CLI smoke checks: `python -m blackzero --help`, invalid URL expecting code `2`, local successful download expecting code `0`, and local checksum failure expecting code `1`.
- [ ] **Step 4: Verify** no external-network test dependency, no secret files, no unintended generated files, and no partial files after normal failures.
- [ ] **Step 5: Update** README limitations for servers that do not support Range or provide `Content-Length`.
- [ ] **Step 6: Commit** with `git add .; git commit -m "test: verify blackzero release quality gates"`.
