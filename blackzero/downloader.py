"""Reliable streamed HTTP downloads with safe temporary files."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlsplit

import requests

from .errors import DownloadError
from .files import (
    choose_destination,
    filename_from_response,
    finalize_part,
    part_path,
)
from .models import DownloadOptions, DownloadResult


_CHUNK_SIZE = 64 * 1024
_MAX_BACKOFF_SECONDS = 30.0


def parse_checksum(value: str | None) -> tuple[str, str] | None:
    """Parse the supported ``sha256:HEX`` checksum syntax."""

    if value is None:
        return None

    algorithm, separator, digest = value.partition(":")
    digest = digest.lower()
    if (
        separator != ":"
        or algorithm.lower() != "sha256"
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("checksum must use sha256:HEX format")
    return "sha256", digest


def _validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise DownloadError("URL must use HTTP or HTTPS and include a hostname", "input")


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 429} or 500 <= status_code <= 599


def _retry_delay(response: requests.Response | None, attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return min(max(float(retry_after), 0.0), _MAX_BACKOFF_SECONDS)
            except ValueError:
                pass
    return min(float(2**attempt), _MAX_BACKOFF_SECONDS)


def _total_size(response: requests.Response, existing_size: int, resumed: bool) -> int | None:
    content_range = response.headers.get("Content-Range")
    if resumed and content_range and "/" in content_range:
        total = content_range.rsplit("/", 1)[1]
        if total.isdigit():
            return int(total)

    content_length = response.headers.get("Content-Length")
    if content_length and content_length.isdigit():
        return existing_size + int(content_length) if resumed else int(content_length)
    return None


def _seed_hasher(part: Path, hasher: hashlib._Hash) -> None:
    with part.open("rb") as stream:
        while chunk := stream.read(_CHUNK_SIZE):
            hasher.update(chunk)


def download(
    url: str,
    options: DownloadOptions,
    progress: Callable[[int, int | None], None] | None = None,
) -> DownloadResult:
    """Download one URL, returning a finalized file or a typed error."""

    _validate_url(url)
    try:
        checksum = parse_checksum(options.checksum)
    except ValueError as error:
        raise DownloadError(str(error), "input", cause=error) from error

    destination: Path | None = None
    temporary: Path | None = None
    completed = False
    fallback_name = options.filename or filename_from_response(url, {})

    try:
        initial_destination = choose_destination(
            options.output_dir, fallback_name, options.overwrite
        )
        initial_part = part_path(initial_destination)
        temporary = initial_part

        with requests.Session() as session:
            for attempt in range(options.retries + 1):
                headers: dict[str, str] = {}
                if options.resume and initial_part.exists():
                    headers["Range"] = f"bytes={initial_part.stat().st_size}-"

                try:
                    with session.get(
                        url,
                        stream=True,
                        headers=headers,
                        timeout=(options.timeout, options.timeout),
                    ) as response:
                        if _is_retryable_status(response.status_code):
                            if attempt < options.retries:
                                time.sleep(_retry_delay(response, attempt))
                                continue
                            raise DownloadError(
                                f"HTTP {response.status_code} while downloading {url}",
                                "http",
                            )

                        if response.status_code >= 400:
                            raise DownloadError(
                                f"HTTP {response.status_code} while downloading {url}",
                                "http",
                            )

                        filename = options.filename or filename_from_response(
                            url, response.headers
                        )
                        destination = choose_destination(
                            options.output_dir, filename, options.overwrite
                        )
                        temporary = part_path(destination)
                        if (
                            "Range" in headers
                            and response.status_code == 206
                            and temporary != initial_part
                        ):
                            if not options.keep_partial:
                                initial_part.unlink(missing_ok=True)
                            initial_part = temporary
                            continue
                        existing_size = temporary.stat().st_size if temporary.exists() else 0
                        resumed = (
                            options.resume
                            and existing_size > 0
                            and response.status_code == 206
                        )
                        if not resumed:
                            existing_size = 0

                        hasher = hashlib.sha256() if checksum else None
                        if resumed and hasher is not None:
                            _seed_hasher(temporary, hasher)

                        total = _total_size(response, existing_size, resumed)
                        written = existing_size
                        mode = "ab" if resumed else "wb"
                        with temporary.open(mode) as stream:
                            for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
                                if not chunk:
                                    continue
                                stream.write(chunk)
                                written += len(chunk)
                                if hasher is not None:
                                    hasher.update(chunk)
                                if progress is not None:
                                    progress(written, total)

                        finalize_part(temporary, destination, options.overwrite)
                        if checksum is not None and hasher is not None:
                            _, expected = checksum
                            if hasher.hexdigest() != expected:
                                destination.unlink(missing_ok=True)
                                raise DownloadError("checksum verification failed", "checksum")

                        completed = True
                        return DownloadResult(
                            url=url,
                            path=destination,
                            bytes_written=written,
                            resumed=resumed,
                            checksum_verified=checksum is not None,
                        )
                except requests.RequestException as error:
                    if attempt < options.retries:
                        time.sleep(_retry_delay(None, attempt))
                        continue
                    raise DownloadError(
                        f"network request failed while downloading {url}",
                        "network",
                        cause=error,
                    ) from error

    except DownloadError:
        raise
    except OSError as error:
        raise DownloadError(
            f"filesystem error while downloading {url}", "filesystem", cause=error
        ) from error
    finally:
        if not completed and not options.keep_partial and temporary is not None:
            temporary.unlink(missing_ok=True)
