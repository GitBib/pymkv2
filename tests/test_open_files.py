from pathlib import Path

import pytest

from pymkv import MKVFile


def test_open_file() -> None:
    path = Path.cwd() / "tests"
    mkv = MKVFile(path / "file.mkv")

    assert len(mkv.tracks) == 2  # noqa: PLR2004


def test_mux_file() -> None:
    path = Path.cwd() / "tests"
    mkv = MKVFile(path / "file.mkv")
    output_file = path / "file-test.mkv"
    mkv.mux(output_file, silent=True)

    assert output_file.is_file(), f"File {output_file} does not exist after muxing"


def test_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        MKVFile("file-zero.mkv")
