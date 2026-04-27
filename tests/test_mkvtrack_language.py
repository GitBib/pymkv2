"""Tests for the lenient + canonicalizing :attr:`MKVTrack.language` setter."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pymkv import MKVTrack
from pymkv.Languages import _load_mkvmerge_table

if TYPE_CHECKING:
    from pathlib import Path

    from pymkv.models import MkvMergeOutput

# Synthetic mkvmerge table covering every language used by the tests below.
# Mocking the subprocess keeps these tests hermetic so they don't depend on
# whether mkvmerge is installed on the host running the suite.
_SYNTHETIC_TABLE = (
    "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
    "----------------------+----------------+----------------+---------------\n"
    "Arabic                | ara            | ara            | ar\n"
    "Chinese               | chi            | chi            | zh\n"
    "English               | eng            | eng            | en\n"
    "French                | fre            | fre            | fr\n"
    "German                | ger            | ger            | de\n"
    "Japanese              | jpn            | jpn            | ja\n"
    "Afro-Asiatic languages| afa            | afa            |\n"
    "Toki Pona             | tok            |                |\n"
    "Undetermined          | und            | und            |\n"
)


@pytest.fixture(autouse=True)
def _patched_mkvmerge_table(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Run every test against a deterministic synthetic mkvmerge table."""
    _load_mkvmerge_table.cache_clear()
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: _SYNTHETIC_TABLE)
    yield
    _load_mkvmerge_table.cache_clear()


def _make_track(dummy_mkv: Path, info: MkvMergeOutput) -> MKVTrack:
    """Build an MKVTrack against a dummy file path with mocked file probing."""
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info", return_value=info),
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
    ):
        return MKVTrack(str(dummy_mkv))


def test_language_setter_part2b_passthrough(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "eng"
    assert track.language == "eng"


def test_language_setter_part2t_canonicalizes_to_part2b(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "fra"
    assert track.language == "fre"


def test_language_setter_part2t_german_canonicalizes(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "deu"
    assert track.language == "ger"


def test_language_setter_part1_resolves(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "en"
    assert track.language == "eng"


def test_language_setter_english_name(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "English"
    assert track.language == "eng"


def test_language_setter_lowercase_name(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "english"
    assert track.language == "eng"


def test_language_setter_mixed_case_name(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "ARAbIC"
    assert track.language == "ara"


def test_language_setter_none_unsets(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "eng"
    assert track.language == "eng"
    track.language = None
    assert track.language is None


def test_language_setter_invalid_raises_with_offending_value(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    with pytest.raises(
        ValueError,
        match=r"'xyz' cannot be mapped to a valid ISO 639-2 language code",
    ):
        track.language = "xyz"


def test_language_setter_part3_only_raises(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    with pytest.raises(
        ValueError,
        match=r"'tok' cannot be mapped to a valid ISO 639-2 language code",
    ):
        track.language = "tok"


def test_language_setter_empty_string_raises(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    with pytest.raises(
        ValueError,
        match=r"'' cannot be mapped to a valid ISO 639-2 language code",
    ):
        track.language = ""


def test_language_setter_constructor_canonicalizes(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info", return_value=single_video_info),
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
    ):
        track = MKVTrack(str(dummy_mkv), language="fra")
    assert track.language == "fre"


def test_language_setter_accepts_iso639_2_collective_code(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "afa"
    assert track.language == "afa"


def test_language_setter_accepts_bcp47_with_subtags(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "zh-Hans"
    assert track.language == "chi"


def test_effective_language_both_set_prefers_language_ietf(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "chi"
    track.language_ietf = "zh-Hans"
    assert track.effective_language == "chi"


def test_effective_language_only_language_ietf(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = None
    track.language_ietf = "zh-Hans"
    assert track.effective_language == "chi"


def test_effective_language_only_language_field(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "deu"
    track.language_ietf = None
    assert track.effective_language == "ger"


def test_effective_language_strips_bcp47_subtags(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "eng"
    track.language_ietf = "en-US"
    assert track.effective_language == "eng"


def test_effective_language_und_resolves_to_none(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = None
    track.language_ietf = "und"
    assert track.effective_language is None


def test_effective_language_both_none(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = None
    track.language_ietf = None
    assert track.effective_language is None


def test_effective_language_unknown_ietf_falls_through_to_language(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "eng"
    track.language_ietf = "xyz"
    assert track.effective_language == "eng"


def test_effective_language_name_only_ietf_falls_through_to_language(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = None
    track.language_ietf = "English"
    assert track.effective_language is None

    track.language = "fre"
    assert track.effective_language == "fre"


def test_matches_language_bcp47_against_language_field(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "chi"
    track.language_ietf = None
    assert track.matches_language("zh") is True


def test_matches_language_concrete_bug_repro(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "chi"
    track.language_ietf = "zh-Hans"
    assert track.matches_language("chi") is True


def test_matches_language_part2t_against_language(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "deu"
    track.language_ietf = None
    assert track.matches_language("deu") is True
    assert track.matches_language("ger") is True
    assert track.matches_language("de") is True


def test_matches_language_english_name(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "eng"
    track.language_ietf = "en-US"
    assert track.matches_language("English") is True
    assert track.matches_language("english") is True


def test_matches_language_different_language_returns_false(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "chi"
    track.language_ietf = "zh-Hans"
    assert track.matches_language("jpn") is False


def test_matches_language_none_or_empty_or_und_returns_false(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "eng"
    track.language_ietf = None
    assert track.matches_language(None) is False
    assert track.matches_language("") is False
    assert track.matches_language("und") is False


def test_matches_language_unknown_code_returns_false(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "eng"
    track.language_ietf = None
    assert track.matches_language("xyz") is False


def test_matches_language_iso639_3_only_via_language_ietf(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = None
    track.language_ietf = "tok"
    assert track.matches_language("tok") is True
    assert track.matches_language("eng") is False


def test_matches_language_track_without_any_language_returns_false(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = None
    track.language_ietf = None
    assert track.matches_language("eng") is False


def test_language_setter_und_stored_as_none(dummy_mkv: Path, single_video_info: MkvMergeOutput) -> None:
    # ``"und"`` means "no language"; the setter normalizes it to ``None`` so
    # the read side (``language``, ``effective_language``) agrees.
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "und"
    assert track.language is None
    assert track.effective_language is None


def test_language_setter_und_uppercase_stored_as_none(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    track = _make_track(dummy_mkv, single_video_info)
    track.language = "UND"
    assert track.language is None


def test_language_ietf_und_still_emits_explicit_undefined(
    dummy_mkv: Path,
    single_video_info: MkvMergeOutput,
) -> None:
    # The escape hatch: callers wanting to explicitly emit ``--language TID:und``
    # to mkvmerge use ``language_ietf`` (which has no validating setter).
    track = _make_track(dummy_mkv, single_video_info)
    track.language = None
    track.language_ietf = "und"
    assert track.language is None
    assert track.language_ietf == "und"
