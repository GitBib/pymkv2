import shutil
import subprocess as sp
from pathlib import Path
from unittest.mock import Mock

import msgspec
import pytest

from pymkv import MKVFile
from pymkv.chapters import ChapterAtom, ChapterDisplay, Chapters, EditionEntry, parse_chapters_xml
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
    """Unit test for the plumbing in `_read_chapters` (command shape, stdout parsing)."""
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


def _extract_chapters(path: Path) -> Chapters:
    """Chapters of `path` as reported by the real mkvextract."""
    mkvextract = shutil.which("mkvextract")
    assert mkvextract is not None
    result = sp.run([mkvextract, "chapters", str(path)], check=True, capture_output=True)  # noqa: S603
    return parse_chapters_xml(result.stdout)


def _chapter_count(path: Path) -> int:
    info = get_file_info(path, "mkvmerge")
    return sum(c.num_entries for c in info.chapters)


@requires_mkvtoolnix
def test_command_passes_through_untouched_chapters(get_path_test_file_with_chapters: Path) -> None:
    """Chapters read from the source must be left to mkvmerge."""
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None

    command = mkv.command("output.mkv", subprocess=True)

    assert "--chapters" not in command
    assert "--no-chapters" not in command
    assert mkv._temp_chapters_file is None  # noqa: SLF001


@requires_mkvtoolnix
def test_mux_untouched_chapters_keeps_all_fields(get_path_test_file_with_chapters: Path, tmp_path: Path) -> None:
    """Remuxing without edits keeps fields such as ChapterPhysicalEquiv and ChapLanguageIETF."""
    output = tmp_path / "out.mkv"
    MKVFile(str(get_path_test_file_with_chapters)).mux(output, silent=True)

    atom = _extract_chapters(output).editions[0].atoms[0]
    assert atom.physical_equiv == 10  # noqa: PLR2004
    assert atom.displays[0].language_ietf == ["zh-Hans"]


@requires_mkvtoolnix
def test_in_place_edit_is_written(get_path_test_file_with_chapters: Path, tmp_path: Path) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None
    mkv.chapters_obj.editions[0].atoms[0].displays[0].string = "RENAMED"

    command = mkv.command("output.mkv", subprocess=True)
    assert "--chapters" in command
    assert command.index("--no-chapters") < command.index(str(get_path_test_file_with_chapters))

    output = tmp_path / "out.mkv"
    mkv.mux(output, silent=True)

    atoms = _extract_chapters(output).editions[0].atoms
    assert [a.displays[0].string for a in atoms] == ["RENAMED", "Outro"]


@requires_mkvtoolnix
def test_edit_keeps_unmodified_fields(get_path_test_file_with_chapters: Path, tmp_path: Path) -> None:
    """Fields untouched by the edit survive the write path."""
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    mkv.add_chapter(ChapterAtom(time_start="00:00:02.000", displays=[ChapterDisplay(string="New Chapter")]))

    output = tmp_path / "out.mkv"
    mkv.mux(output, silent=True)

    atoms = _extract_chapters(output).editions[0].atoms
    assert len(atoms) == 3  # noqa: PLR2004
    assert atoms[0].physical_equiv == 10  # noqa: PLR2004
    assert atoms[0].displays[0].language_ietf == ["zh-Hans"]
    assert atoms[0].displays[0].language == "chi"


@requires_mkvtoolnix
def test_deleted_chapter_is_removed_from_output(get_path_test_file_with_chapters: Path, tmp_path: Path) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    chapters = mkv.chapters_obj
    assert chapters is not None
    del chapters.editions[0].atoms[1]
    mkv.chapters_obj = chapters

    output = tmp_path / "out.mkv"
    mkv.mux(output, silent=True)

    atoms = _extract_chapters(output).editions[0].atoms
    assert [a.displays[0].string for a in atoms] == ["Intro"]


