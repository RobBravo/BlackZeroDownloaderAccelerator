"""Typed contracts for the BlackZero downloader."""

from .errors import DownloadError
from .models import DownloadOptions, DownloadResult

__all__ = ["DownloadError", "DownloadOptions", "DownloadResult"]
