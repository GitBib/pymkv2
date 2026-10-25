import logging
import xml.etree.ElementTree as ET

import msgspec
import pytest

from pymkv import chapters as chapters_module
from pymkv.chapters import (
    BinaryValue,
    ChapterAtom,
    ChapterProcess,
    ChapterProcessCommand,
    Chapters,
    ChapterTrack,
    EditionDisplay,
    EditionEntry,
    export_to_xml,
    parse_chapters_xml,
)

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


FULL_CHAPTERS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Chapters>
  <EditionEntry>
    <EditionUID>1</EditionUID>
    <EditionFlagHidden>0</EditionFlagHidden>
    <EditionFlagDefault>1</EditionFlagDefault>
    <EditionFlagOrdered>1</EditionFlagOrdered>
    <EditionDisplay>
      <EditionString>Director's cut</EditionString>
      <EditionLanguageIETF>en</EditionLanguageIETF>
      <EditionLanguageIETF>de</EditionLanguageIETF>
    </EditionDisplay>
    <ChapterAtom>
      <ChapterUID>10</ChapterUID>
      <ChapterStringUID>intro-uid</ChapterStringUID>
      <ChapterTimeStart>00:00:00.000000000</ChapterTimeStart>
      <ChapterTimeEnd>00:01:00.000000000</ChapterTimeEnd>
      <ChapterFlagHidden>1</ChapterFlagHidden>
      <ChapterFlagEnabled>0</ChapterFlagEnabled>
      <ChapterSegmentUID format="hex">0102030405060708090a0b0c0d0e0f10</ChapterSegmentUID>
      <ChapterSegmentEditionUID>7</ChapterSegmentEditionUID>
      <ChapterPhysicalEquiv>50</ChapterPhysicalEquiv>
      <ChapterTrack>
        <ChapterTrackNumber>1</ChapterTrackNumber>
        <ChapterTrackNumber>2</ChapterTrackNumber>
      </ChapterTrack>
      <ChapterDisplay>
        <ChapterString>Intro</ChapterString>
        <ChapterLanguage>chi</ChapterLanguage>
        <ChapLanguageIETF>zh-Hans</ChapLanguageIETF>
        <ChapLanguageIETF>zh-CN</ChapLanguageIETF>
        <ChapterCountry>cn</ChapterCountry>
      </ChapterDisplay>
      <ChapterDisplay>
        <ChapterString>Intro (en)</ChapterString>
        <ChapterLanguage>eng</ChapterLanguage>
      </ChapterDisplay>
      <ChapterProcess>
        <ChapterProcessCodecID>1</ChapterProcessCodecID>
        <ChapterProcessPrivate format="base64">AQID</ChapterProcessPrivate>
        <ChapterProcessCommand>
          <ChapterProcessTime>1</ChapterProcessTime>
          <ChapterProcessData format="hex">ff00</ChapterProcessData>
        </ChapterProcessCommand>
      </ChapterProcess>
      <ChapterAtom>
        <ChapterUID>11</ChapterUID>
        <ChapterTimeStart>00:00:30.000000000</ChapterTimeStart>
        <ChapterPhysicalEquiv>40</ChapterPhysicalEquiv>
        <ChapterDisplay>
          <ChapterString>Nested</ChapterString>
          <ChapterLanguage>eng</ChapterLanguage>
        </ChapterDisplay>
      </ChapterAtom>
    </ChapterAtom>
  </EditionEntry>
