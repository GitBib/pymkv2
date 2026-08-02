import subprocess as sp
from pathlib import Path
from unittest.mock import Mock

import msgspec
import pytest

from pymkv import MKVFile
from pymkv.chapters import ChapterAtom, ChapterDisplay, Chapters
from pymkv.Verifications import get_file_info
from tests.conftest import requires_mkvtoolnix


def test_chapter_language_getter_setter() -> None:
    mkv = MKVFile()
    assert mkv.chapter_language is None

    mkv.chapter_language = "eng"
    assert mkv.chapter_language == "eng"

    mkv.chapter_language = None
    assert mkv.chapter_language is None

    with pytest.raises(
        ValueError,
        match=r"'invalid_code' cannot be mapped to a valid ISO 639-2 language code",
    ):
        mkv.chapter_language = "invalid_code"


def test_chapter_language_accepts_english_name() -> None:
    mkv = MKVFile()
    mkv.chapter_language = "English"
    assert mkv.chapter_language == "eng"


def test_chapter_language_lowercase_name() -> None:
    mkv = MKVFile()
    mkv.chapter_language = "english"
    assert mkv.chapter_language == "eng"


def test_chapter_language_canonicalizes_terminological_to_bibliographic() -> None:
    mkv = MKVFile()
    mkv.chapter_language = "fra"
    assert mkv.chapter_language == "fre"

    mkv.chapter_language = "deu"
    assert mkv.chapter_language == "ger"


def test_chapter_language_accepts_iso639_1() -> None:
    mkv = MKVFile()
    mkv.chapter_language = "en"
    assert mkv.chapter_language == "eng"


def test_chapter_language_invalid_includes_offending_value() -> None:
    mkv = MKVFile()
    with pytest.raises(
        ValueError,
        match=r"'xyz' cannot be mapped to a valid ISO 639-2 language code",
    ):
        mkv.chapter_language = "xyz"


def test_chapter_language_accepts_iso639_2_collective_code() -> None:
    mkv = MKVFile()
    mkv.chapter_language = "afa"
    assert mkv.chapter_language == "afa"


def test_chapter_language_und_stored_as_none() -> None:
    mkv = MKVFile()
    mkv.chapter_language = "und"
    assert mkv.chapter_language is None


def test_chapters_method_canonicalizes_language(tmp_path: Path) -> None:
    mkv = MKVFile()
    chapter_file = tmp_path / "chapters.xml"
    chapter_file.touch()

    mkv.chapters(str(chapter_file), language="English")
    assert mkv.chapter_language == "eng"


def test_global_tag_entries() -> None:
    mkv = MKVFile()
    assert mkv.global_tag_entries == 0


def test_link_to_previous(tmp_path: Path) -> None:
    mkv = MKVFile()
    assert mkv._link_to_previous_file is None  # noqa: SLF001

    test_file = tmp_path / "previous_file.mkv"
    test_file.touch()

    mkv.link_to_previous(str(test_file))
    assert mkv._link_to_previous_file == str(test_file)  # noqa: SLF001


def test_link_to_next(tmp_path: Path) -> None:
    mkv = MKVFile()
    assert mkv._link_to_next_file is None  # noqa: SLF001

    test_file = tmp_path / "next_file.mkv"
    test_file.touch()

    mkv.link_to_next(str(test_file))
    assert mkv._link_to_next_file == str(test_file)  # noqa: SLF001


def test_link_to_none() -> None:
    mkv = MKVFile()
    mkv._link_to_previous_file = "previous.mkv"  # noqa: SLF001
    mkv._link_to_next_file = "next.mkv"  # noqa: SLF001

    mkv.link_to_none()
    assert mkv._link_to_previous_file is None  # noqa: SLF001
    assert mkv._link_to_next_file is None  # noqa: SLF001


def test_chapters(tmp_path: Path) -> None:
    mkv = MKVFile()
    assert mkv._chapters_file is None  # noqa: SLF001

    chapter_file = tmp_path / "chapters.xml"
    chapter_file.touch()

    mkv.chapters(str(chapter_file))
    assert mkv._chapters_file == str(chapter_file)  # noqa: SLF001

    mkv2 = MKVFile()
    mkv2._chapters_file = "some_file.xml"  # noqa: SLF001
    mkv2._chapters_file = None  # noqa: SLF001
    assert mkv2._chapters_file is None  # noqa: SLF001


