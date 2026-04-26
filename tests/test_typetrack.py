from unittest.mock import MagicMock

import pytest

from pymkv.TypeTrack import get_track_extension


@pytest.mark.parametrize(
    ("track_type", "codec", "expected"),
    [
        pytest.param("video", "V_MPEG1", "mpg", id="video-V_MPEG1"),
        pytest.param("video", "V_MPEG2", "mpg", id="video-V_MPEG2"),
        pytest.param("video", "V_MPEG4/ISO/AVC", "264", id="video-V_MPEG4_ISO_AVC"),
        pytest.param("video", "MPEG-4p10", "h264", id="video-MPEG-4p10"),
        pytest.param("video", "HEVC", "h265", id="video-HEVC"),
        pytest.param("video", "V_MS/VFW/FOURCC", "avi", id="video-V_MS_VFW_FOURCC"),
        pytest.param("video", "V_REAL", "rm", id="video-V_REAL"),
        pytest.param("video", "V_THEORA", "ogg", id="video-V_THEORA"),
        pytest.param("video", "V_VP8", "ivf", id="video-V_VP8"),
        pytest.param("video", "V_VP9", "ivf", id="video-V_VP9"),
        pytest.param("video", "AVC/H.264/MPEG-4p10", "mp4", id="video-AVC_H264_MPEG-4p10"),
        pytest.param("audio", "AAC", "aac", id="audio-AAC"),
        pytest.param("audio", "AC3", "ac3", id="audio-AC3"),
        pytest.param("audio", "AC-3", "ac3", id="audio-AC-3"),
        pytest.param("audio", "ALAC", "caf", id="audio-ALAC"),
        pytest.param("audio", "DTS", "dts", id="audio-DTS"),
        pytest.param("audio", "FLAC", "flac", id="audio-FLAC"),
        pytest.param("audio", "MPEG/L2", "mp2", id="audio-MPEG_L2"),
        pytest.param("audio", "MPEG/L3", "mp3", id="audio-MPEG_L3"),
        pytest.param("audio", "OPUS", "ogg", id="audio-OPUS"),
        pytest.param("audio", "PCM", "wav", id="audio-PCM"),
        pytest.param("audio", "REAL", "ra", id="audio-REAL"),
        pytest.param("audio", "TRUEHD", "thd", id="audio-TRUEHD"),
        pytest.param("audio", "MLP", "mlp", id="audio-MLP"),
        pytest.param("audio", "TTA1", "tta", id="audio-TTA1"),
        pytest.param("audio", "VORBIS", "ogg", id="audio-VORBIS"),
        pytest.param("audio", "WAVPACK4", "wv", id="audio-WAVPACK4"),
        pytest.param("audio", "Vorbis", "ogg", id="audio-Vorbis"),
        pytest.param("subtitles", "PGS", "sup", id="sub-PGS"),
        pytest.param("subtitles", "ASS", "ass", id="sub-ASS"),
        pytest.param("subtitles", "SubStationAlpha", "ass", id="sub-SubStationAlpha"),
        pytest.param("subtitles", "SSA", "ssa", id="sub-SSA"),
        pytest.param("subtitles", "UTF8", "srt", id="sub-UTF8"),
        pytest.param("subtitles", "SubRip/SRT", "srt", id="sub-SubRip_SRT"),
        pytest.param("subtitles", "ASCII", "srt", id="sub-ASCII"),
        pytest.param("subtitles", "VOBSUB", "sub", id="sub-VOBSUB"),
        pytest.param("subtitles", "USF", "usf", id="sub-USF"),
        pytest.param("subtitles", "WEBVTT", "vtt", id="sub-WEBVTT"),
        pytest.param("audio", "V_MS/VFW/FOURCC, WVC1", "wvc", id="audio-VFW_WVC1"),
        pytest.param("audio", "VC-1", "wvc", id="audio-VC-1"),
    ],
)
def test_get_track_extension_known(track_type: str, codec: str, expected: str) -> None:
    track = MagicMock()
    track.track_type = track_type
    track.track_codec = codec
    assert get_track_extension(track) == expected


def test_get_track_extension_unknown_codec() -> None:
    track = MagicMock()
    track.track_type = "video"
    track.track_codec = "UNKNOWN_CODEC_XYZ"
    assert get_track_extension(track) is None


def test_get_track_extension_unknown_type() -> None:
    track = MagicMock()
    track.track_type = "data"
    track.track_codec = "AAC"
    assert get_track_extension(track) is None
