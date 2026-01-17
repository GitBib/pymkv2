"""Generator for chapter-specific options.

Handles flags for chapter files and languages.

Examples
--------
>>> from pymkv.command_generators.chapter_options import ChapterOptions  # doctest: +SKIP
>>> chap_opts = ChapterOptions()  # doctest: +SKIP
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pymkv.MKVFile import MKVFile

from .base import CommandGeneratorBase


class ChapterOptions(CommandGeneratorBase):
    """Handles chapters flags."""

    def generate(self, mkv_file: MKVFile) -> Iterator[str]:
        """
        Generates the command arguments for this specific part of the mkvmerge command.

        Parameters
        ----------
        mkv_file : MKVFile
            The :class:`~pymkv.MKVFile` object containing the data to be processed.

        Yields
        ------
        str
            The next command line argument token.

        Examples
        --------
        >>> from pymkv.MKVFile import MKVFile
        >>> mkv = MKVFile()
        >>> mkv.chapter_language = "eng"  # doctest: +SKIP
        >>> options = ChapterOptions()
        >>> # args = list(options.generate(mkv))
        >>> # "--chapter-language" in args
        """
        if mkv_file._chapter_language:  # noqa: SLF001
            yield "--chapter-language"
            yield mkv_file._chapter_language  # noqa: SLF001
        if mkv_file._chapters_file:  # noqa: SLF001
            yield "--chapters"
            yield mkv_file._chapters_file  # noqa: SLF001
