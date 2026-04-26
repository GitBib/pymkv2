"""Cross-format language code utilities for pymkv.

This module is the home of the public API for comparing and normalizing
language codes across the formats mkvmerge accepts: ISO 639-1 (``"en"``),
ISO 639-2 /B (``"eng"``), ISO 639-2 /T (``"fra"``), ISO 639-3 (``"eng"``)
and BCP 47 tags with optional script/region subtags (``"zh-Hans-CN"``).

It is the companion to :mod:`pymkv.ISO639_2`'s :func:`get_iso639_2` resolver.
Where :func:`get_iso639_2` only handles the ISO 639 family, the helpers in
this module additionally understand BCP 47 subtags, the ``"und"`` undefined
sentinel, and consult ``mkvmerge --list-languages`` so that pymkv stays
authoritative about exactly the codes mkvmerge will accept on the wire.

Public functions
----------------
- :func:`normalize_language` — any code/name/BCP 47 tag → canonical /B (or ``None``)
- :func:`is_known_language` — is the tag one mkvmerge or python-iso639 recognizes?
- :func:`language_equivalents` — every known code for the same language as a ``frozenset``
- :func:`languages_match` — equality across formats and BCP 47 subtags
- :func:`preload_language_table` — pre-warm the mkvmerge subprocess cache

Data sources
------------
1. ``mkvmerge --list-languages`` (lazily loaded once per process via
   :func:`_load_mkvmerge_table`, cached with :func:`functools.cache`) —
   authoritative for "what mkvmerge will accept".
2. ``python-iso639`` (already a pymkv dependency) — covers /T-variant codes
   (``zho`` → ``chi``, ``deu`` → ``ger``, ``fra`` → ``fre``) that mkvmerge does
   not emit, plus English language names.

There are deliberately **no hardcoded language tables** in this module.

Examples
--------
>>> from pymkv.Languages import normalize_language, languages_match
>>> callable(normalize_language)
True
>>> callable(languages_match)
True
"""

from __future__ import annotations

import functools
import re
import subprocess
import warnings
from typing import NamedTuple

from iso639 import Language, LanguageNotFoundError

from pymkv.ISO639_2 import get_iso639_2

# BCP 47 / mkvmerge "undefined" sentinel — explicitly mapped to "no language".
_UND_SENTINEL = "und"

# Structural BCP 47 well-formedness check (RFC 5646 §2.1 minus grandfathered
# and private-use-only tags, which mkvmerge's parser also handles separately).
# Enforces subtag *shape* and *order*: primary language → script → region →
# variants → extensions → private-use. Singleton extensions must carry at
# least one 2-8 alnum subtag, and ``-x-…`` private-use must carry at least
# one 1-8 alnum subtag. mkvmerge's ``--language`` rejects malformed tags such
# as ``en-a`` (singleton with no content), ``en-x`` (private-use with no
# content), and ``en-US-Latn`` (script after region) on the wire, so this
# regex keeps the read-side (``effective_language``) and write-side
# (``TrackOptions``) gates in agreement with what mkvmerge will actually
# accept.
_BCP47_WELL_FORMED = re.compile(
    r"^"
    # Primary language: 2-3 letters with up to 3 extlang subtags, OR a 4-8
    # letter reserved/registered language tag.
    r"(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}|[A-Za-z]{4,8})"
    # Optional script subtag (4 letters).
    r"(?:-[A-Za-z]{4})?"
    # Optional region subtag (2 letters or 3 digits).
    r"(?:-(?:[A-Za-z]{2}|[0-9]{3}))?"
    # Optional variants (5-8 alnum, or digit + 3 alnum).
    r"(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*"
    # Optional extensions: singleton (alnum except ``x``/``X``) followed by
    # one or more 2-8 alnum subtags.
    r"(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*"
    # Optional private-use: literal ``x``/``X`` followed by one or more 1-8
    # alnum subtags.
    r"(?:-[Xx](?:-[A-Za-z0-9]{1,8})+)?"
    r"$"
)


