BASE 352d5c5
HEAD ec75b7e
--- LOG ---
ec75b7e refactor: define downloader contracts
--- STAT ---
 blackzero/__init__.py |  6 +++++
 blackzero/errors.py   | 15 +++++++++++
 blackzero/models.py   | 44 +++++++++++++++++++++++++++++++
 tests/test_models.py  | 72 +++++++++++++++++++++++++++++++++++++++++++++++++++
 4 files changed, 137 insertions(+)
--- DIFF ---
diff --git a/blackzero/__init__.py b/blackzero/__init__.py
new file mode 100644
index 0000000..a1b43a3
--- /dev/null
+++ b/blackzero/__init__.py
@@ -0,0 +1,6 @@
+"""Typed contracts for the BlackZero downloader."""
+
+from .errors import DownloadError
+from .models import DownloadOptions, DownloadResult
+
+__all__ = ["DownloadError", "DownloadOptions", "DownloadResult"]
diff --git a/blackzero/errors.py b/blackzero/errors.py
new file mode 100644
index 0000000..044d2ae
--- /dev/null
+++ b/blackzero/errors.py
@@ -0,0 +1,15 @@
+"""Typed errors shared by the downloader layers."""
+
+from dataclasses import dataclass
+
+
+@dataclass
+class DownloadError(Exception):
+    """An error raised while validating or downloading a file."""
+
+    message: str
+    kind: str
+    cause: BaseException | None = None
+
+    def __post_init__(self) -> None:
+        Exception.__init__(self, self.message)
diff --git a/blackzero/models.py b/blackzero/models.py
new file mode 100644
index 0000000..a6aac2b
--- /dev/null
+++ b/blackzero/models.py
@@ -0,0 +1,44 @@
+"""Data models shared by the downloader layers."""
+
+from dataclasses import dataclass, field
+from pathlib import Path
+
+
+def _default_output_dir() -> Path:
+    return (Path.home() / "Downloads").expanduser().resolve()
+
+
+def _normalized_path(value: Path) -> Path:
+    return Path(value).expanduser().resolve()
+
+
+@dataclass(frozen=True)
+class DownloadOptions:
+    output_dir: Path = field(default_factory=_default_output_dir)
+    filename: str | None = None
+    overwrite: bool = False
+    resume: bool = False
+    retries: int = 3
+    timeout: float = 30.0
+    checksum: str | None = None
+    quiet: bool = False
+    keep_partial: bool = False
+
+    def __post_init__(self) -> None:
+        if self.retries <= 0:
+            raise ValueError("retries must be positive")
+        if self.timeout <= 0:
+            raise ValueError("timeout must be positive")
+        object.__setattr__(self, "output_dir", _normalized_path(self.output_dir))
+
+
+@dataclass(frozen=True)
+class DownloadResult:
+    url: str
+    path: Path
+    bytes_written: int
+    resumed: bool
+    checksum_verified: bool
+
+    def __post_init__(self) -> None:
+        object.__setattr__(self, "path", _normalized_path(self.path))
diff --git a/tests/test_models.py b/tests/test_models.py
new file mode 100644
index 0000000..ccedd25
--- /dev/null
+++ b/tests/test_models.py
@@ -0,0 +1,72 @@
+import pytest
+
+
+def _models():
+    try:
+        from blackzero.models import DownloadOptions, DownloadResult
+    except ModuleNotFoundError as exc:
+        pytest.fail(f"model contracts are not implemented: {exc}")
+    return DownloadOptions, DownloadResult
+
+
+def _errors():
+    try:
+        from blackzero.errors import DownloadError
+    except ModuleNotFoundError as exc:
+        pytest.fail(f"error contract is not implemented: {exc}")
+    return DownloadError
+
+
+def test_download_options_normalizes_output_path_and_uses_defaults(tmp_path):
+    DownloadOptions, _ = _models()
+
+    options = DownloadOptions(output_dir=tmp_path / "nested" / ".." / "downloads")
+
+    assert options.output_dir == (tmp_path / "downloads").resolve()
+    assert options.filename is None
+    assert options.overwrite is False
+    assert options.resume is False
+    assert options.retries == 3
+    assert options.timeout == 30.0
+    assert options.checksum is None
+    assert options.quiet is False
+    assert options.keep_partial is False
+
+
+def test_download_options_rejects_non_positive_retries_and_timeout(tmp_path):
+    DownloadOptions, _ = _models()
+
+    with pytest.raises(ValueError, match="retries"):
+        DownloadOptions(output_dir=tmp_path, retries=0)
+    with pytest.raises(ValueError, match="timeout"):
+        DownloadOptions(output_dir=tmp_path, timeout=0)
+
+
+def test_download_result_normalizes_path_and_preserves_transfer_fields(tmp_path):
+    _, DownloadResult = _models()
+
+    result = DownloadResult(
+        url="https://example.test/file.bin",
+        path=tmp_path / "folder" / ".." / "file.bin",
+        bytes_written=42,
+        resumed=True,
+        checksum_verified=True,
+    )
+
+    assert result.path == (tmp_path / "file.bin").resolve()
+    assert result.url == "https://example.test/file.bin"
+    assert result.bytes_written == 42
+    assert result.resumed is True
+    assert result.checksum_verified is True
+
+
+def test_download_error_exposes_message_kind_and_cause():
+    DownloadError = _errors()
+    cause = OSError("connection reset")
+
+    error = DownloadError("download failed", "network", cause=cause)
+
+    assert error.message == "download failed"
+    assert error.kind == "network"
+    assert error.cause is cause
+    assert str(error) == "download failed"
