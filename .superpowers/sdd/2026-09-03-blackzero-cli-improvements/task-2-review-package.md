BASE ec75b7e
HEAD f5c8582
 blackzero/files.py  | 124 ++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_files.py |  94 +++++++++++++++++++++++++++++++++++++++
 2 files changed, 218 insertions(+)
diff --git a/blackzero/files.py b/blackzero/files.py
new file mode 100644
index 0000000..381f3ab
--- /dev/null
+++ b/blackzero/files.py
@@ -0,0 +1,124 @@
+"""Safe filename, destination, and temporary-file helpers."""
+
+from __future__ import annotations
+
+import os
+import re
+from pathlib import Path
+from typing import Mapping
+from urllib.parse import unquote, urlsplit
+
+
+_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]+')
+_RESERVED_NAMES = {
+    "CON",
+    "PRN",
+    "AUX",
+    "NUL",
+    *(f"COM{number}" for number in range(1, 10)),
+    *(f"LPT{number}" for number in range(1, 10)),
+}
+
+
+def default_download_dir() -> Path:
+    """Return the current user's platform-default Downloads directory."""
+
+    return (Path.home() / "Downloads").expanduser().resolve()
+
+
+def _fallback_name(fallback: str) -> str:
+    cleaned = _sanitize_candidate(fallback)
+    return cleaned or "archivo_descargado"
+
+
+def _sanitize_candidate(candidate: str) -> str:
+    cleaned = _INVALID_FILENAME_CHARS.sub("_", str(candidate)).strip()
+    cleaned = re.sub(r"_+", "_", cleaned).rstrip(" .")
+    if not cleaned:
+        return ""
+
+    stem = cleaned.split(".", 1)[0]
+    if stem.upper() in _RESERVED_NAMES:
+        cleaned = f"{stem}_{cleaned[len(stem):]}"
+    return cleaned
+
+
+def sanitize_filename(candidate: str, fallback: str = "archivo_descargado") -> str:
+    """Return a filesystem-safe single filename, never a path."""
+
+    cleaned = _sanitize_candidate(candidate)
+    return cleaned or _fallback_name(fallback)
+
+
+def _header_value(headers: Mapping[str, str], name: str) -> str | None:
+    name = name.casefold()
+    for key, value in headers.items():
+        if key.casefold() == name:
+            return value
+    return None
+
+
+def _content_disposition_filename(value: str) -> str | None:
+    extended = re.search(r"(?:^|;)\s*filename\*\s*=\s*([^;]+)", value, re.I)
+    if extended:
+        encoded = extended.group(1).strip().strip('"')
+        _, separator, payload = encoded.partition("''")
+        return unquote(payload if separator else encoded)
+
+    regular = re.search(
+        r'(?:^|;)\s*filename\s*=\s*(?:"([^"]*)"|([^;]*))', value, re.I
+    )
+    if regular:
+        return (regular.group(1) or regular.group(2)).strip()
+    return None
+
+
+def filename_from_response(url: str, headers: Mapping[str, str]) -> str:
+    """Choose and sanitize a filename from response headers or the URL."""
+
+    disposition = _header_value(headers, "Content-Disposition")
+    if disposition:
+        filename = _content_disposition_filename(disposition)
+        if filename:
+            return sanitize_filename(filename)
+
+    path = urlsplit(url).path
+    url_name = unquote(path.rsplit("/", 1)[-1]) if path else ""
+    return sanitize_filename(url_name)
+
+
+def choose_destination(directory: Path, filename: str, overwrite: bool) -> Path:
+    """Create the output directory and select a collision-safe destination."""
+
+    root = Path(directory).expanduser().resolve()
+    root.mkdir(parents=True, exist_ok=True)
+    safe_name = sanitize_filename(filename)
+    destination = (root / safe_name).resolve()
+    if not destination.is_relative_to(root):
+        raise ValueError("destination must remain inside the output directory")
+    if overwrite or not destination.exists():
+        return destination
+
+    stem = destination.stem
+    suffix = destination.suffix
+    counter = 1
+    while True:
+        candidate = (root / f"{stem} ({counter}){suffix}").resolve()
+        if not candidate.exists():
+            return candidate
+        counter += 1
+
+
+def part_path(destination: Path) -> Path:
+    """Return the temporary path used while writing a destination."""
+
+    destination = Path(destination)
+    return destination.with_name(f"{destination.name}.part")
+
+
+def finalize_part(part: Path, destination: Path) -> None:
+    """Atomically move a completed temporary file to its final destination."""
+
+    destination = Path(destination)
+    destination.parent.mkdir(parents=True, exist_ok=True)
+    os.replace(Path(part), destination)
diff --git a/tests/test_files.py b/tests/test_files.py
new file mode 100644
index 0000000..0f05f28
--- /dev/null
+++ b/tests/test_files.py
@@ -0,0 +1,94 @@
+from pathlib import Path
+
+from blackzero.files import (
+    choose_destination,
+    default_download_dir,
+    filename_from_response,
+    finalize_part,
+    part_path,
+    sanitize_filename,
+)
+
+
+def test_default_download_dir_points_to_downloads():
+    assert default_download_dir() == (Path.home() / "Downloads").resolve()
+
+
+def test_filename_from_response_uses_decoded_url_path_then_fallback():
+    assert filename_from_response(
+        "https://example.test/files/reporte%20final.pdf?download=1", {}
+    ) == "reporte final.pdf"
+    assert filename_from_response("https://example.test", {}) == "archivo_descargado"
+
+
+def test_filename_from_response_prefers_content_disposition_filename():
+    headers = {"content-disposition": 'attachment; filename="informe final.pdf"'}
+
+    assert filename_from_response("https://example.test/file.bin", headers) == (
+        "informe final.pdf"
+    )
+
+
+def test_filename_from_response_supports_rfc5987_filename():
+    headers = {"Content-Disposition": "attachment; filename*=UTF-8''caf%C3%A9.txt"}
+
+    assert filename_from_response("https://example.test/file.bin", headers) == "café.txt"
+
+
+def test_sanitize_filename_removes_windows_invalid_characters_and_separators():
+    sanitized = sanitize_filename(' report<draft>:"final"/\\*.txt ')
+
+    assert sanitized == "report_draft_final_.txt"
+    assert "/" not in sanitized
+    assert "\\" not in sanitized
+
+
+def test_sanitize_filename_replaces_reserved_names_and_uses_fallback_for_empty_input():
+    assert sanitize_filename("CON") == "CON_"
+    assert sanitize_filename("aux.txt") == "aux_.txt"
+    assert sanitize_filename("...") == "archivo_descargado"
+    assert sanitize_filename("   ", fallback="sin_nombre") == "sin_nombre"
+
+
+def test_choose_destination_creates_directory_and_suffixes_collisions(tmp_path):
+    directory = tmp_path / "nested" / "downloads"
+    first = choose_destination(directory, "reporte.txt", overwrite=False)
+    first.write_text("existing", encoding="utf-8")
+
+    second = choose_destination(directory, "reporte.txt", overwrite=False)
+
+    assert first == directory.resolve() / "reporte.txt"
+    assert second == directory.resolve() / "reporte (1).txt"
+    assert second.parent == directory.resolve()
+
+
+def test_choose_destination_overwrite_returns_requested_path(tmp_path):
+    destination = choose_destination(tmp_path, "reporte.txt", overwrite=True)
+    destination.write_text("old", encoding="utf-8")
+
+    assert choose_destination(tmp_path, "reporte.txt", overwrite=True) == destination
+
+
+def test_choose_destination_keeps_resolved_output_inside_directory(tmp_path):
+    destination = choose_destination(tmp_path / "downloads", "..\\outside.txt", False)
+
+    assert destination.parent == (tmp_path / "downloads").resolve()
+    assert destination.is_relative_to((tmp_path / "downloads").resolve())
+
+
+def test_part_path_adds_part_suffix():
+    destination = Path("downloads") / "report.zip"
+
+    assert part_path(destination) == Path("downloads") / "report.zip.part"
+
+
+def test_finalize_part_atomically_moves_completed_file(tmp_path):
+    destination = tmp_path / "downloads" / "report.zip"
+    part = part_path(destination)
+    part.parent.mkdir(parents=True)
+    part.write_bytes(b"complete")
+
+    finalize_part(part, destination)
+
+    assert destination.read_bytes() == b"complete"
+    assert not part.exists()
