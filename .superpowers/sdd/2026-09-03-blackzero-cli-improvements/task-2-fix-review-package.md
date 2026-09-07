BASE f5c8582
HEAD cc54907
 .../task-2-fix-report.md                           | 29 +++++++++++++
 blackzero/files.py                                 | 27 ++++++++++---
 tests/test_files.py                                | 47 ++++++++++++++++++++++
 3 files changed, 98 insertions(+), 5 deletions(-)
diff --git a/.superpowers/sdd/2026-09-03-blackzero-cli-improvements/task-2-fix-report.md b/.superpowers/sdd/2026-09-03-blackzero-cli-improvements/task-2-fix-report.md
new file mode 100644
index 0000000..5905925
--- /dev/null
+++ b/.superpowers/sdd/2026-09-03-blackzero-cli-improvements/task-2-fix-report.md
@@ -0,0 +1,29 @@
+# Task 2 Fix Round 1 Report
+
+## Scope
+
+Corrected the two review findings from Task 2 in the isolated worktree:
+
+- `finalize_part` now defaults to non-overwriting publication and preserves an existing destination by raising a clear `FileExistsError`. Passing `overwrite=True` is the explicit authorization required to replace a destination.
+- RFC 5987 `filename*` values now parse the `charset'language'encoded-payload` form, decode percent-encoded bytes using the declared charset, and safely fall back to URL-derived naming when the value is malformed or undecodable.
+
+## TDD evidence
+
+Added regression tests before the production correction. The focused suite initially failed with four expected failures: language-tagged `filename*`, invalid RFC 5987 fallback, rejection of an existing destination, and the new explicit overwrite argument.
+
+## Validation
+
+- Focused: `python -m pytest tests/test_files.py -q` — 15 passed.
+- Full: `python -m pytest -q` — 19 passed.
+
+The Windows `python.exe` app alias was unavailable to the shell, so validation used the installed Python 3.12 interpreter at `C:\Users\ingmo\AppData\Local\Programs\Python\Python312\python.exe`.
+
+## Files changed
+
+- `blackzero/files.py`
+- `tests/test_files.py`
+
+## Remaining concerns
+
+- The downloader call site will need to pass its overwrite decision explicitly in a later task, as planned.
+- The existing plan document still shows the old `finalize_part` signature; it was intentionally left unchanged because this round is restricted to the two code/test files plus this report.
diff --git a/blackzero/files.py b/blackzero/files.py
index 381f3ab..8c650ed 100644
--- a/blackzero/files.py
+++ b/blackzero/files.py
@@ -1,17 +1,17 @@
 """Safe filename, destination, and temporary-file helpers."""
 
 from __future__ import annotations
 
 import os
 import re
 from pathlib import Path
 from typing import Mapping
