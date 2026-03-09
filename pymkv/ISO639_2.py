"""Utilities for working with ISO 639-2 language codes.

Examples
--------
>>> from pymkv.ISO639_2 import get_iso639_2  # doctest: +SKIP
>>> get_iso639_2("eng")  # doctest: +SKIP
'eng'
>>> get_iso639_2("English")  # doctest: +SKIP
'eng'
>>> get_iso639_2("xyz")  # doctest: +SKIP
None
"""

from __future__ import annotations

from functools import cache

from iso639 import Language, LanguageNotFoundError


@cache
def get_iso639_2(language: str) -> str | None:
    """
    Get the ISO 639-2 code for a given language.

    Parameters
    ----------
    language : str
        The language code or name to check for ISO 639-2 compatibility.

    Returns
    -------
    str | None
        The ISO 639-2 (bibliographic) code if the language is recognized,
        None otherwise.
    """
    if not isinstance(language, str):
        return None

    try:
        return Language.match(language, strict_case=False).part2b
    except LanguageNotFoundError:
        return None
