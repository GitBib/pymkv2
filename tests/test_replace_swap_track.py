from pathlib import Path

import pytest

from pymkv import MKVFile, MKVTrack


def test_replace_track_valid(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    new_track = MKVTrack(str(get_path_test_file), track_id=1)
    mkv.replace_track(0, new_track)
    assert mkv.tracks[0] is new_track


def test_replace_track_boundary_last(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    new_track = MKVTrack(str(get_path_test_file), track_id=0)
    last_idx = len(mkv.tracks) - 1
    mkv.replace_track(last_idx, new_track)
    assert mkv.tracks[last_idx] is new_track


def test_replace_track_index_error(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    new_track = MKVTrack(str(get_path_test_file), track_id=0)
    with pytest.raises(IndexError, match="track index out of range"):
        mkv.replace_track(99, new_track)


def test_swap_tracks_valid(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    assert len(mkv.tracks) >= 2  # noqa: PLR2004
    track_0 = mkv.tracks[0]
    track_1 = mkv.tracks[1]
    mkv.swap_tracks(0, 1)
    assert mkv.tracks[0] is track_1
    assert mkv.tracks[1] is track_0


def test_swap_tracks_same_index(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    track_0 = mkv.tracks[0]
    mkv.swap_tracks(0, 0)
    assert mkv.tracks[0] is track_0


def test_swap_tracks_index_error(get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))
    with pytest.raises(IndexError, match="Track index out of range"):
        mkv.swap_tracks(0, 99)
    with pytest.raises(IndexError, match="Track index out of range"):
        mkv.swap_tracks(99, 0)
