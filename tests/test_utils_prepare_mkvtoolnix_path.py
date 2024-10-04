from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from pymkv import utils


def test_prepare_mkvmerge_path_with_string() -> None:
    result = utils.prepare_mkvtoolnix_path(
        "flatpak run org.bunkus.mkvtoolnix-gui mkvmerge",
    )
    assert result == ("flatpak", "run", "org.bunkus.mkvtoolnix-gui", "mkvmerge")


def test_prepare_mkvmerge_path_with_base_string() -> None:
    result = utils.prepare_mkvtoolnix_path("mkvmerge")
    assert result == ("mkvmerge",)


@patch("pathlib.Path.exists")
def test_prepare_mkvmerge_path_with_linux_path(mock_exists):  # noqa: ANN201, ANN001
    mock_exists.return_value = True
    path = "/home/bob/dir with space/mkv/mkvmerge"
    result = utils.prepare_mkvtoolnix_path(path)
    assert result == (path,)


@patch("pathlib.Path.exists")
def test_prepare_mkvmerge_path_with_windows_path(mock_exists):  # noqa: ANN201, ANN001
    mock_exists.return_value = True
    path = r"C:\Program Files\MKVToolNix\mkvmerge.exe"
    result = utils.prepare_mkvtoolnix_path(path)
    assert result == (path,)


def test_prepare_mkvmerge_path_with_nonexistent_path() -> None:
    path = "/nonexistent/path with spaces/mkvmerge"
    result = utils.prepare_mkvtoolnix_path(path)
    assert result == ("/nonexistent/path", "with", "spaces/mkvmerge")


def test_prepare_mkvmerge_path_with_list() -> None:
    result = utils.prepare_mkvtoolnix_path(["mkvmerge", "path"])
    assert result == ("mkvmerge", "path")


def test_prepare_mkvmerge_path_with_pathlike() -> None:
    path = Path(Path(__file__).parent, "mkvmerge")
    result = utils.prepare_mkvtoolnix_path(path)
    assert result == (str(path),)


def test_prepare_mkvmerge_path_with_invalid_argument() -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        utils.prepare_mkvtoolnix_path(cast(str, 123))
