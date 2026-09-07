### Task 2: Implement safe filename and path handling

**Files:** Create `blackzero/files.py` and `tests/test_files.py` only.

**Interfaces:**
- `default_download_dir() -> Path`.
- `sanitize_filename(candidate: str, fallback: str = "archivo_descargado") -> str`.
- `filename_from_response(url: str, headers: Mapping[str, str]) -> str`.
- `choose_destination(directory: Path, filename: str, overwrite: bool) -> Path`.
- `part_path(destination: Path) -> Path`.
- `finalize_part(part: Path, destination: Path) -> None`.

Write tests first and watch them fail. Cover URL fallback names, `Content-Disposition`, invalid Windows characters, reserved names, path separators, collisions, overwrite, directory creation, and atomic rename. Sanitize names and ensure resolved output stays inside the selected directory. Run `pytest tests/test_files.py -q`. Do not modify other files or delegate.
