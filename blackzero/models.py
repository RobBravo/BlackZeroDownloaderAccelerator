"""Data models shared by the downloader layers."""

from dataclasses import dataclass, field
from pathlib import Path


def _default_output_dir() -> Path:
    return (Path.home() / "Downloads").expanduser().resolve()


def _normalized_path(value: Path) -> Path:
    return Path(value).expanduser().resolve()


@dataclass(frozen=True)
class DownloadOptions:
    output_dir: Path = field(default_factory=_default_output_dir)
    filename: str | None = None
    overwrite: bool = False
    resume: bool = False
    retries: int = 3
    timeout: float = 30.0
    checksum: str | None = None
    quiet: bool = False
    keep_partial: bool = False

    def __post_init__(self) -> None:
        if self.retries <= 0:
            raise ValueError("retries must be positive")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        object.__setattr__(self, "output_dir", _normalized_path(self.output_dir))


@dataclass(frozen=True)
class DownloadResult:
    url: str
    path: Path
    bytes_written: int
    resumed: bool
    checksum_verified: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalized_path(self.path))
