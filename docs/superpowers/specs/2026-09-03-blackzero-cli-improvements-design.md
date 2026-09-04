# BlackZero CLI Improvements Design

**Date:** 2026-09-03

**Goal:** Evolve the current interactive downloader into a reliable, scriptable terminal CLI while preserving the existing no-argument interactive flow.

## Scope

The application remains a single-purpose HTTP/HTTPS file downloader. It will support one or more URLs, configurable destination and filename, progress output, quiet output, timeouts, retries, resumable downloads, optional SHA-256 verification, safe temporary files, and meaningful process exit codes.

The existing command remains valid:

```text
python DownloadFiles.py
```

The primary interface becomes:

```text
python -m blackzero URL [URL ...] [options]
```

`python DownloadFiles.py URL` will also be accepted for compatibility.

## Architecture

`blackzero/cli.py` parses arguments and owns terminal output. `blackzero/downloader.py` performs HTTP transfer and returns structured results without printing. `blackzero/files.py` resolves safe names, destination paths, collision policy, temporary paths, and atomic finalization. `blackzero/models.py` defines typed options/results/errors shared by the other modules. The root `DownloadFiles.py` remains a compatibility launcher that delegates to the CLI.

The downloader will use `requests.Session`, `timeout=(connect, read)`, `iter_content(chunk_size=64 * 1024)`, and a response context manager. A completed transfer is renamed from a `.part` file to its final path. Failed transfers remove the temporary file unless `--keep-partial` is explicitly selected.

## CLI contract

- Positional `urls`: one or more HTTP/HTTPS URLs.
- `-o, --output-dir PATH`: destination directory; default is the platform user's Downloads directory.
- `-n, --filename NAME`: explicit filename; allowed only with one URL.
- `--overwrite`: replace an existing final file; default is collision-safe suffixing.
- `--resume`: use HTTP Range requests when a `.part` file exists and the server advertises byte ranges.
- `--retries N`: retry transient network failures and HTTP 408/429/5xx responses; default `3`.
- `--timeout SECONDS`: connect and read timeout; default `30`.
- `--checksum sha256:HEX`: verify the completed file and delete it on mismatch.
- `-q, --quiet`: suppress progress and informational output; errors still go to stderr.
- `--keep-partial`: preserve `.part` files after failure.
- `--version` and `--help`.

Exit code `0` means all URLs succeeded; `2` means invalid CLI input; `1` means one or more downloads failed or checksum verification failed. Multiple URLs are processed sequentially and each result is reported independently.

## Safety and failure behavior

Only `http` and `https` schemes with a hostname are accepted. Filenames come from `Content-Disposition` when safely parseable, then the URL path, then `archivo_descargado`; path separators, control characters, Windows-reserved names, and invalid characters are sanitized. The output path must remain inside the selected output directory.

The destination directory is created if necessary. Existing files are never overwritten unless `--overwrite` is present. Network, filesystem, invalid-header, interruption, and checksum errors are represented as typed errors; the CLI maps them to stable exit codes and readable stderr messages.

## Testing and packaging

Tests will use `pytest` and a local HTTP server fixture, with no external network dependency. Coverage will include parsing, URL validation, filename sanitization, collision behavior, known and unknown content length, retryable statuses, timeout/error cleanup, resume with Range/206, checksum success/failure, quiet output, and exit codes.

`pyproject.toml` will define the package, runtime dependencies (`requests`, `tqdm`), test dependency (`pytest`), and the `blackzero` console entry point. README usage will document both interactive compatibility and scriptable CLI commands.

## Out of scope

Parallel downloads, authentication profiles, proxy configuration, torrent support, GUI functionality, and a persistent configuration file are deferred until the single-download reliability contract is stable.
