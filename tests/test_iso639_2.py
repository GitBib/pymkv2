from typing import cast

import pytest

from pymkv.ISO639_2 import get_iso639_2, is_iso639_2


def test_get_iso639_2_part2b_passthrough() -> None:
    assert get_iso639_2("eng") == "eng"


def test_get_iso639_2_part2t_to_part2b() -> None:
    assert get_iso639_2("fra") == "fre"


def test_get_iso639_2_part2t_german() -> None:
    assert get_iso639_2("deu") == "ger"


def test_get_iso639_2_part1() -> None:
    assert get_iso639_2("en") == "eng"


def test_get_iso639_2_english_name() -> None:
    assert get_iso639_2("English") == "eng"


def test_get_iso639_2_lowercase_name() -> None:
    assert get_iso639_2("english") == "eng"


def test_get_iso639_2_mixed_case_name() -> None:
    assert get_iso639_2("ARAbIC") == "ara"


def test_get_iso639_2_part3_only_returns_none() -> None:
    assert get_iso639_2("tok") is None


def test_get_iso639_2_invalid_returns_none() -> None:
    assert get_iso639_2("xyz") is None


def test_get_iso639_2_non_str_returns_none() -> None:
    assert get_iso639_2(cast("str", 123)) is None


def test_get_iso639_2_unhashable_returns_none() -> None:
    assert get_iso639_2(cast("str", ["en"])) is None
    assert get_iso639_2(cast("str", {"en": 1})) is None


def test_get_iso639_2_empty_string_returns_none() -> None:
    assert get_iso639_2("") is None


def test_get_iso639_2_none_returns_none() -> None:
    assert get_iso639_2(None) is None


def test_is_iso639_2_warns_deprecation() -> None:
    with pytest.warns(DeprecationWarning, match="is_iso639_2 is deprecated"):
        result = is_iso639_2("eng")
    assert result is True


def test_is_iso639_2_invalid_returns_false() -> None:
    with pytest.warns(DeprecationWarning, match="is_iso639_2 is deprecated"):
        result = is_iso639_2("xyz")
    assert result is False
