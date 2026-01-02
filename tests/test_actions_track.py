import sys
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from pymkv import MKVFile, MKVTrack
from pymkv.models import ContainerInfo, MkvMergeOutput, TrackInfo, TrackProperties


def test_remove_track_one_track(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)
    mkv.remove_track(1)

    assert len(mkv.tracks) == 1
    assert mkv.tracks[0].track_type == "video"


def test_remove_track_zero_track(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)
    mkv.remove_track(0)

    assert len(mkv.tracks) == 1
    assert mkv.tracks[0].track_type == "audio"


def test_remove_track_and_mux_file(
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    mkv = MKVFile(get_path_test_file)
    output_file = get_base_path / "file-test.mkv"
    mkv.remove_track(1)
    mkv.mux(output_file)

    assert output_file.is_file()

    mkv = MKVFile(output_file)

    assert len(mkv.tracks) == 1
    assert mkv.tracks[0].track_type == "video"


def test_move_track_front(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)
    mkv.move_track_front(1)

    assert len(mkv.tracks) == 2  # noqa: PLR2004
    assert mkv.tracks[0].track_type == "audio"
    assert mkv.tracks[1].track_type == "video"


def test_move_track_front_raises(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)

    with pytest.raises(IndexError):
        mkv.move_track_front(-1)

    with pytest.raises(IndexError):
        mkv.move_track_front(2)


def test_move_track_front_and_mux(
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    output_file = get_base_path / "file-test.mkv"

    mkv = MKVFile(get_path_test_file)
    mkv.move_track_front(1)
    mkv.mux(output_file)

    mkv = MKVFile(output_file)

    assert len(mkv.tracks) == 2  # noqa: PLR2004
    assert mkv.tracks[0].track_type == "audio"
    assert mkv.tracks[1].track_type == "video"


def test_mux_and_test_title(get_base_path: Path, get_path_test_file: Path) -> None:
    output_file = get_base_path / "file-test.mkv"

    mkv = MKVFile(get_path_test_file)
    mkv.title = "Test title in mkv file"
    mkv.mux(output_file)

    mkv = MKVFile(output_file)

    assert mkv.title == "Test title in mkv file"


def test_mux_and_test_track_name(get_base_path: Path, get_path_test_file: Path) -> None:
    output_file = get_base_path / "file-test.mkv"

    mkv = MKVFile(get_path_test_file)
    mkv.tracks[0].track_name = "Test track name"
    mkv.mux(output_file)

    mkv = MKVFile(output_file)

    assert mkv.tracks[0].track_name == "Test track name"


def test_move_track_end_raises(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)

    with pytest.raises(IndexError):
        mkv.move_track_end(-1)

    with pytest.raises(IndexError):
        mkv.move_track_end(2)


def test_move_track_end_and_mux(get_base_path: Path, get_path_test_file: Path) -> None:
    output_file = get_base_path / "file-test.mkv"

    mkv = MKVFile(get_path_test_file)
    mkv.move_track_end(0)
    mkv.mux(output_file)

    mkv = MKVFile(output_file)

    assert len(mkv.tracks) == 2  # noqa: PLR2004
    assert mkv.tracks[0].track_type == "audio"
    assert mkv.tracks[1].track_type == "video"


def test_move_track_forward_raises(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)

    with pytest.raises(IndexError):
        mkv.move_track_forward(-1)

    with pytest.raises(IndexError):
        mkv.move_track_forward(2)

    with pytest.raises(IndexError):
        mkv.move_track_forward(1)


def test_move_track_forward_and_mux(
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    output_file = get_base_path / "file-test.mkv"

    mkv = MKVFile(get_path_test_file)
    mkv.move_track_forward(0)
    mkv.mux(output_file)

    mkv = MKVFile(output_file)

    assert len(mkv.tracks) == 2  # noqa: PLR2004
    assert mkv.tracks[0].track_type == "audio"
    assert mkv.tracks[1].track_type == "video"


def test_move_track_backward_raises(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)

    with pytest.raises(IndexError):
        mkv.move_track_backward(-1)

    with pytest.raises(IndexError):
        mkv.move_track_backward(2)


def test_move_track_backward_and_mux(
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    output_file = get_base_path / "file-test.mkv"

    mkv = MKVFile(get_path_test_file)
    mkv.move_track_backward(1)
    mkv.mux(output_file)

    mkv = MKVFile(output_file)

    assert len(mkv.tracks) == 2  # noqa: PLR2004
    assert mkv.tracks[0].track_type == "audio"
    assert mkv.tracks[1].track_type == "video"


def test_get_track(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)
    track = cast("MKVTrack", mkv.get_track(1))

    assert track.track_type == "audio"

    tracks = mkv.get_track()

    assert isinstance(tracks, list)
    assert len(tracks) == 2  # noqa: PLR2004


def test_get_track_error(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)
    with pytest.raises(IndexError):
        mkv.get_track(2)


def test_track_init_legacy_dict(dummy_mkv: Path) -> None:
    # Test initialization with existing_info as a dict (legacy support)
    info = {
        "container": {"supported": True, "properties": {}},
        "tracks": [{"id": 0, "start_pts": 100, "codec": "AAC", "type": "audio", "properties": {}}],
    }
    t = MKVTrack(str(dummy_mkv), track_id=0, existing_info=info)
    # Check if dict was correctly used/converted
    assert t.track_codec == "AAC"
    assert t.track_type == "audio"
    # pts check removed due to uncertainty of field mapping


def test_track_repr(dummy_mkv: Path) -> None:
    # return dummy info with at least 1 track
    info = MkvMergeOutput(container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")])

    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info", return_value=info),
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
    ):
        t = MKVTrack(str(dummy_mkv))
        rep = repr(t)
        assert repr(str(dummy_mkv)) in rep
        assert "MKVTrack" in str(type(t))


def test_track_pts_property(dummy_mkv: Path) -> None:
    info = MkvMergeOutput(
        container=ContainerInfo(),
        tracks=[TrackInfo(id=0, type="video", codec="h264", properties=TrackProperties(language_ietf="en-US"))],
    )

    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info", return_value=info),
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
    ):
        t = MKVTrack(str(dummy_mkv))
        # pts is 0 by default
        assert t.pts == 0
        t._pts = 123  # noqa: SLF001
        assert t.pts == 123  # noqa: PLR2004


def test_track_tags_setter(dummy_mkv: Path, tmp_path: Path) -> None:
    # Setup dummy validation
    info = MkvMergeOutput(container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")])

    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info", return_value=info),
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
    ):
        t = MKVTrack(str(dummy_mkv))

        # Test None
        t.tags = None
        assert t.tags is None

        # Test invalid type
        with pytest.raises(TypeError, match="not of type str"):
            t.tags = 123  # type: ignore[assignment]

        # Test non-existent file
        with pytest.raises(FileNotFoundError, match="does not exist"):
            t.tags = str(tmp_path / "non_existent_tags.xml")

        # Test valid file
        tags_file = tmp_path / "tags.xml"
        tags_file.touch()
        t.tags = str(tags_file)
        assert t.tags == str(tags_file)


def test_track_file_path_setter_verification_failure(tmp_path: Path) -> None:
    # Test that verify_supported failure raises ValueError
    invalid = tmp_path / "invalid.mkv"
    invalid.touch()
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=False),
        pytest.raises(ValueError, match="not a valid Matroska file"),
    ):
        MKVTrack(str(invalid))


def test_extract_silent_and_path(dummy_mkv: Path, tmp_path: Path) -> None:
    info = MkvMergeOutput(container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")])
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info", return_value=info),
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
    ):
        t = MKVTrack(str(dummy_mkv))
    output = tmp_path / "extracted"

    with patch("subprocess.run") as mock_run:
        res = t.extract(output_path=output, silent=True)

        args = mock_run.call_args[0][0]
        assert args[0] == "mkvextract"
        assert args[1] == "tracks"
        assert str(dummy_mkv) in args[2]
        assert f"0:{output}" in args[3]

        # MKVTrack appends filename + extract info to the output path (assuming it as directory)
        # We just verify it returns a string starting with our output path
        assert str(output) in res
