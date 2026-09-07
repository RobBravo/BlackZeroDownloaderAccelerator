BASE cc54907
HEAD 72b87f8
 blackzero/downloader.py  | 214 ++++++++++++++++++++++++++++
 tests/test_downloader.py | 357 +++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 571 insertions(+)
diff --git a/blackzero/downloader.py b/blackzero/downloader.py
new file mode 100644
index 0000000..9acb752
--- /dev/null
+++ b/blackzero/downloader.py
@@ -0,0 +1,214 @@
+"""Reliable streamed HTTP downloads with safe temporary files."""
+
+from __future__ import annotations
+
+import hashlib
+import time
+from collections.abc import Callable
+from pathlib import Path
+from urllib.parse import urlsplit
+
+import requests
+
+from .errors import DownloadError
+from .files import (
+    choose_destination,
+    filename_from_response,
+    finalize_part,
+    part_path,
+)
+from .models import DownloadOptions, DownloadResult
+
+
+_CHUNK_SIZE = 64 * 1024
+_MAX_BACKOFF_SECONDS = 30.0
+
+
+def parse_checksum(value: str | None) -> tuple[str, str] | None:
+    """Parse the supported ``sha256:HEX`` checksum syntax."""
+
+    if value is None:
+        return None
+
+    algorithm, separator, digest = value.partition(":")
+    digest = digest.lower()
+    if (
+        separator != ":"
+        or algorithm.lower() != "sha256"
+        or len(digest) != 64
+        or any(character not in "0123456789abcdef" for character in digest)
+    ):
+        raise ValueError("checksum must use sha256:HEX format")
+    return "sha256", digest
+
+
+def _validate_url(url: str) -> None:
+    parsed = urlsplit(url)
+    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
+        raise DownloadError("URL must use HTTP or HTTPS and include a hostname", "input")
+
+
+def _is_retryable_status(status_code: int) -> bool:
+    return status_code in {408, 429} or 500 <= status_code <= 599
+
+
+def _retry_delay(response: requests.Response | None, attempt: int) -> float:
+    if response is not None:
+        retry_after = response.headers.get("Retry-After")
+        if retry_after is not None:
+            try:
+                return min(max(float(retry_after), 0.0), _MAX_BACKOFF_SECONDS)
+            except ValueError:
+                pass
+    return min(float(2**attempt), _MAX_BACKOFF_SECONDS)
+
+
+def _total_size(response: requests.Response, existing_size: int, resumed: bool) -> int | None:
+    content_range = response.headers.get("Content-Range")
+    if resumed and content_range and "/" in content_range:
+        total = content_range.rsplit("/", 1)[1]
+        if total.isdigit():
+            return int(total)
+
+    content_length = response.headers.get("Content-Length")
+    if content_length and content_length.isdigit():
+        return existing_size + int(content_length) if resumed else int(content_length)
+    return None
+
+
+def _seed_hasher(part: Path, hasher: hashlib._Hash) -> None:
+    with part.open("rb") as stream:
+        while chunk := stream.read(_CHUNK_SIZE):
+            hasher.update(chunk)
+
+
+def download(
+    url: str,
+    options: DownloadOptions,
+    progress: Callable[[int, int | None], None] | None = None,
+) -> DownloadResult:
+    """Download one URL, returning a finalized file or a typed error."""
+
+    _validate_url(url)
+    try:
+        checksum = parse_checksum(options.checksum)
+    except ValueError as error:
+        raise DownloadError(str(error), "input", cause=error) from error
+
+    destination: Path | None = None
+    temporary: Path | None = None
+    completed = False
+    fallback_name = options.filename or filename_from_response(url, {})
+
+    try:
+        initial_destination = choose_destination(
+            options.output_dir, fallback_name, options.overwrite
+        )
+        initial_part = part_path(initial_destination)
+        temporary = initial_part
+
+        with requests.Session() as session:
+            for attempt in range(options.retries + 1):
+                headers: dict[str, str] = {}
+                if options.resume and initial_part.exists():
+                    headers["Range"] = f"bytes={initial_part.stat().st_size}-"
+
+                try:
+                    with session.get(
+                        url,
+                        stream=True,
+                        headers=headers,
+                        timeout=(options.timeout, options.timeout),
+                    ) as response:
+                        if _is_retryable_status(response.status_code):
+                            if attempt < options.retries:
+                                time.sleep(_retry_delay(response, attempt))
+                                continue
+                            raise DownloadError(
+                                f"HTTP {response.status_code} while downloading {url}",
+                                "http",
+                            )
+
+                        if response.status_code >= 400:
+                            raise DownloadError(
+                                f"HTTP {response.status_code} while downloading {url}",
+                                "http",
+                            )
+
+                        filename = options.filename or filename_from_response(
+                            url, response.headers
+                        )
+                        destination = choose_destination(
+                            options.output_dir, filename, options.overwrite
+                        )
+                        temporary = part_path(destination)
+                        if (
+                            "Range" in headers
+                            and response.status_code == 206
+                            and temporary != initial_part
+                        ):
+                            if not options.keep_partial:
+                                initial_part.unlink(missing_ok=True)
+                            initial_part = temporary
+                            continue
+                        existing_size = temporary.stat().st_size if temporary.exists() else 0
+                        resumed = (
+                            options.resume
+                            and existing_size > 0
+                            and response.status_code == 206
+                        )
+                        if not resumed:
+                            existing_size = 0
+
+                        hasher = hashlib.sha256() if checksum else None
+                        if resumed and hasher is not None:
+                            _seed_hasher(temporary, hasher)
+
+                        total = _total_size(response, existing_size, resumed)
+                        written = existing_size
+                        mode = "ab" if resumed else "wb"
+                        with temporary.open(mode) as stream:
+                            for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
+                                if not chunk:
+                                    continue
+                                stream.write(chunk)
+                                written += len(chunk)
+                                if hasher is not None:
+                                    hasher.update(chunk)
+                                if progress is not None:
+                                    progress(written, total)
+
+                        finalize_part(temporary, destination, options.overwrite)
+                        if checksum is not None and hasher is not None:
+                            _, expected = checksum
+                            if hasher.hexdigest() != expected:
+                                destination.unlink(missing_ok=True)
+                                raise DownloadError("checksum verification failed", "checksum")
+
+                        completed = True
+                        return DownloadResult(
+                            url=url,
+                            path=destination,
+                            bytes_written=written,
+                            resumed=resumed,
+                            checksum_verified=checksum is not None,
+                        )
+                except requests.RequestException as error:
+                    if attempt < options.retries:
+                        time.sleep(_retry_delay(None, attempt))
+                        continue
+                    raise DownloadError(
+                        f"network request failed while downloading {url}",
+                        "network",
+                        cause=error,
+                    ) from error
+
+    except DownloadError:
+        raise
+    except OSError as error:
+        raise DownloadError(
+            f"filesystem error while downloading {url}", "filesystem", cause=error
+        ) from error
+    finally:
+        if not completed and not options.keep_partial and temporary is not None:
+            temporary.unlink(missing_ok=True)
diff --git a/tests/test_downloader.py b/tests/test_downloader.py
new file mode 100644
index 0000000..d34b079
--- /dev/null
+++ b/tests/test_downloader.py
@@ -0,0 +1,357 @@
+from __future__ import annotations
+
+import hashlib
+import threading
+import time
+from collections.abc import Iterator
+from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
+from pathlib import Path
+
+import pytest
+import requests
+
+from blackzero.errors import DownloadError
+from blackzero.files import part_path
+from blackzero.models import DownloadOptions
+
+
+PAYLOAD = b"BlackZero reliable download payload" * 3_000
+PARTIAL_SIZE = 70 * 1024
+CHUNK_SIZE = 64 * 1024
+
+
+class _DownloadServer(ThreadingHTTPServer):
+    allow_reuse_address = True
+
+    def __init__(self, address, handler):
+        super().__init__(address, handler)
+        self.attempts: dict[str, int] = {}
+        self.ranges: list[str | None] = []
+
+
+class _Handler(BaseHTTPRequestHandler):
+    protocol_version = "HTTP/1.1"
+
+    def do_GET(self) -> None:  # noqa: N802
+        path = self.path
+        self.server.attempts[path] = self.server.attempts.get(path, 0) + 1
+        self.server.ranges.append(self.headers.get("Range"))
+
+        if path == "/unknown":
+            self.protocol_version = "HTTP/1.0"
+            self.send_response(200)
+            self.end_headers()
+            self.wfile.write(PAYLOAD)
+            self.close_connection = True
+            return
+
+        if path == "/slow":
+            time.sleep(0.2)
+            self._send(PAYLOAD)
+            return
+
+        if path == "/broken":
+            self.send_response(200)
+            self.send_header("Content-Length", str(len(PAYLOAD)))
+            self.end_headers()
+            self.wfile.write(PAYLOAD[:PARTIAL_SIZE])
+            self.wfile.flush()
+            self.close_connection = True
+            return
+
+        if path in {"/retry-503", "/retry-429", "/retry-408"}:
+            statuses = {
+                "/retry-503": 503,
+                "/retry-429": 429,
+                "/retry-408": 408,
+            }
+            if self.server.attempts[path] == 1:
+                self.send_response(statuses[path])
+                if path == "/retry-429":
+                    self.send_header("Retry-After", "0")
+                self.send_header("Content-Length", "0")
+                self.end_headers()
+                return
+
+        if path == "/missing":
+            self.send_response(404)
+            self.send_header("Content-Length", "0")
+            self.end_headers()
+            return
+
+        if path == "/range":
+            range_header = self.headers.get("Range")
+            if range_header:
+                start = int(range_header.removeprefix("bytes=").removesuffix("-"))
+                body = PAYLOAD[start:]
+                self.send_response(206)
+                self.send_header("Content-Range", f"bytes {start}-{len(PAYLOAD) - 1}/{len(PAYLOAD)}")
+                self.send_header("Content-Length", str(len(body)))
+                self.send_header("Content-Disposition", 'attachment; filename="server.bin"')
+                self.send_header("Connection", "close")
+                self.end_headers()
+                self.wfile.write(body)
+                return
+
+        if path == "/ignore-range":
+            self._send(PAYLOAD)
+            return
+
+        self._send(PAYLOAD)
+
+    def _send(self, body: bytes) -> None:
+        self.send_response(200)
+        self.send_header("Content-Length", str(len(body)))
+        self.send_header("Content-Disposition", 'attachment; filename="server.bin"')
+        self.end_headers()
+        self.wfile.write(body)
+
+    def log_message(self, format: str, *args: object) -> None:
+        return
+
+
+@pytest.fixture
+def http_server() -> Iterator[tuple[_DownloadServer, str]]:
+    server = _DownloadServer(("127.0.0.1", 0), _Handler)
+    thread = threading.Thread(target=server.serve_forever, daemon=True)
+    thread.start()
+    try:
+        yield server, f"http://127.0.0.1:{server.server_port}"
+    finally:
+        server.shutdown()
+        thread.join()
+        server.server_close()
+
+
+def _options(tmp_path: Path, **overrides: object) -> DownloadOptions:
+    values: dict[str, object] = {"output_dir": tmp_path, "retries": 1}
+    values.update(overrides)
+    return DownloadOptions(**values)
+
+
+def _downloader():
+    try:
+        from blackzero.downloader import download, parse_checksum
+    except ModuleNotFoundError as exc:
+        pytest.fail(f"downloader contract is not implemented: {exc}")
+    return download, parse_checksum
+
+
+def test_parse_checksum_accepts_sha256_and_rejects_invalid_values():
+    _, parse_checksum = _downloader()
+    digest = hashlib.sha256(PAYLOAD).hexdigest()
+
+    assert parse_checksum(None) is None
+    assert parse_checksum(f"sha256:{digest.upper()}") == ("sha256", digest)
+    with pytest.raises(ValueError, match="checksum"):
+        parse_checksum("md5:1234")
+    with pytest.raises(ValueError, match="checksum"):
+        parse_checksum("sha256:not-a-digest")
+
+
+def test_download_streams_known_length_reports_progress_and_closes_response(
+    tmp_path, http_server, monkeypatch
+):
+    download, _ = _downloader()
+    server, base_url = http_server
+    progress: list[tuple[int, int | None]] = []
+    responses = []
+    original_get = requests.Session.get
+
+    def capture_get(self, *args, **kwargs):
+        response = original_get(self, *args, **kwargs)
+        responses.append(response)
+        return response
+
+    monkeypatch.setattr(requests.Session, "get", capture_get)
+
+    result = download(
+        f"{base_url}/known",
+        _options(tmp_path, timeout=0.25),
+        progress=lambda written, total: progress.append((written, total)),
+    )
+
+    assert result.path.read_bytes() == PAYLOAD
+    assert result.bytes_written == len(PAYLOAD)
+    assert result.resumed is False
+    assert result.checksum_verified is False
+    assert progress[-1] == (len(PAYLOAD), len(PAYLOAD))
+    assert responses[0].raw.closed is True
+    assert server.attempts["/known"] == 1
+
+
+def test_download_uses_unknown_content_length_and_timeout_tuple(tmp_path, http_server, monkeypatch):
+    download, _ = _downloader()
+    _, base_url = http_server
+    progress: list[tuple[int, int | None]] = []
+    seen_timeouts = []
+    original_get = requests.Session.get
+
+    def capture_get(self, *args, **kwargs):
+        seen_timeouts.append(kwargs["timeout"])
+        return original_get(self, *args, **kwargs)
+
+    monkeypatch.setattr(requests.Session, "get", capture_get)
+
+    result = download(
+        f"{base_url}/unknown",
+        _options(tmp_path, timeout=0.25),
+        progress=lambda written, total: progress.append((written, total)),
+    )
+
+    assert result.path.read_bytes() == PAYLOAD
+    assert progress[-1] == (len(PAYLOAD), None)
+    assert seen_timeouts == [(0.25, 0.25)]
+
+
+@pytest.mark.parametrize("path", ["/retry-503", "/retry-429", "/retry-408"])
+def test_download_retries_transient_http_statuses(tmp_path, http_server, monkeypatch, path):
+    download, _ = _downloader()
+    server, base_url = http_server
+    sleeps = []
+    monkeypatch.setattr("blackzero.downloader.time.sleep", sleeps.append)
+
+    result = download(f"{base_url}{path}", _options(tmp_path, retries=1))
+
+    assert result.path.read_bytes() == PAYLOAD
+    assert server.attempts[path] == 2
+    assert sleeps == [0.0 if path == "/retry-429" else 1.0]
+
+
+def test_download_does_not_retry_permanent_http_error_and_removes_part(tmp_path, http_server):
+    download, _ = _downloader()
+    server, base_url = http_server
+
+    with pytest.raises(DownloadError, match="404") as caught:
+        download(f"{base_url}/missing", _options(tmp_path, retries=3))
+
+    assert caught.value.kind == "http"
+    assert server.attempts["/missing"] == 1
+    assert not list(tmp_path.glob("*.part"))
+
+
+def test_download_removes_existing_partial_after_failed_resume(tmp_path, http_server):
+    download, _ = _downloader()
+    _, base_url = http_server
+    destination = tmp_path / "resume-failure.bin"
+    part = part_path(destination)
+    part.write_bytes(PAYLOAD[:100])
+
+    with pytest.raises(DownloadError, match="404"):
+        download(
+            f"{base_url}/missing",
+            _options(tmp_path, filename=destination.name, resume=True),
+        )
+
+    assert not part.exists()
+
+
+def test_download_propagates_timeout_as_typed_error_and_cleans_partial(tmp_path, http_server):
+    download, _ = _downloader()
+    _, base_url = http_server
+
+    with pytest.raises(DownloadError) as caught:
+        download(f"{base_url}/slow", _options(tmp_path, timeout=0.02))
+
+    assert caught.value.kind == "network"
+    assert not list(tmp_path.glob("*.part"))
+
+
+def test_download_preserves_partial_file_only_when_requested(tmp_path, http_server):
+    download, _ = _downloader()
+    _, base_url = http_server
+
+    with pytest.raises(DownloadError):
+        download(f"{base_url}/broken", _options(tmp_path / "discard"))
+    with pytest.raises(DownloadError):
+        download(
+            f"{base_url}/broken",
+            _options(tmp_path / "keep", keep_partial=True),
+        )
+
+    assert not list((tmp_path / "discard").glob("*.part"))
+    kept_parts = list((tmp_path / "keep").glob("*.part"))
+    assert len(kept_parts) == 1
+    assert kept_parts[0].read_bytes() == PAYLOAD[:CHUNK_SIZE]
+
+
+def test_download_resumes_a_partial_file_after_range_response(tmp_path, http_server):
+    download, _ = _downloader()
+    server, base_url = http_server
+    destination = tmp_path / "resume.bin"
+    part = part_path(destination)
+    part.write_bytes(PAYLOAD[:100])
+
+    result = download(
+        f"{base_url}/range",
+        _options(tmp_path, filename="resume.bin", resume=True),
+    )
+
+    assert server.ranges[-1] == "bytes=100-"
+    assert result.path == destination.resolve()
+    assert result.path.read_bytes() == PAYLOAD
+    assert result.bytes_written == len(PAYLOAD)
+    assert result.resumed is True
+    assert not part.exists()
+
+
+def test_download_restarts_when_response_filename_changes_resume_target(tmp_path, http_server):
+    download, _ = _downloader()
+    server, base_url = http_server
+    url_part = part_path(tmp_path / "range")
+    url_part.write_bytes(PAYLOAD[:100])
+
+    result = download(f"{base_url}/range", _options(tmp_path, resume=True))
+
+    assert server.ranges == ["bytes=100-", None]
+    assert result.path.name == "server.bin"
+    assert result.path.read_bytes() == PAYLOAD
+    assert result.resumed is False
+    assert not url_part.exists()
+
+
+def test_download_restarts_when_server_ignores_range_request(tmp_path, http_server):
+    download, _ = _downloader()
+    server, base_url = http_server
+    destination = tmp_path / "restart.bin"
+    part = part_path(destination)
+    part.write_bytes(b"stale partial data")
+
+    result = download(
+        f"{base_url}/ignore-range",
+        _options(tmp_path, filename="restart.bin", resume=True),
+    )
+
+    assert server.ranges[-1] == f"bytes={len(b'stale partial data')}-"
+    assert result.path.read_bytes() == PAYLOAD
+    assert result.resumed is False
+    assert not part.exists()
+
+
+def test_download_verifies_sha256_incrementally(tmp_path, http_server):
+    download, _ = _downloader()
+    _, base_url = http_server
+    digest = hashlib.sha256(PAYLOAD).hexdigest()
+
+    result = download(
+        f"{base_url}/known",
+        _options(tmp_path, checksum=f"sha256:{digest}"),
+    )
+
+    assert result.path.read_bytes() == PAYLOAD
+    assert result.checksum_verified is True
+
+
+def test_download_deletes_completed_file_when_checksum_mismatches(tmp_path, http_server):
+    download, _ = _downloader()
+    _, base_url = http_server
+
+    with pytest.raises(DownloadError, match="checksum") as caught:
+        download(
+            f"{base_url}/known",
+            _options(tmp_path, checksum=f"sha256:{'0' * 64}"),
+        )
+
+    assert caught.value.kind == "checksum"
+    assert not list(tmp_path.glob("*.bin"))
+    assert not list(tmp_path.glob("*.part"))
