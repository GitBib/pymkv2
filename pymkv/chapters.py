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

import functools
import logging
import types
import xml.etree.ElementTree as ET
from typing import Any, Union, get_args, get_origin, get_type_hints

import msgspec

# Struct field names starting with "@" map to XML attributes, "#text" maps to the element text.
_ATTRIBUTE_PREFIX = "@"
_TEXT_KEY = "#text"


class BinaryValue(msgspec.Struct):
    """
    Binary element payload together with its ``format`` attribute (``hex`` or ``base64``).
    """

    value: str = msgspec.field(name=_TEXT_KEY)
    format: str | None = msgspec.field(name="@format", default=None)


class ChapterDisplay(msgspec.Struct):
    """
    Display properties for a chapter.
    """

    string: str = msgspec.field(name="ChapterString")
    language: str = msgspec.field(name="ChapterLanguage", default="eng")
    country: str | None = msgspec.field(name="ChapterCountry", default=None)
    language_ietf: list[str] = msgspec.field(name="ChapLanguageIETF", default_factory=list)


class ChapterTrack(msgspec.Struct):
    """
    Tracks a chapter applies to. An empty list means all tracks.
    """

    numbers: list[int] = msgspec.field(name="ChapterTrackNumber", default_factory=list)


class ChapterProcessCommand(msgspec.Struct):
    """
    A single command of a chapter process (``ChapterProcessCommand``).
    """

    time: int | None = msgspec.field(name="ChapterProcessTime", default=None)
    data: BinaryValue | None = msgspec.field(name="ChapterProcessData", default=None)


class ChapterProcess(msgspec.Struct):
    """
    Chapter codec process (``ChapterProcess``).
    """

    codec_id: int | None = msgspec.field(name="ChapterProcessCodecID", default=None)
    private: BinaryValue | None = msgspec.field(name="ChapterProcessPrivate", default=None)
    commands: list[ChapterProcessCommand] = msgspec.field(name="ChapterProcessCommand", default_factory=list)


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
    string_uid: str | None = msgspec.field(name="ChapterStringUID", default=None)
    segment_uid: BinaryValue | None = msgspec.field(name="ChapterSegmentUID", default=None)
    segment_edition_uid: int | None = msgspec.field(name="ChapterSegmentEditionUID", default=None)
    physical_equiv: int | None = msgspec.field(name="ChapterPhysicalEquiv", default=None)
    track: ChapterTrack | None = msgspec.field(name="ChapterTrack", default=None)
    processes: list[ChapterProcess] = msgspec.field(name="ChapterProcess", default_factory=list)


class EditionDisplay(msgspec.Struct):
    """
    Display properties of an edition.
    """

    string: str = msgspec.field(name="EditionString")
    language_ietf: list[str] = msgspec.field(name="EditionLanguageIETF", default_factory=list)


class EditionEntry(msgspec.Struct):
    """
    An edition entry containing chapters.
    """

    uid: int | None = msgspec.field(name="EditionUID", default=None)
    hidden: bool | None = msgspec.field(name="EditionFlagHidden", default=None)
    default: bool | None = msgspec.field(name="EditionFlagDefault", default=None)
    ordered: bool | None = msgspec.field(name="EditionFlagOrdered", default=None)
    atoms: list[ChapterAtom] = msgspec.field(name="ChapterAtom", default_factory=list)
    displays: list[EditionDisplay] = msgspec.field(name="EditionDisplay", default_factory=list)


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

    Keys starting with ``@`` become attributes and the ``#text`` key becomes the element text.
    """
    for key, value in data.items():
        if value is None:
            continue

        if key == _TEXT_KEY:
            parent.text = str(value)
        elif key.startswith(_ATTRIBUTE_PREFIX):
            parent.set(key[len(_ATTRIBUTE_PREFIX) :], str(value))
        elif isinstance(value, list):
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


def _unwrap_optional(tp: Any) -> Any:  # noqa: ANN401
    """
    Return ``X`` for ``X | None``, otherwise the type unchanged.
    """
    if get_origin(tp) in (Union, types.UnionType):
        args = [arg for arg in get_args(tp) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return tp


def _is_struct(tp: Any) -> bool:  # noqa: ANN401
    return isinstance(tp, type) and issubclass(tp, msgspec.Struct)


@functools.cache
def _schema(cls: type[msgspec.Struct]) -> tuple[tuple[msgspec.structs.FieldInfo, Any], ...]:
    """
    Return the fields of a struct paired with their resolved, non-optional types.
    """
    hints = get_type_hints(cls)
    return tuple((info, _unwrap_optional(hints[info.name])) for info in msgspec.structs.fields(cls))


def _convert_scalar(text: str | None, tp: type) -> Any:  # noqa: ANN401
    """
    Convert XML text to ``tp`` (str, int or bool); blank or invalid values give ``None``.
    """
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    if tp is bool:
        return {"1": True, "0": False}.get(text)
    if tp is int:
        try:
            return int(text)
        except ValueError:
            return None
    return text


def _parse_children(children: list[ET.Element], tp: Any, unknown: set[str]) -> Any:  # noqa: ANN401
    """
    Parse the child elements sharing one tag according to the field type ``tp``.
    """
    if get_origin(tp) is list:
        (item_type,) = get_args(tp)
        if _is_struct(item_type):
            return [_parse_struct(child, item_type, unknown) for child in children]
        values = (_convert_scalar(child.text, item_type) for child in children)
        return [value for value in values if value is not None]
    if not children:
        return None
    if _is_struct(tp):
        return _parse_struct(children[0], tp, unknown)
    return _convert_scalar(children[0].text, tp)


def _parse_struct(element: ET.Element, cls: type[msgspec.Struct], unknown: set[str]) -> dict[str, Any]:
    """
    Parse an XML element into a dict keyed by the XML names of ``cls``.

    Child tags that ``cls`` does not model are added to ``unknown``.
    """
    data: dict[str, Any] = {}
    known: set[str] = set()
    for info, tp in _schema(cls):  # type: ignore[arg-type]
        tag = info.encode_name
        if tag == _TEXT_KEY:
            value = _convert_scalar(element.text, tp)
        elif tag.startswith(_ATTRIBUTE_PREFIX):
            value = _convert_scalar(element.get(tag[len(_ATTRIBUTE_PREFIX) :]), tp)
        else:
            known.add(tag)
            value = _parse_children(element.findall(tag), tp, unknown)

        if value is None and info.required and tp is str:
            value = ""
        if value is not None:
            data[tag] = value

    unknown.update(child.tag for child in element if child.tag not in known)
    return data


def parse_chapters_xml(xml_content: str | bytes) -> Chapters:
    """
    Parse a Matroska chapters XML document (such as the output of ``mkvextract chapters``)
    into a :class:`Chapters` object.

    Every element of the mkvmerge chapter XML format is supported. Elements that are not part of
    the supported format are skipped with a logged warning.

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
    if isinstance(xml_content, str):
        xml_content = xml_content.lstrip("\ufeff")
    root = ET.fromstring(xml_content)  # noqa: S314
    unknown: set[str] = set()
    data = _parse_struct(root, Chapters, unknown)
    if unknown:
        logging.warning("Ignoring unsupported chapter XML elements: %s", ", ".join(sorted(unknown)))
    return msgspec.convert(data, type=Chapters, strict=False)
