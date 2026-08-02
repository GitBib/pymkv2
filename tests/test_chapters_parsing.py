import xml.etree.ElementTree as ET

import pytest

from pymkv.chapters import Chapters, export_to_xml, parse_chapters_xml

SIMPLE_CHAPTERS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Chapters>
  <EditionEntry>
    <EditionUID>1000000000</EditionUID>
    <EditionFlagDefault>1</EditionFlagDefault>
    <EditionFlagHidden>0</EditionFlagHidden>
    <ChapterAtom>
      <ChapterUID>  </ChapterUID>
      <ChapterTimeStart>00:00:00.000000000</ChapterTimeStart>
      <ChapterTimeEnd>00:05:00.000000000</ChapterTimeEnd>
      <ChapterFlagHidden>0</ChapterFlagHidden>
      <ChapterFlagEnabled>1</ChapterFlagEnabled>
      <ChapterDisplay>
        <ChapterString>Intro</ChapterString>
        <ChapterLanguage>eng</ChapterLanguage>
      </ChapterDisplay>
    </ChapterAtom>
    <ChapterAtom>
      <ChapterUID>2000000002</ChapterUID>
      <ChapterTimeStart>00:05:00.000000000</ChapterTimeStart>
      <ChapterDisplay>
        <ChapterString>Chapter 2</ChapterString>
        <ChapterLanguage>eng</ChapterLanguage>
      </ChapterDisplay>
    </ChapterAtom>
    <ChapterAtom>
      <ChapterUID>not-a-number</ChapterUID>
      <ChapterTimeStart>00:15:00.000000000</ChapterTimeStart>
      <ChapterDisplay>
        <ChapterString>Invalid UID</ChapterString>
      </ChapterDisplay>
    </ChapterAtom>
  </EditionEntry>
</Chapters>
"""

NESTED_CHAPTERS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Chapters>
  <EditionEntry>
    <ChapterAtom>
      <ChapterTimeStart>00:00:00.000000000</ChapterTimeStart>
      <ChapterDisplay>
        <ChapterString>Parent</ChapterString>
      </ChapterDisplay>
      <ChapterAtom>
        <ChapterTimeStart>00:01:00.000000000</ChapterTimeStart>
        <ChapterDisplay>
          <ChapterString>Nested</ChapterString>
          <ChapterCountry>us</ChapterCountry>
        </ChapterDisplay>
      </ChapterAtom>
    </ChapterAtom>
  </EditionEntry>
</Chapters>
"""

MULTI_EDITION_CHAPTERS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Chapters>
  <EditionEntry>
    <EditionUID>1</EditionUID>
    <ChapterAtom>
      <ChapterTimeStart>00:00:00.000000000</ChapterTimeStart>
      <ChapterDisplay>
        <ChapterString>Edition 1 Chapter</ChapterString>
      </ChapterDisplay>
    </ChapterAtom>
  </EditionEntry>
  <EditionEntry>
    <EditionUID>2</EditionUID>
    <EditionFlagOrdered>1</EditionFlagOrdered>
    <ChapterAtom>
      <ChapterTimeStart>00:00:00.000000000</ChapterTimeStart>
      <ChapterDisplay>
        <ChapterString>Edition 2 Chapter</ChapterString>
      </ChapterDisplay>
    </ChapterAtom>
  </EditionEntry>
</Chapters>
"""

NO_EDITIONS_CHAPTERS_XML = '<?xml version="1.0" encoding="UTF-8"?>\n<Chapters></Chapters>\n'


def test_parse_chapters_xml_returns_chapters_instance() -> None:
    chapters = parse_chapters_xml(SIMPLE_CHAPTERS_XML)
    assert isinstance(chapters, Chapters)


def test_parse_chapters_xml_simple_edition_and_atoms() -> None:
    chapters = parse_chapters_xml(SIMPLE_CHAPTERS_XML)

    assert len(chapters.editions) == 1
    edition = chapters.editions[0]
    assert edition.uid == 1000000000  # noqa: PLR2004
    assert edition.default is True
    assert edition.hidden is False

    assert len(edition.atoms) == 3  # noqa: PLR2004
    first, second, invalid_uid = edition.atoms

    assert first.uid is None  # blank text
    assert first.time_start == "00:00:00.000000000"
    assert first.time_end == "00:05:00.000000000"
    assert first.hidden is False
    assert first.enabled is True
    assert len(first.displays) == 1
    assert first.displays[0].string == "Intro"
    assert first.displays[0].language == "eng"

    assert second.uid == 2000000002  # noqa: PLR2004
    assert second.time_end is None
    assert second.displays[0].string == "Chapter 2"

    assert invalid_uid.uid is None  # non-numeric
    assert invalid_uid.displays[0].string == "Invalid UID"


def test_parse_chapters_xml_nested_atoms() -> None:
    chapters = parse_chapters_xml(NESTED_CHAPTERS_XML)

    edition = chapters.editions[0]
    parent = edition.atoms[0]
    assert parent.displays[0].string == "Parent"
    assert len(parent.atoms) == 1

    nested = parent.atoms[0]
    assert nested.displays[0].string == "Nested"
    assert nested.displays[0].country == "us"
    # Language falls back to the default when not specified in the XML.
    assert nested.displays[0].language == "eng"


def test_parse_chapters_xml_multiple_editions() -> None:
    chapters = parse_chapters_xml(MULTI_EDITION_CHAPTERS_XML)

    assert len(chapters.editions) == 2  # noqa: PLR2004
    assert chapters.editions[0].uid == 1
    assert chapters.editions[1].uid == 2  # noqa: PLR2004
    assert chapters.editions[1].ordered is True
    assert chapters.editions[0].atoms[0].displays[0].string == "Edition 1 Chapter"
    assert chapters.editions[1].atoms[0].displays[0].string == "Edition 2 Chapter"


def test_parse_chapters_xml_no_editions() -> None:
    chapters = parse_chapters_xml(NO_EDITIONS_CHAPTERS_XML)
    assert chapters.editions == []


def test_parse_chapters_xml_invalid_xml_raises() -> None:
    with pytest.raises(ET.ParseError):
        parse_chapters_xml("<Chapters><EditionEntry>")


def test_parse_chapters_xml_accepts_bytes() -> None:
    chapters = parse_chapters_xml(SIMPLE_CHAPTERS_XML.encode("utf-8"))
    assert len(chapters.editions) == 1


def test_parse_chapters_xml_roundtrip_with_export() -> None:
    """A chapters object built by hand should survive an export -> parse round trip."""
    chapters = Chapters()
    chapters.add_simple_chapter("00:00:00.000", "Intro", language="eng")
    chapters.add_simple_chapter("00:10:00.000", "Part 2", language="eng")

    xml_content = export_to_xml(chapters)
    reparsed = parse_chapters_xml(xml_content)

    assert len(reparsed.editions) == 1
    assert len(reparsed.editions[0].atoms) == 2  # noqa: PLR2004
    assert reparsed.editions[0].atoms[0].displays[0].string == "Intro"
    assert reparsed.editions[0].atoms[0].time_start == "00:00:00.000"
    assert reparsed.editions[0].atoms[1].displays[0].string == "Part 2"
