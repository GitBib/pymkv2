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
        # effective_language is now the canonical /B code (normalized).
        assert track.effective_language == "rus"

        track.language = "eng"
        assert track.language == "eng"
        assert track.language_ietf == "ru-RU"
        # language_ietf wins, normalized to "rus".
        assert track.effective_language == "rus"


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


def test_track_options_skips_unnormalizable_language_ietf() -> None:
    # When ``language_ietf`` cannot be normalized to a known /B code, the
    # command generator must not emit it — otherwise mkvmerge would receive
    # the bogus tag and override the valid ``--language`` we already yielded.
    # This pairs with ``effective_language`` falling back to ``language`` in
    # the same case, keeping the read- and write-side APIs consistent.
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info") as mock_info,
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
        patch.object(sys.modules["pymkv.MKVFile"], "verify_mkvmerge", return_value=True),
        patch.object(sys.modules["pymkv.MKVTrack"], "checking_file_path", side_effect=lambda x: x),
    ):
        mock_info.return_value.tracks = [
            MagicMock(id=0, codec="V_MS/VFW/FOURCC", type="video", start_pts=0),
        ]

        mkv = MKVFile()
        track = MKVTrack("dummy.mkv", track_id=0)
        track.language = "eng"
        track.language_ietf = "xyz"  # unrecognized — must be skipped
        mkv.add_track(track)

        command = mkv.command("output.mkv", subprocess=True)

        assert command.count("--language") == 1
        assert "0:eng" in command
        assert "0:xyz" not in command


def test_track_options_emits_und_sentinel_language_ietf() -> None:
    # The BCP 47 ``und`` sentinel is a valid mkvmerge tag that explicitly
    # marks a track as "undefined language". ``normalize_language`` collapses
    # it to ``None`` for matching purposes, but the write side must still
    # emit it so mkvmerge actually overwrites any existing source-language
    # tag with ``und`` (rather than silently passing the source through).
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info") as mock_info,
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
        patch.object(sys.modules["pymkv.MKVFile"], "verify_mkvmerge", return_value=True),
        patch.object(sys.modules["pymkv.MKVTrack"], "checking_file_path", side_effect=lambda x: x),
    ):
        mock_info.return_value.tracks = [
            MagicMock(id=0, codec="V_MS/VFW/FOURCC", type="video", start_pts=0),
        ]

        mkv = MKVFile()
        track = MKVTrack("dummy.mkv", track_id=0)
        track.language_ietf = "und"
        mkv.add_track(track)

        command = mkv.command("output.mkv", subprocess=True)

        assert command.count("--language") == 1
        assert "0:und" in command


def test_track_options_und_ietf_does_not_override_language() -> None:
    # When ``language="eng"`` and ``language_ietf="und"`` are both set,
    # ``effective_language`` resolves to ``"eng"`` (the read side falls back
    # to ``language`` because the ``und`` sentinel collapses to ``None``).
    # The write side must mirror that precedence — emitting ``0:und`` after
    # ``0:eng`` would let mkvmerge override the valid value, leaving the read
    # and write APIs disagreeing about the same track.
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info") as mock_info,
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
        patch.object(sys.modules["pymkv.MKVFile"], "verify_mkvmerge", return_value=True),
        patch.object(sys.modules["pymkv.MKVTrack"], "checking_file_path", side_effect=lambda x: x),
    ):
        mock_info.return_value.tracks = [
            MagicMock(id=0, codec="V_MS/VFW/FOURCC", type="video", start_pts=0),
        ]

        mkv = MKVFile()
        track = MKVTrack("dummy.mkv", track_id=0)
        track.language = "eng"
        track.language_ietf = "und"
        mkv.add_track(track)
        assert track.effective_language == "eng"

        command = mkv.command("output.mkv", subprocess=True)

        assert command.count("--language") == 1
        assert "0:eng" in command
        assert "0:und" not in command


def test_track_options_und_subtag_ietf_does_not_override_language() -> None:
    # ``"und-Latn"`` (BCP 47 undefined-language with a script subtag) does
    # not normalize to a /B code, so ``effective_language`` falls back to
    # ``language``. The write side must not emit the IETF tag in that case.
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info") as mock_info,
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
        patch.object(sys.modules["pymkv.MKVFile"], "verify_mkvmerge", return_value=True),
        patch.object(sys.modules["pymkv.MKVTrack"], "checking_file_path", side_effect=lambda x: x),
    ):
        mock_info.return_value.tracks = [
            MagicMock(id=0, codec="V_MS/VFW/FOURCC", type="video", start_pts=0),
        ]

        mkv = MKVFile()
        track = MKVTrack("dummy.mkv", track_id=0)
        track.language = "eng"
        track.language_ietf = "und-Latn"
        mkv.add_track(track)
        assert track.effective_language == "eng"

        command = mkv.command("output.mkv", subprocess=True)

        assert command.count("--language") == 1
        assert "0:eng" in command
        assert "0:und-Latn" not in command


def test_track_options_name_ietf_does_not_emit_and_reads_consistently() -> None:
    # ``language_ietf="English"`` is a name, not a tag mkvmerge accepts.
    # The writer drops it (``is_known_language`` rejects names) and the
    # reader must agree — ``effective_language`` falling through to
    # ``language`` keeps the two ends consistent. Without the fall-through,
    # the read side would report ``"eng"`` while mkvmerge muxed no
    # ``--language`` at all.
    with (
        patch.object(sys.modules["pymkv.MKVTrack"], "get_file_info") as mock_info,
        patch.object(sys.modules["pymkv.MKVTrack"], "verify_supported", return_value=True),
        patch.object(sys.modules["pymkv.MKVFile"], "verify_mkvmerge", return_value=True),
        patch.object(sys.modules["pymkv.MKVTrack"], "checking_file_path", side_effect=lambda x: x),
    ):
        mock_info.return_value.tracks = [
            MagicMock(id=0, codec="V_MS/VFW/FOURCC", type="video", start_pts=0),
        ]

        mkv = MKVFile()
        track = MKVTrack("dummy.mkv", track_id=0)
        track.language = None
        track.language_ietf = "English"
        mkv.add_track(track)
        assert track.effective_language is None

        command = mkv.command("output.mkv", subprocess=True)

        assert command.count("--language") == 0
        assert "0:English" not in command
