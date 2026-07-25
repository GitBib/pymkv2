"""
This module provides classes for creating and managing Matroska chapters programmatically.

It uses `msgspec` structs to represent the hierarchical structure of chapters
(EditionEntry -> ChapterAtom -> ChapterDisplay)
and provides functionality to export these structures to the XML format required by `mkvmerge`.

Examples
--------
>>> from pymkv.chapters import Chapters, ChapterAtom, ChapterDisplay  # doctest: +SKIP
>>>
>>> # Create the container
>>> chapters = Chapters()
>>>
>>> # Method 1: Use helper for simple chapters
>>> chapters.add_simple_chapter("00:00:00.000", "Intro")
>>>
>>> # Method 2: Create complex nested chapters
>>> display = ChapterDisplay(string="Nested Chapter", language="eng")
>>> atom = ChapterAtom(time_start="00:05:00.000", displays=[display])
>>>
>>> parent = ChapterAtom(time_start="00:01:00.000", atoms=[atom])
>>>
>>> # Add to manually created edition
>>> from pymkv.chapters import EditionEntry  # doctest: +SKIP
>>> edition = EditionEntry(atoms=[parent])
>>> chapters.editions.append(edition)
>>>
>>> # Export to XML
>>> xml_content = export_to_xml(chapters)  # doctest: +SKIP
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import msgspec


class ChapterDisplay(msgspec.Struct):
    """
    Display properties for a chapter.
    """

    string: str = msgspec.field(name="ChapterString")
    language: str = msgspec.field(name="ChapterLanguage", default="eng")
    country: str | None = msgspec.field(name="ChapterCountry", default=None)


class ChapterAtom(msgspec.Struct):
    """
    A single chapter atom.

    Examples
    --------
    >>> from pymkv.chapters import ChapterAtom, ChapterDisplay  # doctest: +SKIP
    >>>
    >>> # Simple chapter with title
    >>> atom = ChapterAtom(
    ...     time_start="00:00:10.000",
    ...     displays=[ChapterDisplay(string="Chapter 1")]
    ... )
    >>>
    >>> # Nested chapters
    >>> parent = ChapterAtom(
    ...     time_start="00:00:00.000",
    ...     atoms=[
    ...         ChapterAtom(time_start="00:05:00.000")
    ...     ]
    ... )
    """

    time_start: str = msgspec.field(name="ChapterTimeStart")
    time_end: str | None = msgspec.field(name="ChapterTimeEnd", default=None)
    uid: int | None = msgspec.field(name="ChapterUID", default=None)
    hidden: bool | None = msgspec.field(name="ChapterFlagHidden", default=None)
    enabled: bool | None = msgspec.field(name="ChapterFlagEnabled", default=None)
    displays: list[ChapterDisplay] = msgspec.field(name="ChapterDisplay", default_factory=list)
    atoms: list[ChapterAtom] = msgspec.field(name="ChapterAtom", default_factory=list)


class EditionEntry(msgspec.Struct):
    """
    An edition entry containing chapters.
    """

    uid: int | None = msgspec.field(name="EditionUID", default=None)
    hidden: bool | None = msgspec.field(name="EditionFlagHidden", default=None)
    default: bool | None = msgspec.field(name="EditionFlagDefault", default=None)
    ordered: bool | None = msgspec.field(name="EditionFlagOrdered", default=None)
    atoms: list[ChapterAtom] = msgspec.field(name="ChapterAtom", default_factory=list)


class Chapters(msgspec.Struct):
    """
    Root container for chapters.

    Examples
    --------
    >>> from pymkv.chapters import Chapters, ChapterAtom  # doctest: +SKIP
    >>>
    >>> # Create and export
    >>> chapters = Chapters()
    >>> chapters.add_simple_chapter("00:00:00.000", "Intro")
    >>> xml = export_to_xml(chapters)
    """

    editions: list[EditionEntry] = msgspec.field(name="EditionEntry", default_factory=list)

    def add_simple_chapter(self, time_start: str, title: str, language: str = "eng") -> None:
        """
        Helper to add a simple chapter to the first edition (creates one if needed).
        """
        if not self.editions:
            self.editions.append(EditionEntry())

        display = ChapterDisplay(string=title, language=language)
        atom = ChapterAtom(time_start=time_start, displays=[display])
        self.editions[0].atoms.append(atom)


def _dict_to_xml(parent: ET.Element, data: dict[str, Any]) -> None:
    """
    Recursively convert a dictionary to XML elements appended to parent.
    """
    for key, value in data.items():
        if value is None:
            continue

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    sub_element = ET.SubElement(parent, key)
                    _dict_to_xml(sub_element, item)
                else:
                    sub_element = ET.SubElement(parent, key)
                    sub_element.text = str(item)
        elif isinstance(value, dict):
            sub_element = ET.SubElement(parent, key)
            _dict_to_xml(sub_element, value)
        else:
            sub_element = ET.SubElement(parent, key)
            if isinstance(value, bool):
                sub_element.text = "1" if value else "0"
            else:
                sub_element.text = str(value)


def export_to_xml(chapters: Chapters) -> str:
    """
    Export Chapters object to XML string.
    """
    # Convert struct to dict
    data = msgspec.to_builtins(chapters)

    root = ET.Element("Chapters")

    _dict_to_xml(root, data)

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    return xml_bytes.decode("utf-8")


def _text_to_bool(value: str | None) -> bool | None:
    """
    Convert a Matroska chapter XML flag ("0"/"1") to a bool, preserving ``None``.
    """
    if value is None:
        return None
    return value.strip() == "1"


def _text_to_int(value: str | None) -> int | None:
    """
    Convert element text to an int, preserving ``None`` and tolerating blank/invalid values.
    """
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_chapter_display(element: ET.Element) -> dict[str, Any]:
    """
    Parse a single ``<ChapterDisplay>`` element into a dict matching :class:`ChapterDisplay`.
    """
    return {
        "ChapterString": element.findtext("ChapterString") or "",
        "ChapterLanguage": element.findtext("ChapterLanguage") or "und",
        "ChapterCountry": element.findtext("ChapterCountry"),
    }


def _parse_chapter_atom(element: ET.Element) -> dict[str, Any]:
    """
    Recursively parse a ``<ChapterAtom>`` element into a dict matching :class:`ChapterAtom`.
    """
    return {
        "ChapterTimeStart": element.findtext("ChapterTimeStart") or "",
        "ChapterTimeEnd": element.findtext("ChapterTimeEnd"),
        "ChapterUID": _text_to_int(element.findtext("ChapterUID")),
        "ChapterFlagHidden": _text_to_bool(element.findtext("ChapterFlagHidden")),
        "ChapterFlagEnabled": _text_to_bool(element.findtext("ChapterFlagEnabled")),
        "ChapterDisplay": [_parse_chapter_display(d) for d in element.findall("ChapterDisplay")],
        "ChapterAtom": [_parse_chapter_atom(a) for a in element.findall("ChapterAtom")],
    }


def _parse_edition_entry(element: ET.Element) -> dict[str, Any]:
    """
    Parse a single ``<EditionEntry>`` element into a dict matching :class:`EditionEntry`.
    """
    return {
        "EditionUID": _text_to_int(element.findtext("EditionUID")),
        "EditionFlagHidden": _text_to_bool(element.findtext("EditionFlagHidden")),
        "EditionFlagDefault": _text_to_bool(element.findtext("EditionFlagDefault")),
        "EditionFlagOrdered": _text_to_bool(element.findtext("EditionFlagOrdered")),
        "ChapterAtom": [_parse_chapter_atom(a) for a in element.findall("ChapterAtom")],
    }


def parse_chapters_xml(xml_content: str | bytes) -> Chapters:
    """
    Parse a Matroska chapters XML document (such as the output of ``mkvextract chapters``)
    into a :class:`Chapters` object.

    Parameters
    ----------
    xml_content : str | bytes
        The XML content to parse, as returned by ``mkvextract chapters <file>``.

    Returns
    -------
    Chapters
        The parsed chapters, with one :class:`EditionEntry` per ``<EditionEntry>`` element.

    Raises
    ------
    xml.etree.ElementTree.ParseError
        If `xml_content` is not well-formed XML.

    Examples
    --------
    >>> xml = '''<?xml version="1.0"?>
    ... <Chapters>
    ...   <EditionEntry>
    ...     <ChapterAtom>
    ...       <ChapterTimeStart>00:00:00.000</ChapterTimeStart>
    ...       <ChapterDisplay>
    ...         <ChapterString>Intro</ChapterString>
    ...         <ChapterLanguage>eng</ChapterLanguage>
    ...       </ChapterDisplay>
    ...     </ChapterAtom>
    ...   </EditionEntry>
    ... </Chapters>'''
    >>> chapters = parse_chapters_xml(xml)
    >>> chapters.editions[0].atoms[0].displays[0].string
    'Intro'
    """
    root = ET.fromstring(xml_content)  # noqa: S314
    data = {"EditionEntry": [_parse_edition_entry(e) for e in root.findall("EditionEntry")]}
    return msgspec.convert(data, type=Chapters, strict=False)
