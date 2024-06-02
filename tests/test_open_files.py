from pathlib import Path

import pytest

from pymkv import MKVFile, MKVTrack


def test_open_file(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)

    assert len(mkv.tracks) == 2  # noqa: PLR2004


def test_mux_file(get_base_path: Path, get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)
    output_file = get_base_path / "file-test.mkv"
    mkv.mux(output_file)

    assert output_file.is_file()


def test_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        MKVFile("file-zero.mkv")


def test_file_not_support() -> None:
    with pytest.raises(
        ValueError,
        match="The file 'tests/conftest.py' is not a valid Matroska file or is not supported.",
    ):
        MKVFile("tests/conftest.py")


def test_track_not_support() -> None:
    with pytest.raises(
        ValueError,
        match="The file 'tests/conftest.py' is not a valid Matroska file or is not supported.",
    ):
        MKVTrack("tests/conftest.py")
