import subprocess as sp
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pymkv.Verifications import (
    checking_file_path,
    get_file_info_raw,
    verify_file_path_and_mkvmerge,
    verify_mkvmerge,
    verify_recognized,
    verify_supported,
)


def test_checking_file_path_valid(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    result = checking_file_path(str(f))
    assert result == str(f)


def test_checking_file_path_pathlike(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    result = checking_file_path(f)
    assert result == str(f)


def test_checking_file_path_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        checking_file_path(str(tmp_path / "nonexistent.mkv"))


def test_checking_file_path_invalid_type_none() -> None:
    with pytest.raises(TypeError, match="not of type str"):
        checking_file_path(None)


def test_checking_file_path_invalid_type_int() -> None:
    with pytest.raises(TypeError, match="not of type str"):
        checking_file_path(123)  # type: ignore[arg-type]


def test_get_file_info_raw_check_path_false() -> None:
    with patch("pymkv.Verifications.sp.check_output", return_value=b'{"container":{"supported":true}}'):
        result = get_file_info_raw("dummy_path", ("mkvmerge",), check_path=False)
        assert result == b'{"container":{"supported":true}}'


def test_get_file_info_raw_check_path_true_missing() -> None:
    with pytest.raises(FileNotFoundError):
        get_file_info_raw("/definitely/nonexistent/file.mkv", ("mkvmerge",), check_path=True)


def test_verify_recognized_true(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    mock_info = MagicMock()
    mock_info.container.recognized = True
    with (
        patch("pymkv.Verifications.verify_mkvmerge", return_value=True),
        patch("pymkv.Verifications.checking_file_path", return_value=str(f)),
        patch("pymkv.Verifications.get_file_info", return_value=mock_info),
    ):
        assert verify_recognized(str(f)) is True


def test_verify_recognized_false(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    mock_info = MagicMock()
    mock_info.container.recognized = False
    with (
        patch("pymkv.Verifications.verify_mkvmerge", return_value=True),
        patch("pymkv.Verifications.checking_file_path", return_value=str(f)),
        patch("pymkv.Verifications.get_file_info", return_value=mock_info),
    ):
        assert verify_recognized(str(f)) is False


def test_verify_recognized_called_process_error(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    with (
        patch("pymkv.Verifications.verify_mkvmerge", return_value=True),
        patch("pymkv.Verifications.checking_file_path", return_value=str(f)),
        patch("pymkv.Verifications.get_file_info", side_effect=sp.CalledProcessError(1, "cmd")),
        pytest.raises(ValueError, match="could not be opened"),
    ):
        verify_recognized(str(f))


def test_verify_supported_true(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    mock_info = MagicMock()
    mock_info.container.supported = True
    with (
        patch("pymkv.Verifications.verify_mkvmerge", return_value=True),
        patch("pymkv.Verifications.checking_file_path", return_value=str(f)),
        patch("pymkv.Verifications.get_file_info", return_value=mock_info),
    ):
        assert verify_supported(str(f)) is True


def test_verify_supported_false(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    mock_info = MagicMock()
    mock_info.container.supported = False
    with (
        patch("pymkv.Verifications.verify_mkvmerge", return_value=True),
        patch("pymkv.Verifications.checking_file_path", return_value=str(f)),
        patch("pymkv.Verifications.get_file_info", return_value=mock_info),
    ):
        assert verify_supported(str(f)) is False


def test_verify_file_path_and_mkvmerge_valid(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    with patch("pymkv.Verifications.verify_mkvmerge", return_value=True):
        result = verify_file_path_and_mkvmerge(str(f))
        assert result == str(f)


def test_verify_file_path_and_mkvmerge_no_mkvmerge(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    with (
        patch("pymkv.Verifications.verify_mkvmerge", return_value=False),
        pytest.raises(FileNotFoundError, match="mkvmerge is not at the specified path"),
    ):
        verify_file_path_and_mkvmerge(str(f))


def test_verify_file_path_and_mkvmerge_no_file() -> None:
    with (
        patch("pymkv.Verifications.verify_mkvmerge", return_value=True),
        pytest.raises(FileNotFoundError, match="does not exist"),
    ):
        verify_file_path_and_mkvmerge("/nonexistent/file.mkv")


def test_verify_mkvmerge_with_list() -> None:
    assert verify_mkvmerge(mkvmerge_path=["mkvmerge"]) is True


def test_verify_recognized_with_list(get_path_test_file: Path) -> None:
    assert verify_recognized(str(get_path_test_file), mkvmerge_path=["mkvmerge"]) is True


def test_verify_supported_with_list(get_path_test_file: Path) -> None:
    assert verify_supported(str(get_path_test_file), mkvmerge_path=["mkvmerge"]) is True


def test_verify_supported_called_process_error(tmp_path: Path) -> None:
    f = tmp_path / "test.mkv"
    f.touch()
    with (
        patch("pymkv.Verifications.verify_mkvmerge", return_value=True),
        patch("pymkv.Verifications.checking_file_path", return_value=str(f)),
        patch("pymkv.Verifications.get_file_info", side_effect=sp.CalledProcessError(1, "cmd")),
        pytest.raises(ValueError, match="could not be opened"),
    ):
        verify_supported(str(f))