class _LangRow(NamedTuple):
    """One language row parsed from ``mkvmerge --list-languages``.

    ``siblings`` holds every non-empty code from the row (639-3, /B, 639-1).
    ``b_code`` is the value of the row's ``ISO 639-2`` column or ``None`` when
    that column is empty (e.g. 639-3-only languages such as Toki Pona). The
    distinction matters because the parsed sibling set alone cannot tell a
    /B-bearing collective code (``afa``) from a 639-3-only code (``aaa``).
    """

    siblings: frozenset[str]
    b_code: str | None


@functools.lru_cache(maxsize=32)
def _load_mkvmerge_table(mkvmerge_path: tuple[str, ...] = ("mkvmerge",)) -> dict[str, _LangRow]:
    """Load and parse ``mkvmerge --list-languages`` into a lookup dict.

    Each language row in the mkvmerge output produces a :class:`_LangRow` whose
    ``siblings`` is the frozenset of every non-empty code for that language
    (English name dropped) and whose ``b_code`` is the row's ISO 639-2 column
    when populated. The returned dict maps every individual code back to the
    same row so any code can find its siblings in O(1).

    Cached with :func:`functools.lru_cache` (maxsize=32) keyed on
    ``mkvmerge_path``: the first call for each distinct binary invokes
    ``mkvmerge``, subsequent calls with the same path return from memory.
    The bound prevents unbounded growth if a long-running service feeds many
    distinct paths through this helper. This lets callers that configure a
    custom :attr:`MKVFile.mkvmerge_path` / :attr:`MKVTrack.mkvmerge_path`
    consult their own binary instead of whatever happens to be on ``$PATH``.

    Parameters
    ----------
    mkvmerge_path : tuple[str, ...], optional
        Tuple form of the mkvmerge invocation, as produced by
        :func:`pymkv.utils.prepare_mkvtoolnix_path`. Defaults to plain
        ``("mkvmerge",)`` so direct callers (e.g. tests) get the same behavior
        as before.

    Returns
    -------
    dict[str, _LangRow]
        Mapping from any known code to the parsed row for the same language.
        Empty dict on any failure (mkvmerge missing, returns garbage, or fails
        to execute) — never raises.
    """
    cmd = [*mkvmerge_path, "--list-languages"]
    try:
        raw = subprocess.check_output(  # noqa: S603
            cmd,
            text=True,
            # mkvmerge emits UTF-8 regardless of host locale; force the
            # decoder so Windows defaults (cp1252) don't choke on non-ASCII
            # language names. errors="replace" guards against any stray byte.
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        UnicodeDecodeError,
        OSError,
    ) as exc:
        warnings.warn(
            f"Could not invoke '{' '.join(cmd)}' ({exc!r}); falling back to python-iso639 only.",
            stacklevel=2,
        )
        return {}

    # Header columns: 0=English name, 1=ISO 639-3, 2=ISO 639-2 /B, 3=ISO 639-1.
    table: dict[str, _LangRow] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if "|" not in line:
            continue
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 4:  # noqa: PLR2004 — table layout (see comment above)
            continue
        # Skip the header row and the '----+----+----+----' separator.
        if cells[0] == "English language name":
            continue
        if cells[0] and set(cells[0]) <= {"-"}:
            continue
        iso_639_2 = cells[2]
        codes = frozenset(c for c in (cells[1], iso_639_2, cells[3]) if c)
        if not codes:
            continue
        row = _LangRow(siblings=codes, b_code=iso_639_2 or None)
        for code in codes:
            table[code] = row

    if not table:
        warnings.warn(
            "'mkvmerge --list-languages' returned no parseable rows; falling back to python-iso639 only.",
            stacklevel=2,
        )
    return table


def _resolve_mkvmerge_table(mkvmerge_path: tuple[str, ...] | None) -> dict[str, _LangRow]:
    """Return the cached mkvmerge table for ``mkvmerge_path`` (or the default).

    Centralizes the ``None`` → default-path normalization so every public
    helper consults the same cache key when callers omit the argument.
    """
    if mkvmerge_path is None:
        return _load_mkvmerge_table()
    return _load_mkvmerge_table(mkvmerge_path)


