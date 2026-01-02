import sys
from unittest.mock import MagicMock, patch

from pymkv import MKVFile, MKVTrack


def test_language_loss_fix() -> None:
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info") as mock_info,
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
        patch.object(sys.modules["pymkv.MKVTrack"], "checking_file_path", side_effect=lambda x: x),
    ):
        mock_info.return_value.tracks = [MagicMock(id=0, codec="V_MS/VFW/FOURCC", type="video", start_pts=0)]

        track = MKVTrack("dummy.mkv", track_id=0)

        track.language = "rus"
        assert track.language == "rus"
        assert track.language_ietf is None
        assert track.effective_language == "rus"

        track.language_ietf = "ru-RU"
        assert track.language == "rus"
        assert track.language_ietf == "ru-RU"
        assert track.effective_language == "ru-RU"

        track.language = "eng"
        assert track.language == "eng"
        assert track.language_ietf == "ru-RU"
        assert track.effective_language == "ru-RU"


def test_track_options_command_generation() -> None:
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info") as mock_info,
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
        patch.object(sys.modules["pymkv.MKVFile"], "verify_mkvmerge", return_value=True),
        patch.object(sys.modules["pymkv.MKVTrack"], "checking_file_path", side_effect=lambda x: x),
    ):
        mock_info.return_value.tracks = [
            MagicMock(id=0, codec="V_MS/VFW/FOURCC", type="video", start_pts=0),
            MagicMock(id=1, codec="A_AAC", type="audio", start_pts=0),
        ]

        mkv = MKVFile()
        track = MKVTrack("dummy.mkv", track_id=0)
        track.language = "rus"
        track.language_ietf = "ru-RU"
        mkv.add_track(track)

        command = mkv.command("output.mkv", subprocess=True)

        expected_language_count = 2
        assert command.count("--language") == expected_language_count
        assert "0:rus" in command
        assert "0:ru-RU" in command
