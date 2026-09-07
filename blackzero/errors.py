"""Typed errors shared by the downloader layers."""

from dataclasses import dataclass


@dataclass
class DownloadError(Exception):
    """An error raised while validating or downloading a file."""

    message: str
    kind: str
    cause: BaseException | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)
