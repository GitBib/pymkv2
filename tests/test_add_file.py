from pathlib import Path

import pytest

from pymkv import MKVFile


def test_add_file(get_base_path: Path, get_path_test_file: Path, get_path_test_file_two: Path) -> None:
    output_file = get_base_path / "file-test.mkv"
    mkv = MKVFile(get_path_test_file)

    mkv_two = MKVFile(get_path_test_file_two)
    mkv.add_file(mkv_two)

    assert len(mkv.tracks) == 4  # noqa: PLR2004
    mkv.mux(output_file)


def test_add_file_error(get_base_path: Path, get_path_test_file: Path) -> None:
    output_file = get_base_path / "file-test.mkv"
    mkv = MKVFile(get_path_test_file)

    mkv_two = MKVFile(get_path_test_file)
    mkv.add_file(mkv_two)

    with pytest.raises(ValueError):  # noqa: PT011
        mkv.mux(output_file)
