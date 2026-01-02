from pathlib import Path
from typing import cast

from pymkv import MKVFile, MKVTrack


def test_language_persistence_real_file(tmp_path: Path, get_path_test_file: Path) -> None:
    source_mkv = str(tmp_path / "source.mkv")
    base_file = str(get_path_test_file)

    mkv_init = MKVFile(base_file)

    video_track_init = cast("MKVTrack", mkv_init.get_track(0))
    video_track_init.language = "rus"

    audio_track_init = cast("MKVTrack", mkv_init.get_track(1))
    audio_track_init.language = "eng"
    audio_track_init.language_ietf = "en-US"

    mkv_init.mux(source_mkv)

    mkv = MKVFile(source_mkv)

    video_track = cast("MKVTrack", mkv.get_track(0))
    assert video_track.language == "rus"
    ietf_lang = video_track.language_ietf
    assert ietf_lang is not None
    assert ietf_lang in ["ru", "rus"]
    eff_lang = video_track.effective_language
    assert eff_lang is not None
    assert eff_lang in ["ru", "rus", "ru-RU"]

    audio_track = cast("MKVTrack", mkv.get_track(1))
    assert audio_track.language == "eng"
    assert audio_track.language_ietf == "en-US"
    assert audio_track.effective_language == "en-US"

    output_mkv = str(tmp_path / "output.mkv")
    command = mkv.command(output_mkv, subprocess=True)

    assert "1:eng" in [c for i, c in enumerate(command) if i > 0 and command[i - 1] == "--language"]
    assert "1:en-US" in [c for i, c in enumerate(command) if i > 0 and command[i - 1] == "--language"]

    mkv.mux(output_mkv)
    mkv_out = MKVFile(output_mkv)
    audio_out = cast("MKVTrack", mkv_out.get_track(1))
    assert audio_out.language == "eng"
    assert audio_out.language_ietf == "en-US"
