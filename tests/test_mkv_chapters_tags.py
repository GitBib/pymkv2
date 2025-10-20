from pathlib import Path
from unittest.mock import Mock

import pytest

from pymkv import MKVFile


def test_chapter_language_getter_setter() -> None:
    mkv = MKVFile()
    assert mkv.chapter_language is None

    mkv.chapter_language = "eng"
    assert mkv.chapter_language == "eng"

    mkv.chapter_language = None
    assert mkv.chapter_language is None

    with pytest.raises(ValueError, match="not a valid ISO 639-2 language code"):
        mkv.chapter_language = "invalid_code"


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
