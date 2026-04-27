"""Tests for :mod:`pymkv.Languages`."""

from __future__ import annotations

import subprocess
from collections.abc import Iterator

import pytest

import pymkv
from pymkv import Languages
from pymkv.ISO639_2 import get_iso639_2

SYNTHETIC_TABLE = """\
English language name                                      | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code
-----------------------------------------------------------+----------------+----------------+---------------
Chinese                                                    | chi            | chi            | zh
English                                                    | eng            | eng            | en
Japanese                                                   | jpn            | jpn            | ja
Filipino                                                   | fil            | fil            |
Undetermined                                               | und            | und            |

"""


def test_languages_module_exports_public_api() -> None:
    for name in (
        "_load_mkvmerge_table",
        "is_known_language",
        "normalize_language",
        "language_equivalents",
        "languages_match",
    ):
        assert callable(getattr(Languages, name)), f"{name} missing or not callable"


def test_pymkv_reexports_language_helpers() -> None:
    assert pymkv.normalize_language is Languages.normalize_language
    assert pymkv.is_known_language is Languages.is_known_language
    assert pymkv.language_equivalents is Languages.language_equivalents
    assert pymkv.languages_match is Languages.languages_match


def test_pymkv_reexports_get_iso639_2() -> None:
    assert pymkv.get_iso639_2 is get_iso639_2


def test_all_includes_new_symbols() -> None:
    for name in (
        "get_iso639_2",
        "is_known_language",
        "language_equivalents",
        "languages_match",
        "normalize_language",
    ):
        assert name in pymkv.__all__, f"{name} missing from pymkv.__all__"


@pytest.fixture(autouse=True)
def _clear_mkvmerge_table_cache() -> Iterator[None]:
    """Reset the in-memory mkvmerge table before *and* after every test.

    Without the teardown clear, the last patched test in the module poisons
    the cache for any later consumer in the suite that hits the real lookup.
    """
    Languages._load_mkvmerge_table.cache_clear()  # noqa: SLF001
    yield
    Languages._load_mkvmerge_table.cache_clear()  # noqa: SLF001


def test_load_mkvmerge_table_parses_synthetic_output(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_check_output(*args: object, **kwargs: object) -> str:
        calls.append((args, kwargs))
        return SYNTHETIC_TABLE

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert calls, "mkvmerge subprocess should be invoked on the first call"
    invoked_args, invoked_kwargs = calls[0]
    assert invoked_args[0] == ["mkvmerge", "--list-languages"]
    assert invoked_kwargs.get("text") is True
    assert invoked_kwargs.get("stderr") is subprocess.DEVNULL

    chinese = frozenset({"chi", "zh"})
    english = frozenset({"eng", "en"})
    japanese = frozenset({"jpn", "ja"})
    filipino = frozenset({"fil"})
    undetermined = frozenset({"und"})

    assert table["chi"].siblings == chinese
    assert table["zh"].siblings == chinese
    assert table["eng"].siblings == english
    assert table["en"].siblings == english
    assert table["jpn"].siblings == japanese
    assert table["ja"].siblings == japanese
    assert table["fil"].siblings == filipino
    assert table["und"].siblings == undetermined

    assert table["chi"].b_code == "chi"
    assert table["en"].b_code == "eng"
    assert table["fil"].b_code == "fil"

    assert "Chinese" not in table
    assert "English language name" not in table


def test_load_mkvmerge_table_caches_result(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"n": 0}

    def fake_check_output(*_args: object, **_kwargs: object) -> str:
        call_count["n"] += 1
        return SYNTHETIC_TABLE

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    first = Languages._load_mkvmerge_table()  # noqa: SLF001
    second = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert call_count["n"] == 1, "second call must hit the cache, not subprocess"
    assert first is second, "cached call must return the exact same dict object"


def test_load_mkvmerge_table_handles_missing_mkvmerge(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_check_output(*_args: object, **_kwargs: object) -> str:
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    with pytest.warns(UserWarning, match="mkvmerge"):
        table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert table == {}


def test_load_mkvmerge_table_handles_called_process_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_check_output(*_args: object, **_kwargs: object) -> str:
        raise subprocess.CalledProcessError(1, ["mkvmerge", "--list-languages"])

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    with pytest.warns(UserWarning, match="mkvmerge"):
        table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert table == {}


def test_load_mkvmerge_table_handles_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_check_output(*_args: object, **_kwargs: object) -> str:
        raise PermissionError

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    with pytest.warns(UserWarning, match="mkvmerge"):
        table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert table == {}


def test_load_mkvmerge_table_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_check_output(*_args: object, **_kwargs: object) -> str:
        raise subprocess.TimeoutExpired(["mkvmerge", "--list-languages"], 10)

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    with pytest.warns(UserWarning, match="mkvmerge"):
        table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert table == {}


def test_load_mkvmerge_table_handles_unicode_decode_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_check_output(*_args: object, **_kwargs: object) -> str:
        # Simulate non-UTF-8 mkvmerge stdout under a UTF-8 locale.
        b"\xff".decode("utf-8")
        return ""  # unreachable but satisfies type checker

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    with pytest.warns(UserWarning, match="mkvmerge"):
        table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert table == {}


def test_load_mkvmerge_table_empty_output_warns_and_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: "")

    with pytest.warns(UserWarning, match="no parseable rows"):
        table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert table == {}


def test_load_mkvmerge_table_skips_short_pipe_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    output = (
        "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
        "----------------------+----------------+----------------+---------------\n"
        "Truncated | row\n"
        "Chinese               | chi            | chi            | zh\n"
    )
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: output)
    table = Languages._load_mkvmerge_table()  # noqa: SLF001
    assert "chi" in table
    assert "row" not in table


