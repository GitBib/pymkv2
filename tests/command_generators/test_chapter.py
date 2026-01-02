from typing import Any
from unittest.mock import MagicMock

from pymkv.command_generators import ChapterOptions


def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_chapter_options(mock_mkv: MagicMock) -> None:
    mock_mkv._chapters_file = "chapters.xml"  # noqa: SLF001
    mock_mkv._chapter_language = "eng"  # noqa: SLF001

    opts = ChapterOptions()
    args = gen_to_list(opts, mock_mkv)

    assert "--chapters" in args
    assert "chapters.xml" in args
    assert "--chapter-language" in args
    assert "eng" in args

    mock_mkv._chapters_file = None  # noqa: SLF001
    mock_mkv._chapter_language = None  # noqa: SLF001
    args = gen_to_list(opts, mock_mkv)
    assert args == []
