from typing import Any
from unittest.mock import MagicMock

from pymkv.command_generators import BaseOptions


# Helper
def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_base_options(mock_mkv: MagicMock) -> None:
    mock_mkv.output_path = "output.mkv"
    mock_mkv.title = "My Title"
    mock_mkv.no_track_statistics_tags = True

    opts = BaseOptions()
    args = gen_to_list(opts, mock_mkv)
    assert args == ["-o", "output.mkv", "--title", "My Title", "--disable-track-statistics-tags"]

    mock_mkv.title = None
    mock_mkv.no_track_statistics_tags = False
    args = gen_to_list(opts, mock_mkv)
    assert args == ["-o", "output.mkv"]
