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
        """
        if mkv_file._global_tags_file:  # noqa: SLF001
            yield "--global-tags"
            yield mkv_file._global_tags_file  # noqa: SLF001
