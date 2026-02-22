from __future__ import annotations

from iso639 import Language


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
    return Language.match(language).part2b
