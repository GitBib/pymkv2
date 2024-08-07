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
    try:
        Language.from_part2b(language)
        return True  # noqa: TRY300
    except LanguageNotFoundError:
        return False
