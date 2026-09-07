"""Command-line interface for BlackZero."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from tqdm import tqdm

from .downloader import download
from .errors import DownloadError
from .files import default_download_dir
from .models import DownloadOptions

_VERSION = "0.1.0"


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive number")
    return number


class _BlackZeroParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None):
        parsed = super().parse_args(args, namespace)
        if parsed.filename is not None and len(parsed.urls) != 1:
            self.error("--filename can only be used with one URL")
        return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = _BlackZeroParser(
        prog="blackzero",
        description="Download files over HTTP or HTTPS.",
    )
    parser.add_argument("urls", nargs="+", help="one or more HTTP/HTTPS URLs")
    parser.add_argument("-o", "--output-dir", type=Path, default=None, metavar="PATH")
    parser.add_argument("-n", "--filename", metavar="NAME")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retries", type=_positive_int, default=3, metavar="N")
    parser.add_argument("--timeout", type=_positive_float, default=30.0, metavar="SECONDS")
    parser.add_argument("--checksum", metavar="sha256:HEX")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("--keep-partial", action="store_true")
    parser.add_argument("--version", action="version", version=_VERSION)
    return parser


def _progress_callback(stdout: TextIO):
    bar = None

    def update(written: int, total: int | None) -> None:
        nonlocal bar
        if bar is None:
            bar = tqdm(total=total, unit="B", unit_scale=True, file=stdout)
        if written > bar.n:
            bar.update(written - bar.n)

    def close() -> None:
        if bar is not None:
            bar.close()

    return update, close


def run_downloads(
    urls: Sequence[str],
    options: DownloadOptions,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Download URLs sequentially and render results to the supplied streams."""

    failed = False
    invalid_input = False
    show_progress = not options.quiet and bool(getattr(stdout, "isatty", lambda: False)())
    for url in urls:
        callback = closer = None
        if show_progress:
            callback, closer = _progress_callback(stdout)
        try:
            result = download(url, options, progress=callback)
        except DownloadError as error:
            failed = True
            invalid_input = invalid_input or error.kind == "input"
            print(f"❌ {url}: {error.message}", file=stderr)
        else:
            if not options.quiet:
                print(
                    f"✅ {url} -> {result.path} ({result.bytes_written} bytes)",
                    file=stdout,
                )
        finally:
            if closer is not None:
                closer()
    if invalid_input:
        return 2
    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code)

    options = DownloadOptions(
        output_dir=args.output_dir or default_download_dir(),
        filename=args.filename,
        overwrite=args.overwrite,
        resume=args.resume,
        retries=args.retries,
        timeout=args.timeout,
        checksum=args.checksum,
        quiet=args.quiet,
        keep_partial=args.keep_partial,
    )
    return run_downloads(args.urls, options, sys.stdout, sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