def preload_language_table(mkvmerge_path: tuple[str, ...] | None = None) -> None:
    """Pre-warm the mkvmerge language table cache.

    The first call to any of :func:`normalize_language`,
    :func:`is_known_language`, :func:`language_equivalents`, or
    :func:`languages_match` triggers ``mkvmerge --list-languages`` (~100-200ms).
    Call this helper at startup if you want to absorb that cost up-front rather
    than during the first lookup in a hot loop.

    Parameters
    ----------
    mkvmerge_path : tuple[str, ...], optional
        Tuple form of the mkvmerge invocation. Defaults to plain ``"mkvmerge"``
        from ``$PATH``. Pass a custom path to warm the cache for a non-default
        binary.
    """
    _resolve_mkvmerge_table(mkvmerge_path)


def _strip_bcp47_subtags(code: str) -> str | None:
    """Return primary subtag for lookup, or ``None`` for malformed/empty input.

    Inputs without a hyphen are returned lowercased and stripped — they're
    treated as plain codes or English language names by the caller. Inputs
    that contain a hyphen must be well-formed BCP 47; otherwise this returns
    ``None``. This rejects malformed tags (``"en--US"``) and language names
    that happen to contain a hyphen (``"Pa-O"``) before they get split-and-
    lookup'd against ``"pa"`` (Punjabi) — :func:`normalize_language` would
    otherwise resolve them to a wildly wrong code.
    """
    stripped = code.strip()
    if not stripped:
        return None
    if "-" in stripped and not _BCP47_WELL_FORMED.fullmatch(stripped):
        return None
    return stripped.split("-", 1)[0].lower()


def normalize_language(code: str | None, mkvmerge_path: tuple[str, ...] | None = None) -> str | None:
    """Normalize a language identifier to its canonical ISO 639-2 /B code.

    Strips BCP 47 subtags before lookup (``"zh-Hans-CN"`` → ``"chi"``) and
    treats ``None``, the empty string, and ``"und"`` (the BCP 47 / mkvmerge
    "undefined" sentinel) as "no language" by returning ``None``.

    Resolution order:

    1. :func:`_load_mkvmerge_table` lookup (authoritative for mkvmerge).
    2. :func:`pymkv.ISO639_2.get_iso639_2` (covers /T → /B and English names).
    3. ``None``.

    Parameters
    ----------
    code : str | None
        Any 639-1/2/B/2/T/3 code, English language name, or BCP 47 tag.
        ``None``, ``""``, ``"und"`` and unrecognized input return ``None``.
    mkvmerge_path : tuple[str, ...], optional
        Tuple form of the mkvmerge invocation (as produced by
        :func:`pymkv.utils.prepare_mkvtoolnix_path`) used to load the
        authoritative language table. Defaults to plain ``"mkvmerge"`` from
        ``$PATH``. Pass :attr:`MKVFile.mkvmerge_path` /
        :attr:`MKVTrack.mkvmerge_path` to honor a per-object override.

    Returns
    -------
    str | None
        Canonical ISO 639-2 /B code, or ``None``.
    """
    if not isinstance(code, str):
        return None
    primary = _strip_bcp47_subtags(code)
    if primary is None or primary == _UND_SENTINEL:
        return None

    row = _resolve_mkvmerge_table(mkvmerge_path).get(primary)
    if row is not None:
        # Sort siblings so the chosen resolution is deterministic across
        # runs (frozenset iteration order varies with the Python hash seed).
        for candidate in sorted(row.siblings):
            resolved = get_iso639_2(candidate)
            if resolved is not None:
                return resolved
        # python-iso639 doesn't recognize this code, but mkvmerge does.
        # If the row carries a /B column value (true for collective ISO 639-5
        # codes like ``afa``/``alg``), return it. Rows with no /B column —
        # 639-3-only languages such as Toki Pona (``tok``) or Ghotuo
        # (``aaa``) — fall through and return ``None``, preserving the
        # documented "Canonical ISO 639-2 /B code" contract.
        if row.b_code is not None:
            return row.b_code

    return get_iso639_2(primary)


