"""Integration tests against the real ``mkvmerge`` binary."""

from __future__ import annotations

import shutil

import pytest

from pymkv import languages_match
from pymkv.Languages import _load_mkvmerge_table

pytestmark = pytest.mark.skipif(
    shutil.which("mkvmerge") is None,
    reason="mkvmerge not installed; integration test requires the real binary",
)


@pytest.fixture(autouse=True)
def _clear_mkvmerge_table_cache() -> None:
    _load_mkvmerge_table.cache_clear()


def test_real_mkvmerge_table_contains_expected_codes() -> None:
    table = _load_mkvmerge_table()
    assert table, "mkvmerge --list-languages produced no parseable rows"

    for code in ("chi", "eng", "jpn", "ger", "fre", "rus"):
        assert code in table, f"expected {code!r} in real mkvmerge table"

    assert "und" in table, "expected 'und' undefined sentinel in real mkvmerge table"

    assert {"chi", "zh"}.issubset(table["chi"].siblings)
    assert {"eng", "en"}.issubset(table["eng"].siblings)
    assert {"jpn", "ja"}.issubset(table["jpn"].siblings)


def test_languages_match_resolves_bcp47_against_real_table() -> None:
    assert languages_match("chi", "zh-Hans") is True
    assert languages_match("jpn", "ja") is True
    assert languages_match("zho", "zh") is True
    assert languages_match("ger", "de") is True
    assert languages_match("eng", "jpn") is False
    assert languages_match("und", "eng") is False
    assert languages_match("", "eng") is False
