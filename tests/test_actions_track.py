from pathlib import Path
from typing import cast

import pytest

from pymkv import MKVFile, MKVTrack


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
    track = cast(MKVTrack, mkv.get_track(1))

    assert track.track_type == "audio"

    tracks = mkv.get_track()

    assert isinstance(tracks, list)
    assert len(tracks) == 2  # noqa: PLR2004


def test_get_track_error(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)
    with pytest.raises(IndexError):
        mkv.get_track(2)
