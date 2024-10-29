from __future__ import annotations

import subprocess as sp
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pymkv import verify_matroska

if TYPE_CHECKING:
    import os


def test_verify_matroska_true(get_path_test_file: Path) -> None:
    assert verify_matroska(get_path_test_file) is True


def test_verify_matroska_mkvmerge_not_found(get_path_test_file: Path) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="mkvmerge is not at the specified path",
    ):
        verify_matroska(get_path_test_file, "mkvmerge-test")


def test_verify_matroska_file_not_found() -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        verify_matroska("non_existent_file.mkv")


def test_verify_matroska_invalid_file() -> None:
    with pytest.raises(ValueError, match="could not be opened"):  # noqa: PT012, SIM117
        with patch("pymkv.Verifications.get_file_info") as mock_get_file_info:
            mock_get_file_info.side_effect = sp.CalledProcessError(1, "mkvmerge")
            verify_matroska("invalid_file.mkv")


@pytest.mark.parametrize(
    "file_type, expected",  # noqa: PT006
    [
        ("Matroska", True),
        ("AVI", False),
        ("MP4", False),
    ],
)
def test_verify_matroska_various_types(
    file_type: str,
    expected: bool,
    get_path_test_file: Path,
) -> None:
    with patch("pymkv.Verifications.get_file_info") as mock_get_file_info:
        mock_get_file_info.return_value = {"container": {"type": file_type}}
        assert verify_matroska(get_path_test_file) is expected


@pytest.mark.parametrize(
    "mkvmerge_path",
    [
        "mkvmerge",
        ["path", "to", "mkvmerge"],
        ("path", "to", "mkvmerge"),
        Path("path/to/mkvmerge"),
    ],
)
def test_verify_matroska_mkvmerge_path_types(
    mkvmerge_path: str | list | os.PathLike,
    get_path_test_file: Path,
) -> None:
    with (
        patch("pymkv.Verifications.verify_mkvmerge") as mock_verify_mkvmerge,
        patch("pymkv.Verifications.get_file_info") as mock_get_file_info,
    ):
        mock_verify_mkvmerge.return_value = True
        mock_get_file_info.return_value = {"container": {"type": "Matroska"}}
        assert verify_matroska(get_path_test_file, mkvmerge_path) is True
        mock_verify_mkvmerge.assert_called_once_with(mkvmerge_path=mkvmerge_path)


def test_verify_matroska_mkvmerge_not_found_various_types() -> None:
    with patch("pymkv.Verifications.verify_mkvmerge") as mock_verify_mkvmerge:
        mock_verify_mkvmerge.return_value = False
        with pytest.raises(
            FileNotFoundError,
            match="mkvmerge is not at the specified path",
        ):
            verify_matroska("test.mkv", "non_existent_path")