def is_known_language(code: str | None, mkvmerge_path: tuple[str, ...] | None = None) -> bool:
    """Return ``True`` when ``code`` is a tag mkvmerge or python-iso639 recognizes.

    Strips BCP 47 subtags before lookup. Differs from
    :func:`normalize_language` by recognizing 639-3-only languages such as
    Toki Pona (``"tok"``) and Ghotuo (``"aaa"``) — mkvmerge accepts these
    even though they have no /B form, so :func:`normalize_language` returns
    ``None`` for them. Use this predicate when you need to gate on "would
    mkvmerge accept this tag" rather than "does it normalize to /B".

    The BCP 47 ``"und"`` sentinel is treated as recognized: mkvmerge
    accepts it as the explicit "undefined language" marker.

    Parameters
    ----------
    code : str | None
        Any 639-1/2/B/2/T/3 code, English language name, or BCP 47 tag.
    mkvmerge_path : tuple[str, ...], optional
        Tuple form of the mkvmerge invocation (as produced by
        :func:`pymkv.utils.prepare_mkvtoolnix_path`). Defaults to plain
        ``"mkvmerge"`` from ``$PATH``. Pass :attr:`MKVFile.mkvmerge_path` /
        :attr:`MKVTrack.mkvmerge_path` to honor a per-object override.

    Returns
    -------
    bool
        ``True`` if the input is well-formed BCP 47 *and* the primary subtag
        appears in the mkvmerge table or is recognized by python-iso639.
        ``False`` for ``None``, non-strings, empty strings, malformed BCP 47
        (whitespace, consecutive hyphens, empty subtags), and unrecognized
        input.
    """
    if not isinstance(code, str):
        return False
    # Reject malformed BCP 47 input *before* primary-subtag extraction — a
    # well-formed primary alone is not enough because the writer emits the
    # original tag verbatim. ``" en-US "`` and ``"en--US"`` would otherwise
    # slip past while their primary (``"en"``) resolves cleanly.
    if not _BCP47_WELL_FORMED.fullmatch(code):
        return False
    primary = code.split("-", 1)[0].lower()
    if primary == _UND_SENTINEL:
        return True
    if primary in _resolve_mkvmerge_table(mkvmerge_path):
        return True
    try:
        lang = Language.match(primary, strict_case=False)
    except LanguageNotFoundError:
        return False
    # ``Language.match`` also resolves English names (``"English"`` →
    # ``part1="en"``). mkvmerge's ``--language`` rejects language names, so
    # this gate must accept the lookup only when ``primary`` is itself one
    # of the recognized ISO 639 codes for the resolved language.
    return primary in {lang.part1, lang.part2b, lang.part2t, lang.part3}


def language_equivalents(code: str | None, mkvmerge_path: tuple[str, ...] | None = None) -> frozenset[str]:
    """Return every known code for the same language as ``code``.

    Merges results from both data sources (mkvmerge frozenset and python-iso639
    attributes) into a single frozenset. Includes 639-1, 639-2 /B, 639-2 /T and
    639-3 codes when known. BCP 47 subtags on the input are stripped before
    lookup so ``"zh-Hans-CN"`` resolves to the same set as ``"chi"``.

    Parameters
    ----------
    code : str | None
        A language identifier.
    mkvmerge_path : tuple[str, ...], optional
        Tuple form of the mkvmerge invocation. Defaults to plain ``"mkvmerge"``
        from ``$PATH``. Pass a custom path to consult a non-default binary.

    Returns
    -------
    frozenset[str]
        All equivalent codes. Empty frozenset for ``None``, ``""``, ``"und"``,
        and malformed BCP 47 input (``"en--US"``, names containing hyphens
        such as ``"Pa-O"``). For an unrecognized but well-formed string,
        returns a frozenset containing only the lower-cased primary subtag.
    """
    if not isinstance(code, str):
        return frozenset()
    primary = _strip_bcp47_subtags(code)
    if primary is None or primary == _UND_SENTINEL:
        return frozenset()

    result: set[str] = set()

    table = _resolve_mkvmerge_table(mkvmerge_path)
    row = table.get(primary)
    if row is not None:
        result.update(row.siblings)

    try:
        lang = Language.match(primary, strict_case=False)
    except LanguageNotFoundError:
        lang = None
    if lang is not None:
        for attr in (lang.part1, lang.part2b, lang.part2t, lang.part3):
            if attr:
                result.add(attr)
        # python-iso639 may have known the language under a /T code; once we
        # know its /B form, expand the mkvmerge lookup to that key as well.
        if lang.part2b and lang.part2b != primary:
            extra = table.get(lang.part2b)
            if extra is not None:
                result.update(extra.siblings)

    if not result:
        return frozenset({primary})
    return frozenset(result)


