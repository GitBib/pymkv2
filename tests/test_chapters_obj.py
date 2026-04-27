import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pymkv import MKVFile
from pymkv.chapters import ChapterAtom, ChapterDisplay, Chapters, EditionEntry, _dict_to_xml, export_to_xml


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


def test_chapter_bool_flags_in_xml() -> None:
    atom = ChapterAtom(time_start="00:00:00", hidden=True, enabled=False)
    chapters = Chapters(editions=[EditionEntry(atoms=[atom])])
    xml = export_to_xml(chapters)
    assert "<ChapterFlagHidden>1</ChapterFlagHidden>" in xml
    assert "<ChapterFlagEnabled>0</ChapterFlagEnabled>" in xml


def test_add_simple_chapter_non_default_language() -> None:
    chapters = Chapters()
    chapters.add_simple_chapter("00:01:00.000", "Chapter", language="jpn")
    xml = export_to_xml(chapters)
    assert "<ChapterLanguage>jpn</ChapterLanguage>" in xml


def test_edition_entry_bool_flags() -> None:
    edition = EditionEntry(hidden=True, default=True, ordered=True, atoms=[ChapterAtom(time_start="00:00:00")])
    chapters = Chapters(editions=[edition])
    xml = export_to_xml(chapters)
    assert "<EditionFlagHidden>1</EditionFlagHidden>" in xml
    assert "<EditionFlagDefault>1</EditionFlagDefault>" in xml
    assert "<EditionFlagOrdered>1</EditionFlagOrdered>" in xml


def test_add_chapter_type_error() -> None:
    mkv = MKVFile()
    with pytest.raises(TypeError, match="chapter must be ChapterAtom or EditionEntry"):
        mkv.add_chapter("not a valid chapter")  # type: ignore[arg-type]


def test_dict_to_xml_non_dict_list_items() -> None:
    root = ET.Element("Root")
    _dict_to_xml(root, {"Tags": ["value1", "value2"]})
    tags_elements = root.findall("Tags")
    assert len(tags_elements) == 2  # noqa: PLR2004
    assert tags_elements[0].text == "value1"
    assert tags_elements[1].text == "value2"


def test_dict_to_xml_nested_dict() -> None:
    root = ET.Element("Root")
    _dict_to_xml(root, {"Outer": {"Inner": "value"}})
    outer = root.find("Outer")
    assert outer is not None
    inner = outer.find("Inner")
    assert inner is not None
    assert inner.text == "value"
