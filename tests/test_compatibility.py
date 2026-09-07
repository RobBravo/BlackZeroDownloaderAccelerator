from __future__ import annotations

import runpy
import sys


def test_launcher_prompts_only_when_no_url_arguments(monkeypatch):
    calls = []
    monkeypatch.setattr("builtins.input", lambda prompt: (calls.append(prompt), "https://example.test/file")[1])
    monkeypatch.setattr("blackzero.cli.main", lambda args: calls.append(args) or 7)
    monkeypatch.setattr(sys, "argv", ["DownloadFiles.py"])

    try:
        runpy.run_path("DownloadFiles.py", run_name="__main__")
    except SystemExit as error:
        assert error.code == 7

    assert calls[0].startswith("🔗")
    assert calls[1] == ["https://example.test/file"]


def test_launcher_delegates_url_arguments_without_prompt(monkeypatch):
    calls = []
    monkeypatch.setattr("builtins.input", lambda prompt: (_ for _ in ()).throw(AssertionError()))
    monkeypatch.setattr("blackzero.cli.main", lambda args: calls.append(args) or 0)
    monkeypatch.setattr(sys, "argv", ["DownloadFiles.py", "https://example.test/file"])

    try:
        runpy.run_path("DownloadFiles.py", run_name="__main__")
    except SystemExit as error:
        assert error.code == 0

    assert calls == [["https://example.test/file"]]
