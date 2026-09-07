from pathlib import Path

from blackzero.files import (
    choose_destination,
    default_download_dir,
    filename_from_response,
    finalize_part,
    part_path,
    sanitize_filename,
)


def test_default_download_dir_points_to_downloads():
    assert default_download_dir() == (Path.home() / "Downloads").resolve()


def test_filename_from_response_uses_decoded_url_path_then_fallback():
    assert filename_from_response(
        "https://example.test/files/reporte%20final.pdf?download=1", {}
    ) == "reporte final.pdf"
    assert filename_from_response("https://example.test", {}) == "archivo_descargado"


def test_filename_from_response_prefers_content_disposition_filename():
    headers = {"content-disposition": 'attachment; filename="informe final.pdf"'}

    assert filename_from_response("https://example.test/file.bin", headers) == (
        "informe final.pdf"
    )


def test_filename_from_response_sanitizes_malicious_header_filename():
    headers = {"Content-Disposition": 'attachment; filename="..\\secret/CON.txt"'}

    assert filename_from_response("https://example.test/file.bin", headers) == (
        ".._secret_CON.txt"
    )


def test_filename_from_response_supports_rfc5987_filename():
    headers = {"Content-Disposition": "attachment; filename*=UTF-8''caf%C3%A9.txt"}

    assert filename_from_response("https://example.test/file.bin", headers) == "café.txt"


def test_filename_from_response_supports_rfc5987_filename_with_language():
    headers = {
        "Content-Disposition": "attachment; filename*=UTF-8'en'caf%C3%A9.txt"
    }

    assert filename_from_response("https://example.test/file.bin", headers) == "café.txt"


def test_filename_from_response_falls_back_for_invalid_rfc5987_filename():
    headers = {"Content-Disposition": "attachment; filename*=NO-SUCH-CHARSET'en'file.txt"}

    assert filename_from_response("https://example.test/fallback.txt", headers) == (
        "fallback.txt"
    )


def test_sanitize_filename_removes_windows_invalid_characters_and_separators():
    sanitized = sanitize_filename(' report<draft>:"final"/\\*.txt ')

    assert sanitized == "report_draft_final_.txt"
    assert "/" not in sanitized
    assert "\\" not in sanitized


def test_sanitize_filename_replaces_reserved_names_and_uses_fallback_for_empty_input():
    assert sanitize_filename("CON") == "CON_"
    assert sanitize_filename("aux.txt") == "aux_.txt"
    assert sanitize_filename("...") == "archivo_descargado"
    assert sanitize_filename("   ", fallback="sin_nombre") == "sin_nombre"


def test_choose_destination_creates_directory_and_suffixes_collisions(tmp_path):
    directory = tmp_path / "nested" / "downloads"
    first = choose_destination(directory, "reporte.txt", overwrite=False)
    first.write_text("existing", encoding="utf-8")

    second = choose_destination(directory, "reporte.txt", overwrite=False)

    assert first == directory.resolve() / "reporte.txt"
    assert second == directory.resolve() / "reporte (1).txt"
    assert second.parent == directory.resolve()


def test_choose_destination_overwrite_returns_requested_path(tmp_path):
    destination = choose_destination(tmp_path, "reporte.txt", overwrite=True)
    destination.write_text("old", encoding="utf-8")

    assert choose_destination(tmp_path, "reporte.txt", overwrite=True) == destination


def test_choose_destination_keeps_resolved_output_inside_directory(tmp_path):
    destination = choose_destination(tmp_path / "downloads", "..\\outside.txt", False)

    assert destination.parent == (tmp_path / "downloads").resolve()
    assert destination.is_relative_to((tmp_path / "downloads").resolve())


def test_part_path_adds_part_suffix():
    destination = Path("downloads") / "report.zip"

    assert part_path(destination) == Path("downloads") / "report.zip.part"


def test_finalize_part_atomically_moves_completed_file(tmp_path):
    destination = tmp_path / "downloads" / "report.zip"
    part = part_path(destination)
    part.parent.mkdir(parents=True)
    part.write_bytes(b"complete")

    finalize_part(part, destination)

    assert destination.read_bytes() == b"complete"
    assert not part.exists()


def test_finalize_part_preserves_existing_destination_without_overwrite(tmp_path):
    destination = tmp_path / "downloads" / "report.zip"
    part = part_path(destination)
    part.parent.mkdir(parents=True)
    destination.write_bytes(b"original")
    part.write_bytes(b"complete")

    try:
        finalize_part(part, destination)
    except FileExistsError as error:
        assert "destination" in str(error).lower()
    else:
        raise AssertionError("finalize_part should reject an existing destination")

    assert destination.read_bytes() == b"original"
    assert part.read_bytes() == b"complete"


def test_finalize_part_replaces_existing_destination_only_when_authorized(tmp_path):
    destination = tmp_path / "downloads" / "report.zip"
    part = part_path(destination)
    part.parent.mkdir(parents=True)
    destination.write_bytes(b"original")
    part.write_bytes(b"complete")

    finalize_part(part, destination, overwrite=True)

    assert destination.read_bytes() == b"complete"
    assert not part.exists()
