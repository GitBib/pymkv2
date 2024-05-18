from __future__ import annotations

from iso639 import languages


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
    try:
        languages.get(part2b=language)
        return True  # noqa: TRY300
    except KeyError:
        return False
