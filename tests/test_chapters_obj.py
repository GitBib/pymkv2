from pathlib import Path

from pymkv import MKVFile
from pymkv.chapters import ChapterAtom, ChapterDisplay, Chapters, EditionEntry, export_to_xml


def test_xml_export_simple() -> None:
    chapters = Chapters()
    chapters.add_simple_chapter("00:00:00.000", "Intro")

    xml = export_to_xml(chapters)

    # Basic containment checks
    assert "<Chapters>" in xml
    assert "<EditionEntry>" in xml
    assert "<ChapterAtom>" in xml
    assert "<ChapterTimeStart>00:00:00.000</ChapterTimeStart>" in xml
    assert "<ChapterString>Intro</ChapterString>" in xml
    assert "<ChapterLanguage>eng</ChapterLanguage>" in xml


def test_xml_export_nested() -> None:
    # Manual construction
    display = ChapterDisplay(string="Nested Chapter")
    child_atom = ChapterAtom(time_start="00:05:00.000", displays=[display])

    parent_atom = ChapterAtom(time_start="00:01:00.000", atoms=[child_atom])

    chapters = Chapters(editions=[EditionEntry(atoms=[parent_atom])])

    xml = export_to_xml(chapters)

    assert "<ChapterAtom>" in xml
    # Should appear twice (parent and child)
    assert xml.count("<ChapterAtom>") == 2  # noqa: PLR2004
    assert "<ChapterString>Nested Chapter</ChapterString>" in xml


def test_mkvfile_integration() -> None:
    mkv = MKVFile()

    # Add chapter object
    chapter = ChapterAtom(time_start="00:00:10.000", displays=[ChapterDisplay(string="My Chapter")])
    mkv.add_chapter(chapter)

    assert mkv.chapters_obj is not None
    assert len(mkv.chapters_obj.editions) == 1
    assert len(mkv.chapters_obj.editions[0].atoms) == 1

    # Generate command - this should trigger XML generation
    _ = mkv.command("output.mkv")

    # Check that a temp file was created for chapters
    assert mkv._chapters_file is not None  # noqa: SLF001
    assert mkv._temp_chapters_file is not None  # noqa: SLF001
    assert mkv._chapters_file == mkv._temp_chapters_file  # noqa: SLF001
    assert Path(mkv._chapters_file).exists()  # noqa: SLF001

    # Read the temp file to verify content
    with Path(mkv._chapters_file).open() as f:  # noqa: SLF001
        content = f.read()
        assert "<ChapterString>My Chapter</ChapterString>" in content

    # Cleanup (usually done by context or explicit deletion, testing manual here)
    Path(mkv._chapters_file).unlink()  # noqa: SLF001


def test_add_chapter_types() -> None:
    mkv = MKVFile()

    # Add EditionEntry
    edition = EditionEntry(uid=123)
    mkv.add_chapter(edition)
    assert mkv.chapters_obj is not None
    assert len(mkv.chapters_obj.editions) == 1
    assert mkv.chapters_obj.editions[0].uid == 123  # noqa: PLR2004

    # Add ChapterAtom (should go to first edition)
    atom = ChapterAtom(time_start="00:00:01")
    mkv.add_chapter(atom)
    assert len(mkv.chapters_obj.editions) == 1
    assert mkv.chapters_obj.editions[0].atoms[0] == atom
