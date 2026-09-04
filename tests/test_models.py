import pytest


def _models():
    try:
        from blackzero.models import DownloadOptions, DownloadResult
    except ModuleNotFoundError as exc:
        pytest.fail(f"model contracts are not implemented: {exc}")
    return DownloadOptions, DownloadResult


def _errors():
    try:
        from blackzero.errors import DownloadError
    except ModuleNotFoundError as exc:
        pytest.fail(f"error contract is not implemented: {exc}")
    return DownloadError


def test_download_options_normalizes_output_path_and_uses_defaults(tmp_path):
    DownloadOptions, _ = _models()

    options = DownloadOptions(output_dir=tmp_path / "nested" / ".." / "downloads")

    assert options.output_dir == (tmp_path / "downloads").resolve()
    assert options.filename is None
    assert options.overwrite is False
    assert options.resume is False
    assert options.retries == 3
    assert options.timeout == 30.0
    assert options.checksum is None
    assert options.quiet is False
    assert options.keep_partial is False


def test_download_options_rejects_non_positive_retries_and_timeout(tmp_path):
    DownloadOptions, _ = _models()

    with pytest.raises(ValueError, match="retries"):
        DownloadOptions(output_dir=tmp_path, retries=0)
    with pytest.raises(ValueError, match="timeout"):
        DownloadOptions(output_dir=tmp_path, timeout=0)


def test_download_result_normalizes_path_and_preserves_transfer_fields(tmp_path):
    _, DownloadResult = _models()

    result = DownloadResult(
        url="https://example.test/file.bin",
        path=tmp_path / "folder" / ".." / "file.bin",
        bytes_written=42,
        resumed=True,
        checksum_verified=True,
    )

    assert result.path == (tmp_path / "file.bin").resolve()
    assert result.url == "https://example.test/file.bin"
    assert result.bytes_written == 42
    assert result.resumed is True
    assert result.checksum_verified is True


def test_download_error_exposes_message_kind_and_cause():
    DownloadError = _errors()
    cause = OSError("connection reset")

    error = DownloadError("download failed", "network", cause=cause)

    assert error.message == "download failed"
    assert error.kind == "network"
    assert error.cause is cause
    assert str(error) == "download failed"