def _canonical_key(code: str | None, mkvmerge_path: tuple[str, ...] | None) -> str | None:
    """Return a stable cross-format identifier for the language of ``code``.

    Prefers the canonical /B code from :func:`normalize_language`. Falls back
    to the row's 639-3 sibling when the mkvmerge table accepts the tag but
    has no /B form (e.g. Toki Pona ``"tok"``, Ghotuo ``"aaa"``) — this lets
    :func:`languages_match` recognize 639-3-only codes that the writer in
    :mod:`pymkv.command_generators.track_options` already emits to mkvmerge.

    Falls back further to ``python-iso639`` for inputs that are absent from
    the mkvmerge table — covers English language names that resolve to a
    639-3-only language (``"Toki Pona"`` → ``"tok"``, ``"Ghotuo"`` →
    ``"aaa"``). Without this branch, :func:`language_equivalents` would
    produce ``frozenset({"tok"})`` for ``"Toki Pona"`` while
    :func:`languages_match` returned ``False`` for the same comparison.

    Returns ``None`` for unrecognized input, ``None``/``""``/``"und"``, and
    rows that are absent from both data sources.
    """
    canonical = normalize_language(code, mkvmerge_path)
    if canonical is not None:
        return canonical
    if not isinstance(code, str):
        return None
    primary = _strip_bcp47_subtags(code)
    if primary is None or primary == _UND_SENTINEL:
        return None
    row = _resolve_mkvmerge_table(mkvmerge_path).get(primary)
    if row is not None:
        # Row exists but has no /B form (otherwise normalize_language would
        # have returned it). For mkvmerge's /B-less rows the only sibling is
        # the 639-3 code itself; pick deterministically via ``min`` so the
        # key is stable regardless of frozenset iteration order.
        return min(row.siblings)
    # Last resort: ask python-iso639. This catches English names that resolve
    # to a /B-less language (``part2b`` is ``None`` so ``normalize_language``
    # returned ``None``); ``part3`` is the same key the mkvmerge-table branch
    # produces when the 639-3 code itself is passed in.
    try:
        lang = Language.match(primary, strict_case=False)
    except LanguageNotFoundError:
        return None
    return lang.part2b or lang.part3 or None


def languages_match(a: str | None, b: str | None, mkvmerge_path: tuple[str, ...] | None = None) -> bool:
    """Return ``True`` when ``a`` and ``b`` refer to the same language.

    Equality is computed across all formats this module understands, including
    BCP 47 subtags, so e.g. ``languages_match("chi", "zh-Hans") is True``.
    639-3-only codes mkvmerge accepts (``"tok"``, ``"aaa"``) compare equal to
    themselves even though they have no canonical /B form.

    Either side being ``None``, ``""`` or ``"und"`` always returns ``False`` —
    "unknown matches unknown" is not useful in the contexts this API was
    designed for (track filtering, "is this the original-language audio?"
    questions).

    Parameters
    ----------
    a, b : str | None
        Language identifiers to compare.
    mkvmerge_path : tuple[str, ...], optional
        Tuple form of the mkvmerge invocation. Defaults to plain ``"mkvmerge"``
        from ``$PATH``.

    Returns
    -------
    bool
        ``True`` if both inputs resolve to the same canonical key.
    """
    key_a = _canonical_key(a, mkvmerge_path)
    if key_a is None:
        return False
    return key_a == _canonical_key(b, mkvmerge_path)
