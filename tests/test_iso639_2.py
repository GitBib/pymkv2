from typing import cast

from pymkv.ISO639_2 import is_iso639_2


def test_is_iso639_2_true() -> None:
    assert is_iso639_2("eng") is True


def test_is_iso639_2_false() -> None:
    assert is_iso639_2("xyz") is False


def test_is_iso639_2_non_str_input() -> None:
    assert is_iso639_2(cast(str, 123)) is False


def test_is_iso639_2_empty_string() -> None:
    assert is_iso639_2("") is False
