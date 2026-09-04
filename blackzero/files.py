"""Safe filename, destination, and temporary-file helpers."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping
from urllib.parse import unquote, urlsplit


_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]+')
_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def default_download_dir() -> Path:
    """Return the current user's platform-default Downloads directory."""

    return (Path.home() / "Downloads").expanduser().resolve()


def _fallback_name(fallback: str) -> str:
    cleaned = _sanitize_candidate(fallback)
    return cleaned or "archivo_descargado"


def _sanitize_candidate(candidate: str) -> str:
    cleaned = _INVALID_FILENAME_CHARS.sub("_", str(candidate)).strip()
    cleaned = re.sub(r"_+", "_", cleaned).rstrip(" .")
    if not cleaned:
        return ""

    stem = cleaned.split(".", 1)[0]
    if stem.upper() in _RESERVED_NAMES:
        cleaned = f"{stem}_{cleaned[len(stem):]}"
    return cleaned


def sanitize_filename(candidate: str, fallback: str = "archivo_descargado") -> str:
    """Return a filesystem-safe single filename, never a path."""

    cleaned = _sanitize_candidate(candidate)
    return cleaned or _fallback_name(fallback)


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    name = name.casefold()
    for key, value in headers.items():
        if key.casefold() == name:
            return value
    return None


def _content_disposition_filename(value: str) -> str | None:
    extended = re.search(r"(?:^|;)\s*filename\*\s*=\s*([^;]+)", value, re.I)
    if extended:
        encoded = extended.group(1).strip().strip('"')
        _, separator, payload = encoded.partition("''")
        return unquote(payload if separator else encoded)

    regular = re.search(
        r'(?:^|;)\s*filename\s*=\s*(?:"([^"]*)"|([^;]*))', value, re.I
    )
    if regular:
        return (regular.group(1) or regular.group(2)).strip()
    return None


def filename_from_response(url: str, headers: Mapping[str, str]) -> str:
    """Choose and sanitize a filename from response headers or the URL."""

    disposition = _header_value(headers, "Content-Disposition")
    if disposition:
        filename = _content_disposition_filename(disposition)
        if filename:
            return sanitize_filename(filename)

    path = urlsplit(url).path
    url_name = unquote(path.rsplit("/", 1)[-1]) if path else ""
    return sanitize_filename(url_name)


def choose_destination(directory: Path, filename: str, overwrite: bool) -> Path:
    """Create the output directory and select a collision-safe destination."""

    root = Path(directory).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(filename)
    destination = (root / safe_name).resolve()
    if not destination.is_relative_to(root):
        raise ValueError("destination must remain inside the output directory")
    if overwrite or not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    counter = 1
    while True:
        candidate = (root / f"{stem} ({counter}){suffix}").resolve()
        if not candidate.exists():
            return candidate
        counter += 1


def part_path(destination: Path) -> Path:
    """Return the temporary path used while writing a destination."""

    destination = Path(destination)
    return destination.with_name(f"{destination.name}.part")


def finalize_part(part: Path, destination: Path) -> None:
    """Atomically move a completed temporary file to its final destination."""

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(Path(part), destination)
