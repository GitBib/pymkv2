from typing import Any
from unittest.mock import MagicMock

from pymkv import MKVTrack
from pymkv.command_generators import TrackOptions


def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_track_options_grouping(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    # Setup tracks from two different files
    # Track 1: File A, ID 0
    video_track = MagicMock(spec=MKVTrack)
    video_track.file_path = "fileA.mkv"
    video_track.file_id = 0
    video_track.track_id = 0
    video_track.track_type = "video"
    video_track._track_id = 0  # Original ID  # noqa: SLF001
    video_track.tags = {}

    # Track 2: File A, ID 1
    audio_track = MagicMock(spec=MKVTrack)
    audio_track.file_path = "fileA.mkv"
    audio_track.file_id = 0
    audio_track.track_id = 1
    audio_track.track_type = "audio"
    audio_track._track_id = 1  # noqa: SLF001
    audio_track.language = "eng"
    audio_track.tags = {}
    # ensure default/forced attrs are clean
    audio_track.configure_mock(**dict.fromkeys(["track_name", "default_track", "forced_track"], None))

    # Track 3: File B, ID 0
    subtitle_track = MagicMock(spec=MKVTrack)
    subtitle_track.file_path = "fileB.mkv"
    subtitle_track.file_id = 1
    subtitle_track.track_id = 0
    subtitle_track.track_type = "subtitles"
    subtitle_track._track_id = 0  # noqa: SLF001
    subtitle_track.tags = {}
    subtitle_track.configure_mock(**dict.fromkeys(["track_name", "language", "default_track"], None))

    mock_mkv.tracks = [video_track, audio_track, subtitle_track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()

    mock_track_cleaner(video_track)
    mock_track_cleaner(audio_track)
    mock_track_cleaner(subtitle_track)

    audio_track.language = "eng"

    args = gen_to_list(opts, mock_mkv)

    # File A check
    assert "fileA.mkv" in args
    assert "fileB.mkv" in args

    # Check that fileA appears once
    assert args.count("fileA.mkv") == 1

    # Group for A
    idx_a = args.index("fileA.mkv")
    opts_a = args[:idx_a]

    # Check A
    assert "--language" in opts_a
    # language is for t2 (id 1) -> 1:eng
    assert "1:eng" in opts_a
    assert "--audio-tracks" in opts_a
    assert "1" in opts_a
    assert "--video-tracks" in opts_a
    assert "0" in opts_a

    # Check B
    # t3 is subtitle -> --subtitle-tracks 0
    assert "--no-video" in args[idx_a:]
    assert "--no-audio" in args[idx_a:]
    assert "--subtitle-tracks" in args[idx_a:]
    assert "0" in args[idx_a:]