</Chapters>
"""


def _xml_tags(structs: list[type[msgspec.Struct]]) -> set[str]:
    return {
        info.encode_name
        for struct in structs
        for info in msgspec.structs.fields(struct)
        if info.encode_name[0] not in "@#"
    }


def test_parse_chapters_xml_all_elements() -> None:
    chapters = parse_chapters_xml(FULL_CHAPTERS_XML)

    edition = chapters.editions[0]
    assert (edition.uid, edition.hidden, edition.default, edition.ordered) == (1, False, True, True)
    assert edition.displays == [EditionDisplay(string="Director's cut", language_ietf=["en", "de"])]

    atom = edition.atoms[0]
    assert atom.uid == 10  # noqa: PLR2004
    assert atom.string_uid == "intro-uid"
    assert (atom.time_start, atom.time_end) == ("00:00:00.000000000", "00:01:00.000000000")
    assert (atom.hidden, atom.enabled) == (True, False)
    assert atom.segment_uid == BinaryValue(value="0102030405060708090a0b0c0d0e0f10", format="hex")
    assert atom.segment_edition_uid == 7  # noqa: PLR2004
    assert atom.physical_equiv == 50  # noqa: PLR2004
    assert atom.track == ChapterTrack(numbers=[1, 2])

    assert [d.string for d in atom.displays] == ["Intro", "Intro (en)"]
    assert atom.displays[0].language == "chi"
    assert atom.displays[0].language_ietf == ["zh-Hans", "zh-CN"]
    assert atom.displays[0].country == "cn"

    assert atom.processes == [
        ChapterProcess(
            codec_id=1,
            private=BinaryValue(value="AQID", format="base64"),
            commands=[ChapterProcessCommand(time=1, data=BinaryValue(value="ff00", format="hex"))],
        )
    ]

    nested = atom.atoms[0]
    assert nested.uid == 11  # noqa: PLR2004
    assert nested.physical_equiv == 40  # noqa: PLR2004


def test_parse_chapters_xml_all_elements_survive_export_roundtrip() -> None:
    chapters = parse_chapters_xml(FULL_CHAPTERS_XML)

    assert parse_chapters_xml(export_to_xml(chapters)) == chapters


def test_export_writes_binary_format_attribute() -> None:
    xml = export_to_xml(parse_chapters_xml(FULL_CHAPTERS_XML))

    assert '<ChapterSegmentUID format="hex">0102030405060708090a0b0c0d0e0f10</ChapterSegmentUID>' in xml
    assert '<ChapterProcessPrivate format="base64">AQID</ChapterProcessPrivate>' in xml


def test_binary_value_without_format_has_no_attribute() -> None:
    atom = ChapterAtom(time_start="00:00:00.000", segment_uid=BinaryValue(value="aabb"))
    xml = export_to_xml(Chapters(editions=[EditionEntry(atoms=[atom])]))

    assert "<ChapterSegmentUID>aabb</ChapterSegmentUID>" in xml


def test_parser_covers_every_struct_field() -> None:
    """Every XML element modeled by the structs is present in the full sample and parsed."""
    structs: list[type[msgspec.Struct]] = [
        chapters_module.Chapters,
        chapters_module.EditionEntry,
        chapters_module.EditionDisplay,
        chapters_module.ChapterAtom,
        chapters_module.ChapterTrack,
        chapters_module.ChapterDisplay,
        chapters_module.ChapterProcess,
        chapters_module.ChapterProcessCommand,
        chapters_module.BinaryValue,
    ]
    expected = _xml_tags(structs)

    sample_tags = {element.tag for element in ET.fromstring(FULL_CHAPTERS_XML).iter()}  # noqa: S314
    exported = ET.fromstring(export_to_xml(parse_chapters_xml(FULL_CHAPTERS_XML)))  # noqa: S314
    exported_tags = {element.tag for element in exported.iter()}

    assert expected <= sample_tags
    assert expected <= exported_tags


def test_parse_chapters_xml_warns_about_unknown_elements(caplog: pytest.LogCaptureFixture) -> None:
    xml = """<Chapters><EditionEntry><ChapterAtom>
      <ChapterTimeStart>00:00:00.000</ChapterTimeStart>
      <SomethingNew>1</SomethingNew>
    </ChapterAtom></EditionEntry></Chapters>"""

    with caplog.at_level(logging.WARNING):
        chapters = parse_chapters_xml(xml)

    assert chapters.editions[0].atoms[0].time_start == "00:00:00.000"
    assert "SomethingNew" in caplog.text


def test_parse_chapters_xml_no_warning_for_supported_elements(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        parse_chapters_xml(FULL_CHAPTERS_XML)

    assert caplog.records == []


@pytest.mark.parametrize("as_bytes", [False, True])
def test_parse_chapters_xml_accepts_bom(as_bytes: bool) -> None:
    content: str | bytes = "\ufeff" + SIMPLE_CHAPTERS_XML
    if as_bytes:
        content = content.encode("utf-8")  # type: ignore[union-attr]

    assert len(parse_chapters_xml(content).editions) == 1


def test_parse_chapters_xml_ignores_invalid_scalars() -> None:
    xml = """<Chapters><EditionEntry>
      <EditionUID>abc</EditionUID>
      <EditionFlagHidden>maybe</EditionFlagHidden>
      <ChapterAtom>
        <ChapterTimeStart>00:00:00.000</ChapterTimeStart>
        <ChapterPhysicalEquiv></ChapterPhysicalEquiv>
        <ChapterDisplay><ChapterString>A</ChapterString></ChapterDisplay>
      </ChapterAtom>
    </EditionEntry></Chapters>"""

    edition = parse_chapters_xml(xml).editions[0]

    assert edition.uid is None
    assert edition.hidden is None
    assert edition.atoms[0].physical_equiv is None


def test_parse_chapters_xml_missing_required_strings_default_to_empty() -> None:
    xml = """<Chapters><EditionEntry><ChapterAtom>
      <ChapterDisplay><ChapterLanguage>eng</ChapterLanguage></ChapterDisplay>
    </ChapterAtom></EditionEntry></Chapters>"""

    atom = parse_chapters_xml(xml).editions[0].atoms[0]

    assert atom.time_start == ""
    assert atom.displays[0].string == ""
