from __future__ import annotations

import importlib

# package imports
from .MKVAttachment import MKVAttachment
from .MKVFile import MKVFile
from .MKVTrack import MKVTrack
from .Timestamp import Timestamp
from .Verifications import (
    checking_file_path,
    get_file_info,
    verify_matroska,
    verify_mkvmerge,
    verify_recognized,
    verify_supported,
)

# set the version number within the package using importlib
try:
    __version__: str | None = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    # package is not installed
    __version__ = None

__all__ = (
    "MKVAttachment",
    "MKVFile",
    "MKVTrack",
    "Timestamp",
    "verify_matroska",
    "verify_mkvmerge",
    "verify_recognized",
    "verify_supported",
    "checking_file_path",
    "get_file_info",
)
