from pathlib import Path

from pymkv import MKVFile


def test_add_file(get_base_path: Path, get_path_test_file: Path) -> None:
    output_file = get_base_path / "file.mkv_[1]_eng.ogg"
    mkv = MKVFile(get_path_test_file)
    mkv.tracks[1].extract()

    assert output_file.is_file()