def test_global_tags(tmp_path: Path) -> None:
    mkv = MKVFile()
    assert mkv._global_tags_file is None  # noqa: SLF001

    tags_file = tmp_path / "global_tags.xml"
    tags_file.touch()

    mkv.global_tags(str(tags_file))
    assert mkv._global_tags_file == str(tags_file)  # noqa: SLF001


def test_track_tags() -> None:
    mkv = MKVFile()

    track1 = Mock()
    track2 = Mock()
    track3 = Mock()

    track1.no_track_tags = False
    track2.no_track_tags = False
    track3.no_track_tags = False

    mkv.tracks = [track1, track2, track3]

    mkv.track_tags(0, 1)
    assert not mkv.tracks[0].no_track_tags
    assert not mkv.tracks[1].no_track_tags
    assert mkv.tracks[2].no_track_tags

    for track in mkv.tracks:
        track.no_track_tags = False

    mkv.track_tags(0, 1, exclusive=True)
    assert mkv.tracks[0].no_track_tags
    assert mkv.tracks[1].no_track_tags
    assert not mkv.tracks[2].no_track_tags


def test_no_chapters() -> None:
    mkv = MKVFile()

    track1 = Mock()
    track2 = Mock()

    track1.no_chapters = False
    track2.no_chapters = False

    mkv.tracks = [track1, track2]

    mkv.no_chapters()

    for track in mkv.tracks:
        assert track.no_chapters is True


def test_no_global_tags() -> None:
    mkv = MKVFile()

    track1 = Mock()
    track2 = Mock()

    track1.no_global_tags = False
    track2.no_global_tags = False

    mkv.tracks = [track1, track2]

    mkv.no_global_tags()

    for track in mkv.tracks:
        assert track.no_global_tags is True


def test_no_track_tags() -> None:
    mkv = MKVFile()

    track1 = Mock()
    track2 = Mock()

    track1.no_track_tags = False
    track2.no_track_tags = False

    mkv.tracks = [track1, track2]

    mkv.no_track_tags()

    for track in mkv.tracks:
        assert track.no_track_tags is True


def test_chapters_obj_defaults_to_none() -> None:
    mkv = MKVFile()
    assert mkv.chapters_obj is None


def test_read_chapters_parses_mkvextract_output(monkeypatch: pytest.MonkeyPatch, dummy_mkv: Path) -> None:
    """Unit test for the plumbing in `_read_chapters` (command shape, stdout decoding)."""
    mkv = MKVFile()

    xml_output = b"""<?xml version="1.0" encoding="UTF-8"?>
<Chapters>
  <EditionEntry>
    <ChapterAtom>
      <ChapterTimeStart>00:00:00.000000000</ChapterTimeStart>
      <ChapterDisplay>
        <ChapterString>Intro</ChapterString>
        <ChapterLanguage>eng</ChapterLanguage>
      </ChapterDisplay>
    </ChapterAtom>
  </EditionEntry>
</Chapters>
"""

    def fake_run(command: list[str], check: bool, capture_output: bool) -> Mock:
        assert command[-2] == "chapters"
        assert command[-1] == str(dummy_mkv)
        result = Mock()
        result.stdout = xml_output
        return result

    monkeypatch.setattr(sp, "run", fake_run)

    chapters = mkv._read_chapters(str(dummy_mkv))  # noqa: SLF001

    assert chapters is not None
    assert len(chapters.editions) == 1
    assert chapters.editions[0].atoms[0].displays[0].string == "Intro"


@requires_mkvtoolnix
def test_read_chapters_matches_real_mkvextract_output(
    get_path_test_file_with_chapters: Path,
    real_mkvextract_chapters_xml: str,
) -> None:
    """`_read_chapters` should handle actual `mkvextract chapters` output, BOM and all."""
    assert real_mkvextract_chapters_xml.strip(), "expected mkvextract to emit chapter XML"

    mkv = MKVFile()
    chapters = mkv._read_chapters(str(get_path_test_file_with_chapters))  # noqa: SLF001

    assert chapters is not None
    assert len(chapters.editions) == 1
    assert chapters.editions[0].uid == 1111  # noqa: PLR2004
    atom = chapters.editions[0].atoms[0]
    assert atom.uid == 2001  # noqa: PLR2004
    assert atom.displays[0].string == "Intro"
    assert atom.displays[0].language == "chi"


