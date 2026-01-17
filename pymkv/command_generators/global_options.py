"""Generators for global and basic options of mkvmerge.

Includes `BaseOptions` for fundamental flags (like title, output) and `GlobalOptions` for tags.

Examples
--------
>>> from pymkv.command_generators.global_options import GlobalOptions, BaseOptions  # doctest: +SKIP
>>> global_opts = GlobalOptions()  # doctest: +SKIP
>>> base_opts = BaseOptions()  # doctest: +SKIP
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pymkv.MKVFile import MKVFile

from .base import CommandGeneratorBase


class BaseOptions(CommandGeneratorBase):
    """Handles basic options like title and quiet mode."""

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
        >>> mkv.title = "My Movie"
        >>> options = BaseOptions()
        >>> args = list(options.generate(mkv))
        >>> "-o" in args
        True
        >>> "--title" in args
        True
        >>> args[args.index("--title") + 1]
        'My Movie'
        """
        yield "-o"
        yield f"{mkv_file.output_path}"

        if mkv_file.title:
            yield "--title"
            yield mkv_file.title

        if mkv_file.no_track_statistics_tags:
            yield "--disable-track-statistics-tags"


class GlobalOptions(CommandGeneratorBase):
    """Handles global tags and other file-wide settings."""

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
        >>> mkv._global_tags_file = "tags.xml"  # doctest: +SKIP
        >>> options = GlobalOptions()
        >>> # args = list(options.generate(mkv))
        >>> # "--global-tags" in args
        """
        if mkv_file._global_tags_file:  # noqa: SLF001
            yield "--global-tags"
            yield mkv_file._global_tags_file  # noqa: SLF001
