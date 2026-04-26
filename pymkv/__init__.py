from __future__ import annotations

import importlib.metadata

# package imports
from .ISO639_2 import get_iso639_2
from .Languages import (
    is_known_language,
    language_equivalents,
    languages_match,
    normalize_language,
    preload_language_table,
)
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
    __version__: str | None = importlib.metadata.version("pymkv2")
except importlib.metadata.PackageNotFoundError:
    # package is not installed
    __version__ = None

__all__ = (
    "MKVAttachment",
    "MKVFile",
    "MKVTrack",
    "Timestamp",
    "checking_file_path",
    "get_file_info",
    "get_iso639_2",
    "is_known_language",
    "language_equivalents",
    "languages_match",
    "normalize_language",
    "preload_language_table",
    "verify_matroska",
    "verify_mkvmerge",
    "verify_recognized",
    "verify_supported",
)
