from pathlib import Path

import pytest

from pymkv import MKVFile, MKVTrack


def test_open_file(get_path_test_file: Path) -> None:
    mkv = MKVFile(get_path_test_file)

    assert mkv.title is None
    assert len(mkv.tracks) == 2  # noqa: PLR2004
    assert mkv.global_tag_entries == 4  # noqa: PLR2004
    assert mkv.tracks[0].tag_entries == 3  # noqa: PLR2004
    assert mkv.tracks[1].tag_entries == 4  # noqa: PLR2004


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
        match=r"The file 'tests[/\\]conftest\.py' is not a valid Matroska file or is not supported\.",
    ):
        MKVFile("tests/conftest.py")


def test_track_not_support() -> None:
    with pytest.raises(
        ValueError,
        match=r"The file 'tests[/\\]conftest\.py' is not a valid Matroska file or is not supported\.",
    ):
        MKVTrack("tests/conftest.py")


def test_empty_mkv_file() -> None:
    mkv = MKVFile(title="test")

    assert mkv.title == "test"
    assert len(mkv.tracks) == 0


def test_verify_mkvmerge_in_mkv_file() -> None:
    with pytest.raises(
        FileNotFoundError,
        match="mkvmerge is not at the specified path, add it there or changed mkvmerge_path property",
    ):
        MKVFile(title="test", mkvmerge_path="mkvmerge_test")
