from pathlib import Path

import pytest

from pymkv import verify_matroska


def test_verify_matroska_true(get_path_test_file: Path) -> None:
    assert verify_matroska(get_path_test_file) is True


def test_verify_matroska_error(get_path_test_file: Path) -> None:
    with pytest.raises(FileNotFoundError):
        verify_matroska(get_path_test_file, "mkvmerge-test")


def test_verify_matroska_false(get_path_test_file: Path) -> None:
    with pytest.raises(KeyError):
        verify_matroska("tests/conftest.py")
