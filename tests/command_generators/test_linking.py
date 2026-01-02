from typing import Any
from unittest.mock import MagicMock

from pymkv.command_generators import LinkingOptions


def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_linking_options(mock_mkv: MagicMock) -> None:
    mock_mkv._link_to_previous_file = "prev.mkv"  # noqa: SLF001
    mock_mkv._link_to_next_file = "next.mkv"  # noqa: SLF001

    opts = LinkingOptions()
    args = gen_to_list(opts, mock_mkv)

    assert args == ["--link-to-previous", "=prev.mkv", "--link-to-next", "=next.mkv"]

    mock_mkv._link_to_previous_file = None  # noqa: SLF001
    mock_mkv._link_to_next_file = None  # noqa: SLF001
    args = gen_to_list(opts, mock_mkv)
    assert args == []
