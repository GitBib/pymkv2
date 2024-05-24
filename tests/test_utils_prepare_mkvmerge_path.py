import os
from pathlib import Path

import pytest

from pymkv import utils


def test_prepare_mkvmerge_path_with_string() -> None:
    result = utils.prepare_mkvtoolnix_path("flatpak run org.bunkus.mkvtoolnix-gui mkvmerge")
    assert result == ["flatpak", "run", "org.bunkus.mkvtoolnix-gui", "mkvmerge"]


def test_prepare_mkvmerge_path_with_base_string() -> None:
    result = utils.prepare_mkvtoolnix_path("mkvmerge")
    assert result == ["mkvmerge"]


def test_prepare_mkvmerge_path_with_list() -> None:
    result = utils.prepare_mkvtoolnix_path(["mkvmerge", "path"])
    assert result == ["mkvmerge", "path"]


def test_prepare_mkvmerge_path_with_pathlike() -> None:
    path = Path(os.path.join(os.path.dirname(__file__), "mkvmerge"))  # noqa: PTH120, PTH118
    result = utils.prepare_mkvtoolnix_path(path)
    assert result == [str(path)]


def test_prepare_mkvmerge_path_with_invalid_argument() -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        utils.prepare_mkvtoolnix_path(123)
