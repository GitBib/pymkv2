from typing import Any
from unittest.mock import MagicMock

from pymkv.command_generators import SplitOptions


def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_split_options(mock_mkv: MagicMock) -> None:
    mock_mkv._split_options = ["--split", "duration:00:00:10"]  # noqa: SLF001

    opts = SplitOptions()
    args = gen_to_list(opts, mock_mkv)

    assert args == ["--split", "duration:00:00:10"]

    mock_mkv._split_options = []  # noqa: SLF001
    args = gen_to_list(opts, mock_mkv)
    assert args == []