@requires_mkvtoolnix
def test_deleted_chapter_in_place_without_reassign(get_path_test_file_with_chapters: Path, tmp_path: Path) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None
    mkv.chapters_obj.editions[0].atoms.pop()

    output = tmp_path / "out.mkv"
    mkv.mux(output, silent=True)

    assert len(_extract_chapters(output).editions[0].atoms) == 1


@requires_mkvtoolnix
@pytest.mark.parametrize("remove", ["none", "empty_chapters", "empty_edition"])
def test_removing_all_chapters(get_path_test_file_with_chapters: Path, tmp_path: Path, remove: str) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None
    if remove == "none":
        mkv.chapters_obj = None
    elif remove == "empty_chapters":
        mkv.chapters_obj = Chapters()
    else:
        mkv.chapters_obj.editions[0].atoms.clear()

    command = mkv.command("output.mkv", subprocess=True)
    assert "--no-chapters" in command
    assert "--chapters" not in command

    output = tmp_path / "out.mkv"
    mkv.mux(output, silent=True)
    assert _chapter_count(output) == 0


@requires_mkvtoolnix
def test_reverting_edit_returns_to_pass_through(get_path_test_file_with_chapters: Path) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None
    display = mkv.chapters_obj.editions[0].atoms[0].displays[0]

    display.string = "Changed"
    assert "--chapters" in mkv.command("output.mkv", subprocess=True)

    display.string = "Intro"
    command = mkv.command("output.mkv", subprocess=True)
    assert "--chapters" not in command
    assert "--no-chapters" not in command


@requires_mkvtoolnix
def test_second_command_reflects_later_edits(get_path_test_file_with_chapters: Path) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None
    mkv.chapters_obj.editions[0].atoms[0].displays[0].string = "First"
    mkv.command("output.mkv")
    first_temp = Path(mkv._temp_chapters_file or "")  # noqa: SLF001
    assert "First" in first_temp.read_text(encoding="utf-8")

    mkv.chapters_obj.editions[0].atoms[0].displays[0].string = "Second"
    mkv.command("output.mkv")

    assert not first_temp.exists()
    second_temp = Path(mkv._temp_chapters_file or "")  # noqa: SLF001
    assert "Second" in second_temp.read_text(encoding="utf-8")
    mkv.cleanup()


@requires_mkvtoolnix
def test_chapters_file_takes_precedence_over_chapters_obj(
    get_path_test_file_with_chapters: Path,
    get_path_test_chapters_xml: Path,
) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None
    mkv.chapters_obj.editions[0].atoms.clear()
    mkv.chapters(str(get_path_test_chapters_xml))

    command = mkv.command("output.mkv", subprocess=True)

    assert command.count("--chapters") == 1
    assert str(get_path_test_chapters_xml) in command
    assert "--no-chapters" not in command
    assert mkv._temp_chapters_file is None  # noqa: SLF001


@requires_mkvtoolnix
def test_add_file_path_imports_chapters(get_path_test_file_with_chapters: Path) -> None:
    mkv = MKVFile()
    mkv.add_file(str(get_path_test_file_with_chapters))

    assert mkv.chapters_obj is not None
    assert mkv.chapters_obj.editions[0].atoms[0].displays[0].string == "Intro"
    assert "--chapters" not in mkv.command("output.mkv", subprocess=True)


@requires_mkvtoolnix
def test_add_file_mkvfile_imports_chapters(get_path_test_file_with_chapters: Path) -> None:
    mkv = MKVFile()
    mkv.add_file(MKVFile(str(get_path_test_file_with_chapters)))

    assert mkv.chapters_obj is not None
    assert len(mkv.chapters_obj.editions[0].atoms) == 2  # noqa: PLR2004