def test_load_mkvmerge_table_skips_pipe_separator_row(monkeypatch: pytest.MonkeyPatch) -> None:
    output = (
        "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
        "---------------------- | -------------- | -------------- | --------------\n"
        "Chinese                | chi            | chi            | zh\n"
    )
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: output)
    table = Languages._load_mkvmerge_table()  # noqa: SLF001
    assert "chi" in table
    assert "----------------------" not in table


def test_load_mkvmerge_table_skips_rows_with_all_empty_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    output = (
        "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
        "----------------------+----------------+----------------+---------------\n"
        "Mystery               |                |                |               \n"
        "English               | eng            | eng            | en\n"
    )
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: output)
    table = Languages._load_mkvmerge_table()  # noqa: SLF001
    assert "eng" in table
    assert "Mystery" not in table


def test_load_mkvmerge_table_garbage_output_warns_and_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda *_a, **_k: "this is not\na pipe-delimited table\nat all\n",
    )

    with pytest.warns(UserWarning, match="no parseable rows"):
        table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert table == {}


def test_load_mkvmerge_table_skips_blank_and_separator_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    output = (
        "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
        "----------------------+----------------+----------------+---------------\n"
        "\n"
        "Chinese               | chi            | chi            | zh\n"
        "   \n"
        "English               | eng            | eng            | en\n"
    )
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: output)

    table = Languages._load_mkvmerge_table()  # noqa: SLF001

    assert "chi" in table
    assert "eng" in table
    assert "ISO 639-3 code" not in table
    assert "-" not in table