-from urllib.parse import unquote, urlsplit
+from urllib.parse import unquote, unquote_to_bytes, urlsplit
 
 
 _INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]+')
 _RESERVED_NAMES = {
     "CON",
     "PRN",
     "AUX",
     "NUL",
@@ -57,18 +57,24 @@ def _header_value(headers: Mapping[str, str], name: str) -> str | None:
             return value
     return None
 
 
 def _content_disposition_filename(value: str) -> str | None:
     extended = re.search(r"(?:^|;)\s*filename\*\s*=\s*([^;]+)", value, re.I)
     if extended:
         encoded = extended.group(1).strip().strip('"')
-        _, separator, payload = encoded.partition("''")
-        return unquote(payload if separator else encoded)
+        match = re.fullmatch(r"([^']+)'([^']*)'(.+)", encoded)
+        if match:
+            charset, _, payload = match.groups()
+            try:
+                return unquote_to_bytes(payload).decode(charset)
+            except (LookupError, UnicodeDecodeError):
+                return None
+        return None
 
     regular = re.search(
         r'(?:^|;)\s*filename\s*=\s*(?:"([^"]*)"|([^;]*))', value, re.I
     )
     if regular:
         return (regular.group(1) or regular.group(2)).strip()
     return None
 
@@ -111,14 +117,25 @@ def choose_destination(directory: Path, filename: str, overwrite: bool) -> Path:
 
 def part_path(destination: Path) -> Path:
     """Return the temporary path used while writing a destination."""
 
     destination = Path(destination)
     return destination.with_name(f"{destination.name}.part")
 
 
-def finalize_part(part: Path, destination: Path) -> None:
+def finalize_part(part: Path, destination: Path, overwrite: bool = False) -> None:
     """Atomically move a completed temporary file to its final destination."""
 
+    part = Path(part)
     destination = Path(destination)
     destination.parent.mkdir(parents=True, exist_ok=True)
-    os.replace(Path(part), destination)
+    if overwrite:
+        os.replace(part, destination)
+        return
+
+    try:
+        os.link(part, destination)
+    except FileExistsError as error:
+        raise FileExistsError(
+            f"destination already exists: {destination}"
+        ) from error
+    os.unlink(part)
diff --git a/tests/test_files.py b/tests/test_files.py
index 0f05f28..081fb4a 100644
--- a/tests/test_files.py
+++ b/tests/test_files.py
@@ -30,16 +30,32 @@ def test_filename_from_response_prefers_content_disposition_filename():
 
 
 def test_filename_from_response_supports_rfc5987_filename():
     headers = {"Content-Disposition": "attachment; filename*=UTF-8''caf%C3%A9.txt"}
 
     assert filename_from_response("https://example.test/file.bin", headers) == "café.txt"
 
 
+def test_filename_from_response_supports_rfc5987_filename_with_language():
+    headers = {
+        "Content-Disposition": "attachment; filename*=UTF-8'en'caf%C3%A9.txt"
+    }
+
+    assert filename_from_response("https://example.test/file.bin", headers) == "café.txt"
+
+
+def test_filename_from_response_falls_back_for_invalid_rfc5987_filename():
+    headers = {"Content-Disposition": "attachment; filename*=NO-SUCH-CHARSET'en'file.txt"}
+
+    assert filename_from_response("https://example.test/fallback.txt", headers) == (
+        "fallback.txt"
+    )
+
+
 def test_sanitize_filename_removes_windows_invalid_characters_and_separators():
     sanitized = sanitize_filename(' report<draft>:"final"/\\*.txt ')
 
     assert sanitized == "report_draft_final_.txt"
     assert "/" not in sanitized
     assert "\\" not in sanitized
 
 
@@ -87,8 +103,39 @@ def test_finalize_part_atomically_moves_completed_file(tmp_path):
     part = part_path(destination)
     part.parent.mkdir(parents=True)
     part.write_bytes(b"complete")
 
     finalize_part(part, destination)
 
     assert destination.read_bytes() == b"complete"
     assert not part.exists()
+
+
+def test_finalize_part_preserves_existing_destination_without_overwrite(tmp_path):
+    destination = tmp_path / "downloads" / "report.zip"
+    part = part_path(destination)
+    part.parent.mkdir(parents=True)
+    destination.write_bytes(b"original")
+    part.write_bytes(b"complete")
+
+    try:
+        finalize_part(part, destination)
+    except FileExistsError as error:
+        assert "destination" in str(error).lower()
+    else:
+        raise AssertionError("finalize_part should reject an existing destination")
+
+    assert destination.read_bytes() == b"original"
+    assert part.read_bytes() == b"complete"
+
+
+def test_finalize_part_replaces_existing_destination_only_when_authorized(tmp_path):
+    destination = tmp_path / "downloads" / "report.zip"
+    part = part_path(destination)
+    part.parent.mkdir(parents=True)
+    destination.write_bytes(b"original")
+    part.write_bytes(b"complete")
+
+    finalize_part(part, destination, overwrite=True)
+
+    assert destination.read_bytes() == b"complete"
+    assert not part.exists()