def test_read_chapters_returns_none_on_process_error(monkeypatch: pytest.MonkeyPatch, dummy_mkv: Path) -> None:
    mkv = MKVFile()

    def fake_run(*args: object, **kwargs: object) -> Mock:
        raise sp.CalledProcessError(returncode=2, cmd=["mkvextract"])

    monkeypatch.setattr(sp, "run", fake_run)

    assert mkv._read_chapters(str(dummy_mkv)) is None  # noqa: SLF001


def test_read_chapters_returns_none_on_empty_output(monkeypatch: pytest.MonkeyPatch, dummy_mkv: Path) -> None:
    mkv = MKVFile()

    def fake_run(*args: object, **kwargs: object) -> Mock:
        result = Mock()
        result.stdout = b""
        return result

    monkeypatch.setattr(sp, "run", fake_run)

    assert mkv._read_chapters(str(dummy_mkv)) is None  # noqa: SLF001


def test_read_chapters_returns_none_on_invalid_xml(monkeypatch: pytest.MonkeyPatch, dummy_mkv: Path) -> None:
    mkv = MKVFile()

    def fake_run(*args: object, **kwargs: object) -> Mock:
        result = Mock()
        result.stdout = b"<Chapters><EditionEntry>"
        return result

    monkeypatch.setattr(sp, "run", fake_run)

    assert mkv._read_chapters(str(dummy_mkv)) is None  # noqa: SLF001


@requires_mkvtoolnix
def test_init_populates_chapters_obj_from_existing_file(get_path_test_file_with_chapters: Path) -> None:
    """Integration test: opening a file that actually has chapters should expose them."""
    info = msgspec.to_builtins(get_file_info(get_path_test_file_with_chapters, "mkvmerge"))
    chapter_entries = info.get("chapters", [])
    assert any(entry.get("num_entries", 0) > 0 for entry in chapter_entries), (
        "fixture file should have chapters -- test is not exercising the feature"
    )

    mkv = MKVFile(str(get_path_test_file_with_chapters))

    assert mkv.chapters_obj is not None
    assert len(mkv.chapters_obj.editions) > 0
    assert mkv.chapters_obj.editions[0].atoms[0].displays[0].string == "Intro"


@requires_mkvtoolnix
def test_command_does_not_rewrite_chapters_read_from_source(get_path_test_file_with_chapters: Path) -> None:
    """Chapters populated from an existing file must not be round-tripped through `Chapters`."""
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None  # sanity check: the fixture does have chapters

    command = mkv.command("output.mkv", subprocess=True)

    assert "--chapters" not in command
    assert mkv._chapters_file is None  # noqa: SLF001


@requires_mkvtoolnix
def test_command_rewrites_chapters_after_explicit_edit(get_path_test_file_with_chapters: Path) -> None:
    """Once the caller explicitly edits chapters that came from the source file, they should be
    written out and passed to mkvmerge via `--chapters`, since they no longer match the source.
    """
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None

    mkv.add_chapter(ChapterAtom(time_start="00:10:00.000", displays=[ChapterDisplay(string="New Chapter")]))

    command = mkv.command("output.mkv", subprocess=True)

    assert "--chapters" in command
    assert mkv._chapters_file is not None  # noqa: SLF001


def test_command_rewrites_chapters_reassigned_by_caller() -> None:
    """Reassigning `chapters_obj` directly is also treated as a caller edit."""
    mkv = MKVFile()
    mkv.chapters_obj = Chapters()
    mkv.chapters_obj.add_simple_chapter("00:00:00.000", "Intro")

    command = mkv.command("output.mkv", subprocess=True)

    assert "--chapters" in command
    assert mkv._chapters_file is not None  # noqa: SLF001


def test_no_attachments() -> None:
    mkv = MKVFile()

    track1 = Mock()
    track2 = Mock()

    track1.no_attachments = False
    track2.no_attachments = False

    mkv.tracks = [track1, track2]

    mkv.no_attachments()

    for track in mkv.tracks:
        assert track.no_attachments is True
