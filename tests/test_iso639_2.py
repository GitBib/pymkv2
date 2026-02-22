from typing import cast

from pymkv.ISO639_2 import get_iso639_2


def test_get_iso639_2_valid_code() -> None:
    assert get_iso639_2("eng") == "eng"


def test_get_iso639_2_valid_name() -> None:
    # Using language name instead of code
    assert get_iso639_2("English") == "eng"


def test_get_iso639_2_invalid_code() -> None:
    assert get_iso639_2("xyz") is None


def test_get_iso639_2_non_str_input() -> None:
    # Should gracefully return None for non-str input
    assert get_iso639_2(cast("str", 123)) is None


def test_get_iso639_2_empty_string() -> None:
    assert get_iso639_2("") is None
