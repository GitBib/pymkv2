from pathlib import Path

import msgspec

from pymkv import MKVFile, MKVTrack
from pymkv.Verifications import get_file_info


def test_setter_exclusivity(get_path_test_file: Path) -> None:
    """
    Test that setting language clears language_ietf and vice-versa in memory.
    """
    track = MKVTrack(str(get_path_test_file), track_id=0)

    # 1. Set IETF, ensure legacy cleared (though it might be None initally)
    track.language_ietf = "en-US"
    assert track.language_ietf == "en-US"
    assert track.language is None

    # 2. Set Legacy, ensure IETF cleared
    track.language = "eng"
    assert track.language == "eng"
    assert track.language_ietf is None

    # 3. Set IETF again
    track.language_ietf = "fr-CA"
    assert track.language_ietf == "fr-CA"
    assert track.language is None


def test_language_precedence_physical(get_path_test_file: Path, tmp_path: Path) -> None:
    """
    Test that strict setter logic results in correct output file metadata.
    """
    # Create a file with IETF language
    mkv = MKVFile()
    track = MKVTrack(str(get_path_test_file), track_id=0)
    track.language_ietf = "en-US"  # Should clear any default 'eng' if it was set
    mkv.add_track(track)

    output_ietf = str(tmp_path / "output_ietf.mkv")
    mkv.mux(output_ietf)

    # Verify IETF is present
    info_ietf = msgspec.to_builtins(get_file_info(output_ietf, "mkvmerge"))
    t0_ietf = info_ietf["tracks"][0]
    properties_ietf = t0_ietf.get("properties", {})

    # mkvmerge should report language_ietf.
    # Note: mkvmerge might also automatically fill 'language' from IETF,
    # but we want to ensure IETF is what we set.
    assert properties_ietf.get("language_ietf") == "en-US"
    # Legacy language might be 'eng' derived from 'en-US' by mkvmerge
    assert properties_ietf.get("language") == "eng"

    # Now take that IETF file and override with legacy language
    mkv2 = MKVFile(output_ietf)
    t0_legacy = mkv2.tracks[0]

    # Check that effective_language picked up IETF
    assert t0_legacy.language_ietf == "en-US"

    # Override with 'ger' (German)
    t0_legacy.language = "ger"

    # In memory check
    assert t0_legacy.language == "ger"
    assert t0_legacy.language_ietf is None

    output_legacy = str(tmp_path / "output_legacy.mkv")
    mkv2.mux(output_legacy)

    # Verify output has GERMAN and NO IETF (or IETF matches 'ger' if mkvmerge adds it)
    info_legacy = msgspec.to_builtins(get_file_info(output_legacy, "mkvmerge"))
    t0_legacy_out = info_legacy["tracks"][0]
    properties_legacy = t0_legacy_out.get("properties", {})

    assert properties_legacy.get("language") == "ger"
    # mkvmerge might not output language_ietf if it's just 'ger', or it might be 'de'
    # The key point is it's NOT 'en-US'
    assert properties_legacy.get("language_ietf") != "en-US"
