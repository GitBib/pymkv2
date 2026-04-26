import msgspec

from pymkv.models import (
    AttachmentInfo,
    AttachmentProperties,
    ContainerInfo,
    ContainerProperties,
    MkvMergeOutput,
    TagEntry,
    TrackInfo,
    TrackProperties,
)


def test_track_properties_defaults() -> None:
    tp = TrackProperties()
    assert tp.track_name is None
    assert tp.language is None
    assert tp.language_ietf is None
    assert tp.default_track is False
    assert tp.forced_track is False
    assert tp.flag_commentary is False
    assert tp.flag_hearing_impaired is False
    assert tp.flag_visual_impaired is False
    assert tp.flag_original is False


def test_track_info_defaults() -> None:
    ti = TrackInfo(id=0, type="video", codec="h264")
    assert ti.id == 0
    assert ti.type == "video"
    assert ti.codec == "h264"
    assert ti.num_entries is None
    assert ti.start_pts == 0
    assert isinstance(ti.properties, TrackProperties)


def test_container_info_defaults() -> None:
    ci = ContainerInfo()
    assert ci.supported is True
    assert ci.recognized is True
    assert ci.type is None
    assert isinstance(ci.properties, ContainerProperties)


def test_container_properties_defaults() -> None:
    cp = ContainerProperties()
    assert cp.title is None


def test_tag_entry_defaults() -> None:
    te = TagEntry()
    assert te.num_entries == 0
    assert te.track_id is None


def test_attachment_info_defaults() -> None:
    ai = AttachmentInfo(id=1)
    assert ai.id == 1
    assert ai.file_name is None
    assert ai.content_type is None
    assert ai.description is None
    assert ai.size == 0
    assert isinstance(ai.properties, AttachmentProperties)


def test_attachment_properties_defaults() -> None:
    ap = AttachmentProperties()
    assert ap.name is None
    assert ap.description is None
    assert ap.mime_type is None


def test_mkv_merge_output_defaults() -> None:
    output = MkvMergeOutput(container=ContainerInfo())
    assert output.tracks == []
    assert output.global_tags == []
    assert output.track_tags == []
    assert output.attachments == []
    assert output.file_name is None


def test_mkv_merge_output_lists_are_independent() -> None:
    """Verify that default list fields are not shared between instances."""
    output1 = MkvMergeOutput(container=ContainerInfo())
    output2 = MkvMergeOutput(container=ContainerInfo())
    output1.tracks.append(TrackInfo(id=0, type="video", codec="h264"))
    assert len(output2.tracks) == 0


def test_mkv_merge_output_decode() -> None:
    json_bytes = b"""{
        "container": {"supported": true, "recognized": true, "type": "Matroska",
                       "properties": {"title": "My Movie"}},
        "tracks": [{"id": 0, "type": "video", "codec": "h264",
                    "properties": {"default_track": true}}],
        "global_tags": [],
        "track_tags": [],
        "attachments": [],
        "file_name": "test.mkv"
    }"""
    result = msgspec.json.decode(json_bytes, type=MkvMergeOutput, strict=False)
    assert result.container.supported is True
    assert result.container.properties.title == "My Movie"
    assert result.container.type == "Matroska"
    assert len(result.tracks) == 1
    assert result.tracks[0].codec == "h264"
    assert result.tracks[0].properties.default_track is True
    assert result.file_name == "test.mkv"
