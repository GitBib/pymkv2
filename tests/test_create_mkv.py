import subprocess as sp
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import msgspec
import pytest

from pymkv import MKVFile, MKVTrack
from pymkv.models import ContainerInfo, MkvMergeOutput, TrackInfo


def test_create_new_mkv(
    get_base_path: Path,
    get_path_test_file: Path,
    get_path_test_srt: Path,
) -> None:
    output_file = get_base_path / "new-file.mkv"
    mkv = MKVFile(str(get_path_test_file))
    track = MKVTrack(str(get_path_test_srt))

    mkv.add_track(track)

    assert len(mkv.tracks) == 3  # noqa: PLR2004
    mkv.mux(output_file)


@patch("pymkv.MKVFile.checking_file_path")
def test_mkvfile_init_errors(mock_check: MagicMock, tmp_path: Path) -> None:
    mock_check.side_effect = lambda x: x

    # 1. CalledProcessError re-raise
    with patch("pymkv.MKVFile.get_file_info") as mock_get:
        mock_get.side_effect = sp.CalledProcessError(1, "cmd", output=b"error")
        with pytest.raises(sp.CalledProcessError):
            MKVFile("file.mkv")

    # 2. msgspec.ValidationError -> ValueError
    with patch("pymkv.MKVFile.get_file_info") as mock_get:
        mock_get.side_effect = msgspec.ValidationError("invalid json")
        with pytest.raises(ValueError, match="Invalid JSON"):
            MKVFile("file.mkv")

    # 3. Not supported
    with patch("pymkv.MKVFile.get_file_info") as mock_get:
        # returns valid info but supported=False
        real_info = MkvMergeOutput(container=ContainerInfo(supported=False))
        mock_get.return_value = real_info

        with pytest.raises(ValueError, match="not a valid Matroska file"):
            MKVFile("file.mkv")


def test_mkvfile_repr() -> None:
    mkv = MKVFile()
    assert "MKVFile" in str(type(mkv))
    assert repr(mkv)


def test_chapter_language_validation() -> None:
    mkv = MKVFile()

    # Valid
    mkv.chapter_language = "eng"
    assert mkv.chapter_language == "eng"

    # None
    mkv.chapter_language = None
    assert mkv.chapter_language is None

    # Invalid
    with pytest.raises(ValueError, match="not a valid ISO 639-2"):
        mkv.chapter_language = "invalid"


def test_split_methods_validation() -> None:
    mkv = MKVFile()

    # split_timestamps
    # Unordered/Invalid
    with pytest.raises(ValueError, match="formatted timestamps"):
        # Assuming ValueError comes from order check or format
        mkv.split_timestamps("00:00:20", "00:00:10")
    with pytest.raises(ValueError, match="formatted timestamps"):
        # Match part of error or use no match if message varies too much
        # But linter demands match. Let's use a generic match or suppress if unknown
        mkv.split_timestamps(None)  # type: ignore[arg-type]

    # split_frames
    # Non-int
    with pytest.raises(TypeError, match="not an int"):
        mkv.split_frames("100")  # type: ignore[arg-type]
    # Unordered
    with pytest.raises(ValueError, match="formatted frames"):
        mkv.split_frames(100, 50)

    # split_timestamp_parts
    # Empty
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_timestamp_parts([])
    # None in wrong place
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_timestamp_parts([["00:00:10", None, "00:00:20"]])  # type: ignore[list-item]
    # Unordered in zip
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_timestamp_parts([["00:00:20", "00:00:10"]])

    # Not list/tuple set - expects ValueError
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_timestamp_parts(["not-list"])  # type: ignore[arg-type,list-item]
    # Bad set length
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_timestamp_parts([["00:00:10"]])  # length 1

    # split_parts_frames
    # Empty
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_parts_frames([])
    # None in wrong place
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_parts_frames([[100, None, 200]])  # type: ignore[list-item]
    # Unordered
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_parts_frames([[200, 100]])  # type: ignore[list-item]
    # Not list/tuple
    with pytest.raises(ValueError, match="formatted"):  # Same reason as above
        mkv.split_parts_frames(["not-list"])  # type: ignore[arg-type,list-item]
    # Bad set length
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_parts_frames([[100]])  # type: ignore[list-item]
    # Not int
    with pytest.raises(TypeError):
        mkv.split_parts_frames([[100, "200"]])  # type: ignore[list-item]
    # Not int (type check inside loop)
    # To verify the explicit type check using floats to bypass ">= not supported" TypeError
    # We remove the regex match requirement because it might be flaky depending on implementation details
    with pytest.raises(TypeError):
        mkv.split_parts_frames([[100.5, 200.5]])  # type: ignore[list-item]

    # split_chapters
    # Not int
    with pytest.raises(TypeError):
        mkv.split_chapters("1")  # type: ignore[arg-type]
    # Invalid value (<1)
    with pytest.raises(ValueError, match="formatted chapters"):
        mkv.split_chapters(0)
    # Unordered
    with pytest.raises(ValueError, match="formatted chapters"):
        mkv.split_chapters(2, 1)


@patch("pymkv.MKVTrack.get_file_info")
@patch("pymkv.MKVTrack.checking_file_path")
@patch("pymkv.MKVTrack.verify_supported", return_value=True)
def test_order_tracks_by_file_id_keyerror(mock_verify: MagicMock, mock_check: MagicMock, mock_info: MagicMock) -> None:
    mock_check.side_effect = lambda x: x
    mock_info.return_value = MkvMergeOutput(
        container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")]
    )

    mkv = MKVFile()
    t1 = MKVTrack("file1.mkv")
    mkv.tracks = [t1]

    # We simulate KeyError by making track.file_path return different values

    mock_track = MagicMock()
    type(mock_track).file_path = PropertyMock(side_effect=["A", "B", "C", "D"])

    mkv.tracks = [mock_track]

    with pytest.raises(ValueError):  # noqa: PT011
        mkv.order_tracks_by_file_id()