@pytest.fixture
def mocked_mkvmerge_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch ``subprocess.check_output`` to return :data:`SYNTHETIC_TABLE`."""
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: SYNTHETIC_TABLE)


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("zh-Hans-CN", "chi"),
        ("und", None),
        ("", None),
        ("chi", "chi"),
        ("zh", "chi"),
        ("zho", "chi"),
        ("zh-Hans", "chi"),
        ("jpn", "jpn"),
        ("ja", "jpn"),
        ("deu", "ger"),
        ("ger", "ger"),
        ("eng", "eng"),
        ("en-US", "eng"),
        ("en-GB", "eng"),
        ("xyz", None),
        (None, None),
    ],
)
def test_normalize_language(code: str | None, expected: str | None) -> None:
    assert Languages.normalize_language(code) == expected


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_normalize_language_is_case_insensitive() -> None:
    assert Languages.normalize_language("ENG") == "eng"
    assert Languages.normalize_language("Zh-HANS") == "chi"
    assert Languages.normalize_language("UND") is None


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_normalize_language_strips_whitespace_in_primary_subtag() -> None:
    assert Languages.normalize_language("  en  ") == "eng"


def test_normalize_language_handles_non_string_input() -> None:
    assert Languages.normalize_language(123) is None  # type: ignore[arg-type]
    assert Languages.normalize_language(["en"]) is None  # type: ignore[arg-type]


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_normalize_language_unknown_bcp47_primary_returns_none() -> None:
    assert Languages.normalize_language("qq-Latn") is None


TABLE_WITH_COLLECTIVE_CODES = (
    "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
    "----------------------+----------------+----------------+---------------\n"
    "Afro-Asiatic languages| afa            | afa            |\n"
    "Ghotuo                | aaa            |                |\n"
)


@pytest.fixture
def mocked_collective_codes_table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: TABLE_WITH_COLLECTIVE_CODES)


@pytest.mark.usefixtures("mocked_collective_codes_table")
def test_normalize_language_collective_code_falls_back_to_b_column() -> None:
    assert Languages.normalize_language("afa") == "afa"


@pytest.mark.usefixtures("mocked_collective_codes_table")
def test_normalize_language_iso639_3_only_returns_none() -> None:
    assert Languages.normalize_language("aaa") is None


@pytest.mark.usefixtures("mocked_collective_codes_table")
def test_languages_match_iso639_3_only_compares_equal() -> None:
    assert Languages.languages_match("aaa", "aaa") is True
    assert Languages.languages_match("aaa", "afa") is False
    assert Languages.languages_match("aaa", "eng") is False


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("Toki Pona", "tok"),
        ("Ghotuo", "aaa"),
    ],
)
def test_languages_match_iso639_3_only_name_resolves(name: str, code: str) -> None:
    assert Languages.languages_match(name, code) is True
    assert Languages.languages_match(code, name) is True


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("chi", "zh-Hans", True),
        ("chi", "zh-CN", True),
        ("chi", "zho", True),
        ("zho", "zh", True),
        ("jpn", "ja", True),
        ("eng", "en-US", True),
        ("eng", "en-GB", True),
        ("chi", "jpn", False),
        ("chi", None, False),
        (None, "chi", False),
        ("und", "chi", False),
        ("xyz", "chi", False),
        ("zh-Hans", "chi", True),
        ("zh", "chi", True),
        ("ja", "ja", True),
        ("ENG", "eng", True),
        ("", "eng", False),
        ("eng", "", False),
    ],
)
def test_languages_match_edge_cases(a: str | None, b: str | None, expected: bool) -> None:
    assert Languages.languages_match(a, b) is expected


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_languages_match_handles_non_string_input() -> None:
    assert Languages.languages_match(123, "chi") is False  # type: ignore[arg-type]
    assert Languages.languages_match("chi", ["zh"]) is False  # type: ignore[arg-type]


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_language_equivalents_chinese_merges_both_sources() -> None:
    assert Languages.language_equivalents("chi") == frozenset({"chi", "zh", "zho"})
    assert Languages.language_equivalents("zh") == frozenset({"chi", "zh", "zho"})
    assert Languages.language_equivalents("zho") == frozenset({"chi", "zh", "zho"})
    assert Languages.language_equivalents("zh-Hans-CN") == frozenset({"chi", "zh", "zho"})


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_language_equivalents_japanese() -> None:
    assert Languages.language_equivalents("jpn") == frozenset({"jpn", "ja"})
    assert Languages.language_equivalents("ja") == frozenset({"jpn", "ja"})


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_language_equivalents_german_uses_iso639_only() -> None:
    assert Languages.language_equivalents("ger") == frozenset({"ger", "deu", "de"})
    assert Languages.language_equivalents("deu") == frozenset({"ger", "deu", "de"})


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_language_equivalents_filipino_no_part1() -> None:
    assert Languages.language_equivalents("fil") == frozenset({"fil"})


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_language_equivalents_iso639_3_only() -> None:
    assert Languages.language_equivalents("tok") == frozenset({"tok"})


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_language_equivalents_unknown_returns_singleton() -> None:
    assert Languages.language_equivalents("xyz") == frozenset({"xyz"})


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize("value", [None, "", "und", "UND"])
def test_language_equivalents_empty_for_no_language(value: str | None) -> None:
    assert Languages.language_equivalents(value) == frozenset()


def test_language_equivalents_handles_non_string_input() -> None:
    assert Languages.language_equivalents(123) == frozenset()  # type: ignore[arg-type]


CUSTOM_TABLE = (
    "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
    "----------------------+----------------+----------------+---------------\n"
    "Afro-Asiatic languages| afa            | afa            |\n"
    "Klingon               | tlh            | tlh            |\n"
)


def test_load_mkvmerge_table_invokes_provided_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_check_output(cmd: list[str], **_kwargs: object) -> str:
        captured.append(cmd)
        return CUSTOM_TABLE

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    Languages._load_mkvmerge_table(("/opt/mkvtoolnix/bin/mkvmerge",))  # noqa: SLF001

    assert captured == [["/opt/mkvtoolnix/bin/mkvmerge", "--list-languages"]]


def test_load_mkvmerge_table_caches_per_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_check_output(cmd: list[str], **_kwargs: object) -> str:
        captured.append(cmd)
        return CUSTOM_TABLE if cmd[0].startswith("/opt/") else SYNTHETIC_TABLE

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    default_first = Languages._load_mkvmerge_table(("mkvmerge",))  # noqa: SLF001
    custom_first = Languages._load_mkvmerge_table(("/opt/mkvtoolnix/bin/mkvmerge",))  # noqa: SLF001
    default_second = Languages._load_mkvmerge_table(("mkvmerge",))  # noqa: SLF001
    custom_second = Languages._load_mkvmerge_table(("/opt/mkvtoolnix/bin/mkvmerge",))  # noqa: SLF001

    expected_subprocess_calls = 2
    assert len(captured) == expected_subprocess_calls, "each distinct path triggers exactly one subprocess call"
    assert default_first is default_second
    assert custom_first is custom_second
    assert default_first is not custom_first

    assert "tlh" in custom_first
    assert "chi" not in custom_first
    assert "chi" in default_first
    assert "tlh" not in default_first


def test_normalize_language_uses_custom_table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: CUSTOM_TABLE)

    custom_path = ("/opt/mkvtoolnix/bin/mkvmerge",)

    assert Languages.normalize_language("afa", custom_path) == "afa"
    assert Languages.normalize_language("tlh", custom_path) == "tlh"


def test_languages_match_uses_custom_table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: CUSTOM_TABLE)

    custom_path = ("/opt/mkvtoolnix/bin/mkvmerge",)

    assert Languages.languages_match("afa", "afa", custom_path) is True


def test_language_equivalents_uses_custom_table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: CUSTOM_TABLE)

    custom_path = ("/opt/mkvtoolnix/bin/mkvmerge",)

    assert "afa" in Languages.language_equivalents("afa", custom_path)


@pytest.mark.usefixtures("mocked_collective_codes_table")
@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("aaa", True),
        ("afa", True),
        ("und", True),
        ("UND", True),
        ("und-Latn", True),
        ("", False),
        (None, False),
        ("   ", False),
        ("xyz", False),
    ],
)
def test_is_known_language_collective_table(code: str | None, expected: bool) -> None:
    assert Languages.is_known_language(code) is expected


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_is_known_language_falls_back_to_python_iso639() -> None:
    assert Languages.is_known_language("ger") is True
    assert Languages.is_known_language("deu") is True


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_is_known_language_strips_bcp47_subtags() -> None:
    assert Languages.is_known_language("zh-Hans-CN") is True
    assert Languages.is_known_language("en-US") is True


def test_is_known_language_handles_non_string_input() -> None:
    assert Languages.is_known_language(123) is False  # type: ignore[arg-type]
    assert Languages.is_known_language(["en"]) is False  # type: ignore[arg-type]


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize(
    "value",
    [
        "English",
        "english",
        "ENGLISH",
        "English-US",
        "English-United States",
        "Russian",
        "Mandarin",
    ],
)
def test_is_known_language_rejects_language_names(value: str) -> None:
    assert Languages.is_known_language(value) is False


def test_is_known_language_uses_custom_table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: CUSTOM_TABLE)

    custom_path = ("/opt/mkvtoolnix/bin/mkvmerge",)

    assert Languages.is_known_language("afa", custom_path) is True
    assert Languages.is_known_language("tlh", custom_path) is True


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize(
    "malformed",
    [
        " en",
        "en ",
        " en-US ",
        pytest.param("en\tUS", id="en-tab-US"),
        "en US",
        "en--US",
        "-en",
        "en-",
        "en-US-",
        "e",
        "en-toolongsubtag",
        "en-a",
        "en-x",
        "en-US-Latn",
        "en-1",
    ],
)
def test_is_known_language_rejects_malformed_bcp47(malformed: str) -> None:
    assert Languages.is_known_language(malformed) is False


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize(
    "well_formed",
    [
        "en-Latn-US",
        "zh-Hans-CN",
        "en-a-bbb",
        "en-x-private",
        "und-Latn",
        "zh-cmn-Hans-CN",
    ],
)
def test_is_known_language_accepts_well_formed_bcp47(well_formed: str) -> None:
    assert Languages.is_known_language(well_formed) is True


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize(
    "malformed",
    [
        "Pa-O",
        "en--US",
        "en-",
        "-en",
        "en-toolongsubtag",
        "en-US-Latn",
    ],
)
def test_normalize_language_rejects_malformed_bcp47(malformed: str) -> None:
    assert Languages.normalize_language(malformed) is None
    assert Languages.language_equivalents(malformed) == frozenset()
    assert Languages.languages_match(malformed, "eng") is False
    assert Languages.languages_match(malformed, "pan") is False


@pytest.mark.usefixtures("mocked_collective_codes_table")
def test_canonical_key_returns_iso639_3_for_b_less_row() -> None:
    # ``aaa`` is in the mkvmerge table but has no /B form, so
    # ``normalize_language`` returns ``None``. ``_canonical_key`` must fall
    # back to the row's 639-3 sibling so ``languages_match`` recognizes it.
    assert Languages._canonical_key("aaa", None) == "aaa"  # noqa: SLF001


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_canonical_key_falls_back_to_python_iso639_for_b_less_name() -> None:
    # English language name resolving to a /B-less language. The name is not
    # in the mkvmerge table, so the helper must consult python-iso639 and
    # return its part3 ("tok" for Toki Pona).
    assert Languages._canonical_key("Toki Pona", None) == "tok"  # noqa: SLF001


@pytest.mark.usefixtures("mocked_mkvmerge_table")
def test_canonical_key_returns_none_for_sentinels() -> None:
    assert Languages._canonical_key(None, None) is None  # noqa: SLF001
    assert Languages._canonical_key("", None) is None  # noqa: SLF001
    assert Languages._canonical_key("und", None) is None  # noqa: SLF001
    assert Languages._canonical_key("xyz", None) is None  # noqa: SLF001
    assert Languages._canonical_key(123, None) is None  # type: ignore[arg-type]  # noqa: SLF001


@pytest.mark.usefixtures("mocked_mkvmerge_table")
@pytest.mark.parametrize(
    ("code", "is_known", "normalized"),
    [
        # Recognized codes: writer emits, reader returns canonical /B.
        ("eng", True, "eng"),
        ("fre", True, "fre"),
        ("ger", True, "ger"),
        ("jpn", True, "jpn"),
        ("chi", True, "chi"),
        ("zh-Hans", True, "chi"),
        ("en-US", True, "eng"),
        # 639-3-only: writer emits (mkvmerge accepts), reader collapses to None.
        ("tok", True, None),
        # 'und' sentinel: writer emits (explicit-undefined), reader collapses.
        ("und", True, None),
        ("und-Latn", True, None),
        # English language names: writer drops (mkvmerge rejects names),
        # but normalize_language resolves them. The writer's gate is
        # is_known_language, NOT normalize_language — this asymmetry is
        # deliberate and documented.
        ("English", False, "eng"),
        # Unknown / malformed: writer drops, reader returns None.
        ("xyz", False, None),
        ("en--US", False, None),
        ("Pa-O", False, None),
        # Sentinels: both agree on "no language".
        ("", False, None),
        (None, False, None),
    ],
)
def test_writer_gate_and_reader_normalizer_documented_intent(
    code: str | None,
    is_known: bool,
    normalized: str | None,
) -> None:
    """Document the writer-vs-reader gate behavior for tracked inputs.

    The writer (``TrackOptions._generate_properties``) emits ``--language``
    iff :func:`is_known_language` accepts the value. The reader
    (``MKVTrack.effective_language``) reports what mkvmerge will see, which
    is determined by :func:`normalize_language`. The two functions overlap
    on most inputs but diverge intentionally for English language names
    (normalizable but not emitted) and the ``"und"`` sentinel (emitted as
    explicit-undefined but reported as ``None``).
    """
    assert Languages.is_known_language(code) is is_known
    assert Languages.normalize_language(code) == normalized


def test_preload_language_table_warms_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    # The first call inside the same process triggers subprocess; the second
    # must hit the cache. Verify by counting subprocess invocations.
    call_count = {"n": 0}

    def fake_check_output(*_args: object, **_kwargs: object) -> str:
        call_count["n"] += 1
        return SYNTHETIC_TABLE

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    Languages.preload_language_table()
    assert call_count["n"] == 1
    Languages.preload_language_table()
    assert call_count["n"] == 1, "cache should be warm after preload"
    Languages.normalize_language("eng")
    assert call_count["n"] == 1, "subsequent lookups must reuse the cache"


def test_preload_language_table_with_custom_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_check_output(cmd: list[str], **_kwargs: object) -> str:
        captured.append(cmd)
        return SYNTHETIC_TABLE

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    Languages.preload_language_table(("/opt/mkvtoolnix/bin/mkvmerge",))
    assert captured == [["/opt/mkvtoolnix/bin/mkvmerge", "--list-languages"]]


def test_preload_language_table_exported_from_pymkv() -> None:
    assert pymkv.preload_language_table is Languages.preload_language_table
    assert "preload_language_table" in pymkv.__all__
