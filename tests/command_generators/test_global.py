from typing import Any
from unittest.mock import MagicMock

from pymkv.command_generators import GlobalOptions


def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_global_options(mock_mkv: MagicMock) -> None:
    mock_mkv._global_tags_file = "tags.xml"  # noqa: SLF001

    opts = GlobalOptions()
    args = gen_to_list(opts, mock_mkv)
    assert args == ["--global-tags", "tags.xml"]

    mock_mkv._global_tags_file = None  # noqa: SLF001
    args = gen_to_list(opts, mock_mkv)
    assert args == []
