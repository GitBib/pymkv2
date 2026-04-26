from __future__ import annotations

from typing import cast

import bitmath
import pytest

from pymkv import MKVFile


def test_split_none() -> None:
    mkv = MKVFile()
    mkv.split_size(1000)
    mkv.split_none()
    assert mkv._split_options == []  # noqa: SLF001


def test_split_size_with_bitmath() -> None:
    mkv = MKVFile()
    size = bitmath.MiB(10)
    mkv.split_size(size)
    assert mkv._split_options == ["--split", f"size:{int(size.bytes)}"]  # noqa: SLF001


def test_split_size_with_int() -> None:
    mkv = MKVFile()
    size = 10485760  # 10 MiB in bytes
    mkv.split_size(size)
    assert mkv._split_options == ["--split", f"size:{size}"]  # noqa: SLF001


def test_split_size_with_link() -> None:
    mkv = MKVFile()
    size = 10485760
    mkv.split_size(size, link=True)
    assert "--link" in mkv._split_options  # noqa: SLF001
    assert f"size:{size}" in mkv._split_options[1]  # noqa: SLF001


def test_split_size_with_invalid_type() -> None:
    mkv = MKVFile()
    with pytest.raises(TypeError):
        mkv.split_size("10MiB")  # type: ignore[arg-type]


def test_split_duration_with_string() -> None:
    mkv = MKVFile()
    duration = "00:10:00"  # 10 minutes
    mkv.split_duration(duration)
    assert mkv._split_options == ["--split", "duration:10:00"]  # noqa: SLF001


def test_split_duration_with_int() -> None:
    mkv = MKVFile()
    duration = 600  # 10 minutes in seconds
    mkv.split_duration(duration)
    assert mkv._split_options == ["--split", "duration:10:00"]  # noqa: SLF001


def test_split_duration_with_link() -> None:
    mkv = MKVFile()
    duration = "00:10:00"
    mkv.split_duration(duration, link=True)
    assert "--link" in mkv._split_options  # noqa: SLF001
    assert "duration:10:00" in mkv._split_options[1]  # noqa: SLF001


def test_split_timestamps() -> None:
    mkv = MKVFile()
    timestamps: list[str | int] = ["00:05:00", "00:10:00", "00:15:00"]
    mkv.split_timestamps(timestamps)
    assert mkv._split_options == ["--split", "timestamps:05:00,10:00,15:00"]  # noqa: SLF001


def test_split_timestamps_with_mixed_types() -> None:
    mkv = MKVFile()
    timestamps: list[str | int] = ["00:05:00", 600, "00:15:00"]  # 600 seconds = 00:10:00
    mkv.split_timestamps(timestamps)
    assert mkv._split_options == ["--split", "timestamps:05:00,10:00,15:00"]  # noqa: SLF001


def test_split_frames() -> None:
    mkv = MKVFile()
    frames = [100, 200, 300]
    mkv.split_frames(frames)
    assert mkv._split_options == ["--split", "frames:100,200,300"]  # noqa: SLF001


def test_split_frames_with_invalid_frame() -> None:
    mkv = MKVFile()
    with pytest.raises(TypeError):
        mkv.split_frames(cast("list[int]", "not a valid frame type"))


def test_split_chapters() -> None:
    mkv = MKVFile()
    chapters = [1, 2, 3]
    mkv.split_chapters(chapters)
    assert mkv._split_options == ["--split", "chapters:1,2,3"]  # noqa: SLF001


def test_split_chapters_empty() -> None:
    mkv = MKVFile()
    mkv.split_chapters()
    assert mkv._split_options == ["--split", "chapters:all"]  # noqa: SLF001


def test_split_timestamp_parts_valid() -> None:
    mkv = MKVFile()
    mkv.split_timestamp_parts([["00:01:00", "00:02:00"]])
    assert mkv._split_options[0] == "--split"  # noqa: SLF001
    assert mkv._split_options[1] == "parts:01:00-02:00"  # noqa: SLF001


def test_split_timestamp_parts_with_none() -> None:
    mkv = MKVFile()
    mkv.split_timestamp_parts([cast("list[str]", [None, "00:05:00"])])
    assert "parts:" in mkv._split_options[1]  # noqa: SLF001


def test_split_timestamp_parts_with_link() -> None:
    mkv = MKVFile()
    mkv.split_timestamp_parts([["00:01:00", "00:02:00"]], link=True)
    assert "--link" in mkv._split_options  # noqa: SLF001


def test_split_parts_frames_valid() -> None:
    mkv = MKVFile()
    mkv.split_parts_frames([(100, 500)])
    assert mkv._split_options[0] == "--split"  # noqa: SLF001
    assert mkv._split_options[1] == "parts-frames:100-500"  # noqa: SLF001


def test_split_parts_frames_with_link() -> None:
    mkv = MKVFile()
    mkv.split_parts_frames([(100, 500)], link=True)
    assert "--link" in mkv._split_options  # noqa: SLF001


def test_split_chapters_with_link() -> None:
    mkv = MKVFile()
    mkv.split_chapters(1, 2, link=True)
    assert "--link" in mkv._split_options  # noqa: SLF001


def test_split_timestamps_with_link() -> None:
    mkv = MKVFile()
    mkv.split_timestamps("00:01:00", link=True)
    assert "--link" in mkv._split_options  # noqa: SLF001


def test_split_timestamps_empty_raises() -> None:
    mkv = MKVFile()
    with pytest.raises(ValueError, match="formatted timestamps"):
        mkv.split_timestamps()


def test_split_frames_empty_raises() -> None:
    mkv = MKVFile()
    with pytest.raises(ValueError, match="formatted frames"):
        mkv.split_frames()


def test_split_frames_with_link() -> None:
    mkv = MKVFile()
    mkv.split_frames(100, 200, link=True)
    assert "--link" in mkv._split_options  # noqa: SLF001


def test_split_timestamp_parts_bad_set_length() -> None:
    mkv = MKVFile()
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_timestamp_parts([["00:00:10"]])


def test_split_parts_frames_bad_set_length() -> None:
    mkv = MKVFile()
    with pytest.raises(ValueError, match="formatted"):
        mkv.split_parts_frames([(100,)])
