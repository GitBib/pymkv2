"""Utilities for checking ISO 639-2 language code compliance.

Examples
--------
>>> from pymkv.ISO639_2 import is_iso639_2  # doctest: +SKIP
>>> is_iso639_2('eng')  # doctest: +SKIP
True
"""

from __future__ import annotations

from iso639 import Language, LanguageNotFoundError


def is_iso639_2(language: str) -> bool:
    """
    Parameters
    ----------
    language : str
        The language code to check for ISO 639-2 compatibility.

    Returns
    -------
    bool
        True if the language code is valid according to ISO 639-2, False otherwise.
    """
    if not isinstance(language, str):
        return False

    try:
        Language.from_part2b(language)
        return True  # noqa: TRY300
    except LanguageNotFoundError:
        return False
