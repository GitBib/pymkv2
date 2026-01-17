"""Data models for parsing mkvmerge JSON output using msgspec.

This module defines structures that map to the JSON output of `mkvmerge -J`.

Examples
--------
>>> from pymkv.models import MkvMergeOutput  # doctest: +SKIP
>>> # data = msgspec.json.decode(json_bytes, type=MkvMergeOutput)  # doctest: +SKIP
"""

from __future__ import annotations

import msgspec


class TrackProperties(msgspec.Struct, kw_only=True):  # type: ignore[call-arg]
    """
    Properties of a track as returned by `mkvmerge -J`.

    Attributes
    ----------
    track_name : str | None
        The name of the track.
    language : str | None
        The language of the track (ISO 639-2).
    language_ietf : str | None
        The language of the track (BCP 47).
    default_track : bool
        Whether the track is the default track of its type.
    forced_track : bool
        Whether the track is forced.
    flag_commentary : bool
        Whether the track is a commentary track.
    flag_hearing_impaired : bool
        Whether the track is for the hearing impaired.
    flag_visual_impaired : bool
        Whether the track is for the visually impaired.
    flag_original : bool
        Whether the track is the original language.
    """

    track_name: str | None = None
    language: str | None = None
    language_ietf: str | None = None
    default_track: bool = False
    forced_track: bool = False
    flag_commentary: bool = False
    flag_hearing_impaired: bool = False
    flag_visual_impaired: bool = False
    flag_original: bool = False


class TrackInfo(msgspec.Struct):
    """
    Information about a track.

    Attributes
    ----------
    id : int
        The ID of the track.
    type : str
        The type of the track (e.g., 'video', 'audio').
    codec : str
        The codec used by the track.
    properties : TrackProperties
        The properties of the track.
    num_entries : int | None
        The number of tag entries, if available.
    start_pts : int
        The starting timestamp of the track.
    """

    id: int
    type: str
    codec: str
    properties: TrackProperties = msgspec.field(default_factory=TrackProperties)
    num_entries: int | None = None
    start_pts: int = 0


class ContainerProperties(msgspec.Struct):
    """
    Properties of the container.

    Attributes
    ----------
    title : str | None
        The title of the container.
    """

    title: str | None = None


class ContainerInfo(msgspec.Struct):
    """
    Information about the container.

    Attributes
    ----------
    properties : ContainerProperties
        The properties of the container.
    supported : bool
        Whether the container is supported.
    recognized : bool
        Whether the container is recognized.
    type : str | None
        The type of the container.
    """

    properties: ContainerProperties = msgspec.field(default_factory=ContainerProperties)
    supported: bool = True
    recognized: bool = True
    type: str | None = None


class TagEntry(msgspec.Struct):
    """
    Tag entry information.

    Attributes
    ----------
    num_entries : int
        The number of entries in the tag.
    track_id : int | None
        The ID of the track associated with the tag.
    """

    num_entries: int = 0
    track_id: int | None = None


class AttachmentProperties(msgspec.Struct):
    """
    Properties of an attachment.

    Attributes
    ----------
    name : str | None
        The name of the attachment.
    description : str | None
        The description of the attachment.
    mime_type : str | None
        The MIME type of the attachment.
    """

    name: str | None = None
    description: str | None = None
    mime_type: str | None = None


class AttachmentInfo(msgspec.Struct):
    """
    Information about an attachment.

    Attributes
    ----------
    id : int
        The ID of the attachment.
    properties : AttachmentProperties
        The properties of the attachment.
    """

    id: int
    file_name: str | None = None
    content_type: str | None = None
    description: str | None = None
    size: int = 0
    properties: AttachmentProperties = msgspec.field(default_factory=AttachmentProperties)


class MkvMergeOutput(msgspec.Struct):
    """
    Root structure of `mkvmerge -J` output.

    Attributes
    ----------
    container : ContainerInfo
        Information about the container.
    tracks : list[TrackInfo]
        List of tracks in the file.
    global_tags : list[TagEntry]
        List of global tags.
    track_tags : list[TagEntry]
        List of track tags.
    attachments : list[AttachmentInfo]
        List of attachments.
    file_name : str | None
        The file name.
    """

    container: ContainerInfo
    file_name: str | None = None
    tracks: list[TrackInfo] = []
    global_tags: list[TagEntry] = []
    track_tags: list[TagEntry] = []
    attachments: list[AttachmentInfo] = []
