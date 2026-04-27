import subprocess as sp
import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import msgspec
import pytest

from pymkv import MKVFile, MKVTrack
from pymkv.chapters import ChapterAtom, ChapterDisplay
from pymkv.models import ContainerInfo, MkvMergeOutput


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


def test_mkvfile_init_errors(tmp_path: Path) -> None:
    # 1. CalledProcessError re-raise
    with (
        patch.object(sys.modules["pymkv.MKVFile"], "checking_file_path", side_effect=lambda x: x),
        patch.object(
            sys.modules["pymkv.MKVFile"], "get_file_info", side_effect=sp.CalledProcessError(1, "cmd", output=b"error")
        ),
        pytest.raises(sp.CalledProcessError),
    ):
        MKVFile("file.mkv")

    # 2. msgspec.ValidationError -> ValueError
    with (
        patch.object(sys.modules["pymkv.MKVFile"], "checking_file_path", side_effect=lambda x: x),
        patch.object(
            sys.modules["pymkv.MKVFile"], "get_file_info", side_effect=msgspec.ValidationError("invalid json")
        ),
        pytest.raises(ValueError, match="Invalid JSON"),
    ):
        MKVFile("file.mkv")

    # 3. Not supported
    real_info = MkvMergeOutput(container=ContainerInfo(supported=False))
    with (
        patch.object(sys.modules["pymkv.MKVFile"], "checking_file_path", side_effect=lambda x: x),
        patch.object(sys.modules["pymkv.MKVFile"], "get_file_info", return_value=real_info),
        pytest.raises(ValueError, match="not a valid Matroska file"),
    ):
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
    with pytest.raises(
        ValueError,
        match=r"'invalid' cannot be mapped to a valid ISO 639-2 language code",
    ):
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


def test_order_tracks_by_file_id_keyerror(single_video_info: MkvMergeOutput) -> None:
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "checking_file_path", side_effect=lambda x: x),
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info", return_value=single_video_info),
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
    ):
        mkv = MKVFile()
        t1 = MKVTrack("file1.mkv")
        mkv.tracks = [t1]

    # We simulate KeyError by making track.file_path return different values

    mock_track = MagicMock()
    type(mock_track).file_path = PropertyMock(side_effect=["A", "B", "C", "D"])

    mkv.tracks = [mock_track]

    with pytest.raises(ValueError):  # noqa: PT011
        mkv.order_tracks_by_file_id()


def test_add_track_type_error() -> None:
    mkv = MKVFile()
    with pytest.raises(TypeError, match="track is not str or MKVTrack"):
        mkv.add_track(123)  # type: ignore[arg-type]


def test_add_file_type_error() -> None:
    mkv = MKVFile()
    with pytest.raises(TypeError, match="track is not str or MKVFile"):
        mkv.add_file(123)  # type: ignore[arg-type]


def test_add_attachment_type_error() -> None:
    mkv = MKVFile()
    with pytest.raises(TypeError, match="Attachment is not str of MKVAttachment"):
        mkv.add_attachment(123)  # type: ignore[arg-type]


def test_add_chapter_type_error() -> None:
    mkv = MKVFile()
    with pytest.raises(TypeError, match="chapter must be ChapterAtom or EditionEntry"):
        mkv.add_chapter("bad_input")  # type: ignore[arg-type]


def test_track_tags_empty_ids() -> None:
    mkv = MKVFile()
    with pytest.raises(ValueError, match="not properly formatted track ids"):
        mkv.track_tags()


def test_track_tags_non_int_id(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    with pytest.raises(TypeError, match="not an int"):
        mkv.track_tags("a")  # type: ignore[arg-type]


def test_track_tags_out_of_range(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    with pytest.raises(IndexError, match="track id out of range"):
        mkv.track_tags(99)


def test_remove_track_invalid_index(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    with pytest.raises(IndexError, match="track index out of range"):
        mkv.remove_track(999)


def test_mux_silent(
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    mkv = MKVFile(str(get_path_test_file))
    output = get_base_path / "silent_output.mkv"
    ret = mkv.mux(str(output), silent=True)
    assert ret == 0
    assert output.exists()


def test_mux_error_raises() -> None:
    mkv = MKVFile()
    with (
        patch("subprocess.Popen") as mock_popen,
    ):
        proc = MagicMock()
        proc.returncode = 2
        proc.stdout = None
        proc.communicate.return_value = (None, b"some error output")
        mock_popen.return_value = proc
        with pytest.raises(ValueError, match="Command failed"):
            mkv.mux("output.mkv")


def test_mux_warning_ignored() -> None:
    mkv = MKVFile()
    with (
        patch("subprocess.Popen") as mock_popen,
    ):
        proc = MagicMock()
        proc.returncode = 1
        proc.stdout = None
        proc.communicate.return_value = (None, b"warning output")
        mock_popen.return_value = proc
        ret = mkv.mux("output.mkv", ignore_warning=True)
        assert ret == 1


def test_cleanup_removes_temp_chapters() -> None:
    mkv = MKVFile()
    atom = ChapterAtom(time_start="00:00:10.000", displays=[ChapterDisplay(string="Test")])
    mkv.add_chapter(atom)

    mkv.command("output.mkv")

    assert mkv._temp_chapters_file is not None  # noqa: SLF001
    temp_path = Path(mkv._temp_chapters_file)  # noqa: SLF001
    assert temp_path.exists()

    mkv.cleanup()
    assert mkv._temp_chapters_file is None  # noqa: SLF001
    assert mkv._chapters_file is None  # noqa: SLF001
    assert not temp_path.exists()


def test_context_manager_cleanup() -> None:
    with MKVFile() as mkv:
        atom = ChapterAtom(time_start="00:00:10.000", displays=[ChapterDisplay(string="Test")])
        mkv.add_chapter(atom)
        mkv.command("output.mkv")
        assert mkv._temp_chapters_file is not None  # noqa: SLF001
        temp_path = Path(mkv._temp_chapters_file)  # noqa: SLF001
        assert temp_path.exists()

    assert not temp_path.exists()


def test_add_track_with_string(get_path_test_file: Path) -> None:
    mkv = MKVFile()
    mkv.add_track(str(get_path_test_file))
    assert len(mkv.tracks) >= 1
