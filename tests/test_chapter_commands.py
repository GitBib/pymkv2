from pathlib import Path

from pymkv import MKVFile


def test_chapter_command_generation(get_path_test_chapters_xml: Path) -> None:
    mkv = MKVFile()
    chapter_file = get_path_test_chapters_xml
    # chapter_file already touched by fixture
    mkv.chapters(str(chapter_file), language="eng")
    command = mkv.command("output.mkv")

    assert "--chapters" in command
    assert str(chapter_file) in command
    assert "--chapter-language" in command
    assert "eng" in command


def test_chapter_command_generation_subprocess(get_path_test_chapters_txt: Path) -> None:
    mkv = MKVFile()
    chapter_file = get_path_test_chapters_txt
    # chapter_file already touched by fixture
    mkv.chapters(str(chapter_file))
    command_list = mkv.command("output.mkv", subprocess=True)

    assert isinstance(command_list, list)
    assert "--chapters" in command_list
    assert str(chapter_file) in command_list
    assert "--chapter-language" not in command_list
