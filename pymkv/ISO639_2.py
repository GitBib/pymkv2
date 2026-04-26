"""Utilities for resolving ISO 639-2 language codes.

:func:`get_iso639_2` is a lenient resolver that accepts any ISO 639-1 /
639-2 /B / 639-2 /T / 639-3 code or English language name and returns the
canonical ISO 639-2 /B code (or ``None`` if no mapping exists).

The legacy boolean validator :func:`is_iso639_2` is kept as a thin
backwards-compatibility shim and emits :class:`DeprecationWarning`. New code
should use :func:`get_iso639_2`.

Examples
--------
>>> from pymkv.ISO639_2 import get_iso639_2
>>> get_iso639_2("eng")
'eng'
>>> get_iso639_2("English")
'eng'
>>> get_iso639_2("fra")
'fre'
>>> get_iso639_2("xyz") is None
True
"""

from __future__ import annotations

import warnings
from functools import cache

from iso639 import Language, LanguageNotFoundError


def get_iso639_2(language: str | None) -> str | None:
    """Resolve a language identifier to its canonical ISO 639-2 /B code.

    Accepts any ISO 639-1 (``"en"``), 639-2 /B (``"eng"``), 639-2 /T
    (``"fra"`` → ``"fre"``), 639-3 (``"eng"``) code, or English language name
    (``"English"``, ``"english"``). Returns ``None`` for unrecognized input,
    non-string input, empty strings, or for languages that exist only in
    639-3 (e.g. ``"tok"`` / Toki Pona) and therefore have no /B code.

    Parameters
    ----------
    language : str | None
        The language identifier to resolve. ``None``, non-strings (including
        unhashable values such as lists), and empty strings all return
        ``None`` without raising.

    Returns
    -------
    str | None
        The canonical ISO 639-2 /B code, or ``None`` if no mapping exists.

    Examples
    --------
    >>> get_iso639_2("eng")
    'eng'
    >>> get_iso639_2("fra")
    'fre'
    >>> get_iso639_2("English")
    'eng'
    >>> get_iso639_2("tok") is None
    True
    >>> get_iso639_2(None) is None
    True
    """
    # Guard outside @cache so unhashable inputs (e.g. lists) don't raise
    # TypeError when functools tries to compute their hash.
    if not isinstance(language, str) or not language:
        return None
    return _resolve_iso639_2(language)


@cache
def _resolve_iso639_2(language: str) -> str | None:
    # Two paths can return None below:
    # 1. Language.match raises LanguageNotFoundError when the input matches no
    #    639-1/2B/2T/3 code or English name.
    # 2. The match succeeds but the language exists only in 639-3 (e.g. "tok"
    #    / Toki Pona), so its part2b attribute is None.
    try:
        match = Language.match(language, strict_case=False)
    except LanguageNotFoundError:
        return None
    return match.part2b


def is_iso639_2(language: str) -> bool:
    """Check whether a language code is a valid ISO 639-2 identifier.

    .. deprecated::
        Use :func:`get_iso639_2` instead. This wrapper will be removed in a
        future minor release. It accepts any input :func:`get_iso639_2`
        accepts (codes and names), not just /B codes, and returns ``True`` if
        a /B mapping exists.

    Parameters
    ----------
    language : str
        The language identifier to check.

    Returns
    -------
    bool
        ``True`` if the input maps to an ISO 639-2 /B code, ``False`` otherwise.
    """
    warnings.warn(
        "is_iso639_2 is deprecated; use pymkv.get_iso639_2 instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_iso639_2(language) is not None
