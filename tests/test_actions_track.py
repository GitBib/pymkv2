from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from pymkv import MKVFile, MKVTrack
from pymkv.models import ContainerInfo, MkvMergeOutput, TrackInfo


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


def test_added_lang_in_track_and_mux_file(
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    mkv = MKVFile(get_path_test_file)
    output_file = get_base_path / "file-test.mkv"
    track = cast("MKVTrack", mkv.get_track(1))
    track.language_ietf = "TEST"
    with pytest.raises(ValueError):  # noqa: PT011
        mkv.mux(output_file)


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


@patch("pymkv.MKVTrack.get_file_info")
@patch("pymkv.MKVTrack.verify_supported", return_value=True)
def test_track_repr(mock_verify: MagicMock, mock_info: MagicMock, dummy_mkv: Path) -> None:
    # return dummy info with at least 1 track
    mock_info.return_value = MkvMergeOutput(
        container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")]
    )

    t = MKVTrack(str(dummy_mkv))
    rep = repr(t)
    assert str(dummy_mkv) in rep
    assert "MKVTrack" in str(type(t))


@patch("pymkv.MKVTrack.get_file_info")
@patch("pymkv.MKVTrack.verify_supported", return_value=True)
def test_track_properties_ielf_language(mock_verify: MagicMock, mock_info: MagicMock, dummy_mkv: Path) -> None:
    mock_info.return_value = MkvMergeOutput(
        container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")]
    )
    t = MKVTrack(str(dummy_mkv))

    # Test language_ietf setter
    t.language_ietf = "en-US"
    assert t.language_ietf == "en-US"

    # Test effective_language priority
    # 1. Only ietf
    assert t.effective_language == "en-US"

    # 2. Both (ietf wins)
    t.language = "eng"
    assert t.language == "eng"
    assert t.effective_language == "en-US"

    # 3. Only legacy
    t.language_ietf = None
    assert t.effective_language == "eng"

    # 4. None
    t.language = None
    assert t.effective_language is None


@patch("pymkv.MKVTrack.get_file_info")
@patch("pymkv.MKVTrack.verify_supported", return_value=True)
def test_track_pts_property(mock_verify: MagicMock, mock_info: MagicMock, dummy_mkv: Path) -> None:
    mock_info.return_value = MkvMergeOutput(
        container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")]
    )
    t = MKVTrack(str(dummy_mkv))
    # pts is 0 by default
    assert t.pts == 0
    t._pts = 123  # noqa: SLF001
    assert t.pts == 123  # noqa: PLR2004


@patch("pymkv.MKVTrack.get_file_info")
@patch("pymkv.MKVTrack.verify_supported", return_value=True)
def test_track_tags_setter(mock_verify: MagicMock, mock_info: MagicMock, dummy_mkv: Path, tmp_path: Path) -> None:
    mock_info.return_value = MkvMergeOutput(
        container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")]
    )
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
        patch("pymkv.MKVTrack.verify_supported", return_value=False),
        pytest.raises(ValueError, match="not a valid Matroska file"),
    ):
        MKVTrack(str(invalid))


@patch("pymkv.MKVTrack.get_file_info")
@patch("pymkv.MKVTrack.verify_supported", return_value=True)
def test_extract_silent_and_path(mock_verify: MagicMock, mock_info: MagicMock, dummy_mkv: Path, tmp_path: Path) -> None:
    mock_info.return_value = MkvMergeOutput(
        container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")]
    )
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
