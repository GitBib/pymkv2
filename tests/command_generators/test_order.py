from typing import Any
from unittest.mock import MagicMock

from pymkv.command_generators import TrackOrderOptions


def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_track_order_options(mock_mkv: MagicMock) -> None:
    track_1_id_1 = MagicMock()
    track_1_id_1.file_id = 0
    track_1_id_1.track_id = 1
    track_2_id_0 = MagicMock()
    track_2_id_0.file_id = 1
    track_2_id_0.track_id = 0

    mock_mkv.tracks = [track_1_id_1, track_2_id_0]

    opts = TrackOrderOptions()
    args = gen_to_list(opts, mock_mkv)

    assert args == ["--track-order", "0:1,1:0"]
