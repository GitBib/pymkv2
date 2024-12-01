from pathlib import Path

from pymkv import MKVFile, MKVTrack


def test_create_new_mkv(
    get_base_path: Path,
    get_path_test_file: Path,
    get_path_test_srt: Path,
) -> None:
    output_file = get_base_path / "new-file.mkv"
    mkv = MKVFile(str(get_path_test_file))
    track = MKVTrack(str(get_path_test_srt))

    mkv.add_track(track)

    assert len(mkv.tracks) == 3  # noqa: PLR2004
    mkv.mux(output_file)
