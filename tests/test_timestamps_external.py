from pathlib import Path

import pytest

from pymkv import MKVFile, MKVTrack


def test_timestamps_init(get_path_test_file: Path, tmp_path: Path) -> None:
    ts_file = tmp_path / "timestamps.txt"
    ts_file.touch()

    track = MKVTrack(str(get_path_test_file), timestamps=str(ts_file))
    assert track.timestamps == str(ts_file)


def test_timestamps_setter(get_path_test_file: Path, tmp_path: Path) -> None:
    track = MKVTrack(str(get_path_test_file))
    assert track.timestamps is None

    ts_file = tmp_path / "timestamps.txt"
    ts_file.touch()

    track.timestamps = str(ts_file)
    assert track.timestamps == str(ts_file)

    track.timestamps = None
    assert track.timestamps is None


def test_timestamps_setter_errors(get_path_test_file: Path, tmp_path: Path) -> None:
    track = MKVTrack(str(get_path_test_file))

    with pytest.raises(TypeError):
        track.timestamps = 123  # type: ignore[assignment]

    with pytest.raises(FileNotFoundError):
        track.timestamps = str(tmp_path / "non_existent.txt")


def test_timestamps_command_generation(get_path_test_file: Path, tmp_path: Path) -> None:
    ts_file = tmp_path / "timestamps.txt"
    ts_file.touch()

    track = MKVTrack(str(get_path_test_file), track_id=0)
    track.timestamps = str(ts_file)

    mkv = MKVFile()
    mkv.add_track(track)

    cmd = mkv.command("output.mkv")
    assert "--timestamps" in cmd
    assert f"0:{ts_file}" in cmd


def test_timestamps_muxing_and_read(get_path_test_file: Path, tmp_path: Path) -> None:
    ts_content = "# timestamp format v1\nassume 24.0\n0,4,1.0\n"
    ts_file = tmp_path / "timestamps.txt"
    ts_file.write_text(ts_content)

    track = MKVTrack(str(get_path_test_file), track_id=0)
    track.timestamps = str(ts_file)

    mkv = MKVFile()
    mkv.add_track(track)

    output_file = tmp_path / "output_with_timestamps.mkv"

    mkv.mux(output_file)

    assert output_file.exists()

    mkv_read = MKVFile(output_file)
    read_track = mkv_read.get_track(0)
    if isinstance(read_track, list):
        read_track = read_track[0]

    extracted_ts_path = read_track.extract_timestamps(output_path=tmp_path)
    extracted_ts_file = Path(extracted_ts_path)

    assert extracted_ts_file.exists()

    extracted_lines = extracted_ts_file.read_text().splitlines()
    extracted_lines = [line for line in extracted_lines if line.strip() and not line.startswith("#")]

    expected_starts = ["0", "1000", "2000", "3000", "4000"]
    assert extracted_lines[:5] == expected_starts

    assert read_track.timestamps is None
