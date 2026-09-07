from __future__ import annotations

import io
from pathlib import Path

import pytest

from blackzero.cli import build_parser, main, run_downloads
from blackzero.errors import DownloadError
from blackzero.models import DownloadOptions, DownloadResult


def test_parser_accepts_urls_and_all_options(tmp_path: Path):
    args = build_parser().parse_args(
        [
            "https://example.test/a",
            "https://example.test/b",
            "-o",
            str(tmp_path),
            "--retries",
            "5",
            "--timeout",
            "2.5",
            "--resume",
            "--overwrite",
            "--checksum",
            "sha256:" + "a" * 64,
            "--quiet",
            "--keep-partial",
        ]
    )

    assert args.urls == ["https://example.test/a", "https://example.test/b"]
    assert args.output_dir == tmp_path
    assert args.retries == 5
    assert args.timeout == 2.5
    assert args.resume is True
    assert args.overwrite is True
    assert args.quiet is True
    assert args.keep_partial is True


def test_parser_has_contract_defaults():
    args = build_parser().parse_args(["https://example.test/file"])

    assert args.output_dir is None
    assert args.filename is None
    assert args.retries == 3
    assert args.timeout == 30.0
    assert args.resume is False
    assert args.overwrite is False
    assert args.checksum is None
    assert args.quiet is False
    assert args.keep_partial is False


@pytest.mark.parametrize("option", ["--retries", "--timeout"])
def test_parser_rejects_non_positive_numeric_options(option):
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args(["https://example.test/file", option, "0"])

    assert error.value.code == 2


def test_parser_rejects_filename_for_multiple_urls():
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args(
            ["https://example.test/a", "https://example.test/b", "--filename", "a.bin"]
        )

    assert error.value.code == 2


def test_run_downloads_reports_each_result_and_returns_success(monkeypatch, tmp_path):
    results = iter(
        [
            DownloadResult("https://example.test/a", tmp_path / "a", 3, False, False),
            DownloadResult("https://example.test/b", tmp_path / "b", 4, False, False),
        ]
    )
    seen = []

    def fake_download(url, options, progress=None):
        seen.append((url, options, progress))
        return next(results)

    monkeypatch.setattr("blackzero.cli.download", fake_download)
    stdout, stderr = io.StringIO(), io.StringIO()

    code = run_downloads(
        ["https://example.test/a", "https://example.test/b"],
        DownloadOptions(output_dir=tmp_path),
        stdout,
        stderr,
    )

    assert code == 0
    assert [item[0] for item in seen] == [
        "https://example.test/a",
        "https://example.test/b",
    ]
    assert "a" in stdout.getvalue()
    assert "b" in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_run_downloads_reports_errors_and_returns_failure(monkeypatch, tmp_path):
    def fake_download(url, options, progress=None):
        raise DownloadError("server unavailable", "network")

    monkeypatch.setattr("blackzero.cli.download", fake_download)
    stdout, stderr = io.StringIO(), io.StringIO()

    code = run_downloads(
        ["https://example.test/file"],
        DownloadOptions(output_dir=tmp_path),
        stdout,
        stderr,
    )

    assert code == 1
    assert stdout.getvalue() == ""
    assert "server unavailable" in stderr.getvalue()


def test_quiet_run_suppresses_success_output(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "blackzero.cli.download",
        lambda url, options, progress=None: DownloadResult(
            url, tmp_path / "file", 4, False, False
        ),
    )
    stdout, stderr = io.StringIO(), io.StringIO()

    code = run_downloads(
        ["https://example.test/file"],
        DownloadOptions(output_dir=tmp_path, quiet=True),
        stdout,
        stderr,
    )

    assert code == 0
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""


def test_main_returns_two_for_invalid_cli_input(capsys):
    assert main(["not-a-url"]) == 2
    captured = capsys.readouterr()
    assert "URL" in captured.err or "url" in captured.err


def test_main_prints_version_and_returns_zero(capsys):
    assert main(["--version"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "0.1.0"