@requires_mkvtoolnix
def test_add_file_chapters_are_independent_copies(get_path_test_file_with_chapters: Path) -> None:
    other = MKVFile(str(get_path_test_file_with_chapters))
    mkv = MKVFile()
    mkv.add_file(other)
    assert mkv.chapters_obj is not None
    mkv.chapters_obj.editions[0].atoms.clear()

    assert other.chapters_obj is not None
    assert len(other.chapters_obj.editions[0].atoms) == 2  # noqa: PLR2004


@requires_mkvtoolnix
def test_add_file_edit_drops_chapters_of_added_file(get_path_test_file_with_chapters: Path, tmp_path: Path) -> None:
    mkv = MKVFile()
    mkv.add_file(str(get_path_test_file_with_chapters))
    assert mkv.chapters_obj is not None
    mkv.chapters_obj.editions[0].atoms[0].displays[0].string = "RENAMED"

    output = tmp_path / "out.mkv"
    mkv.mux(output, silent=True)

    atoms = _extract_chapters(output).editions[0].atoms
    assert [a.displays[0].string for a in atoms] == ["RENAMED", "Outro"]


@requires_mkvtoolnix
def test_add_file_keeps_chapters_of_first_file(
    get_path_test_file_with_chapters: Path,
    get_path_test_file_two: Path,
) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    mkv.add_file(str(get_path_test_file_two))

    assert mkv.chapters_obj is not None
    assert len(mkv.chapters_obj.editions[0].atoms) == 2  # noqa: PLR2004


@requires_mkvtoolnix
def test_add_file_does_not_replace_caller_chapters(
    get_path_test_file_with_chapters: Path,
    get_path_test_file_two: Path,
) -> None:
    mkv = MKVFile(str(get_path_test_file_two))
    mkv.add_chapter(ChapterAtom(time_start="00:00:00.000", displays=[ChapterDisplay(string="Mine")]))
    mkv.add_file(str(get_path_test_file_with_chapters))

    assert mkv.chapters_obj is not None
    assert [a.displays[0].string for a in mkv.chapters_obj.editions[0].atoms] == ["Mine"]


@requires_mkvtoolnix
def test_add_file_without_chapters_leaves_chapters_obj_none(get_path_test_file_two: Path) -> None:
    mkv = MKVFile()
    mkv.add_file(str(get_path_test_file_two))
    assert mkv.chapters_obj is None


@requires_mkvtoolnix
def test_command_adds_no_chapters_flag_only_for_edited_sources(get_path_test_file_with_chapters: Path) -> None:
    mkv = MKVFile(str(get_path_test_file_with_chapters))
    assert "--no-chapters" not in mkv.command("output.mkv", subprocess=True)

    mkv.add_chapter(ChapterAtom(time_start="00:00:02.000", displays=[ChapterDisplay(string="New")]))
    command = mkv.command("output.mkv", subprocess=True)

    assert command.count("--no-chapters") == 1
    assert command.count("--chapters") == 1


def test_command_rewrites_chapters_assigned_by_caller() -> None:
    """A chapters object that did not come from a source file is always written."""
    mkv = MKVFile()
    mkv.chapters_obj = Chapters()
    mkv.chapters_obj.add_simple_chapter("00:00:00.000", "Intro")

    command = mkv.command("output.mkv", subprocess=True)

    assert "--chapters" in command
    assert "--no-chapters" not in command
    assert mkv._temp_chapters_file is not None  # noqa: SLF001
    mkv.cleanup()


def test_command_skips_editions_without_atoms() -> None:
    mkv = MKVFile()
    mkv.chapters_obj = Chapters(editions=[EditionEntry(uid=1)])

    command = mkv.command("output.mkv", subprocess=True)

    assert "--chapters" not in command
    assert mkv._temp_chapters_file is None  # noqa: SLF001


def test_add_chapter_invalid_type_does_not_create_chapters() -> None:
    mkv = MKVFile()
    with pytest.raises(TypeError):
        mkv.add_chapter("nope")  # type: ignore[arg-type]
    assert mkv.chapters_obj is None


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
