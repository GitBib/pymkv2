"""Generator for splitting options.

Handles various splitting modes (size, duration, timestamps, etc.).

Examples
--------
>>> from pymkv.command_generators.split_options import SplitOptions  # doctest: +SKIP
>>> split_opts = SplitOptions()  # doctest: +SKIP
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pymkv.MKVFile import MKVFile

from .base import CommandGeneratorBase


class SplitOptions(CommandGeneratorBase):
    """Handles split options."""

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
        >>> mkv.split_duration("00:10:00")
        >>> options = SplitOptions()
        >>> args = list(options.generate(mkv))
        >>> "--split" in args
        True
        >>> "duration:00:10:00" in args
        True
        """
        yield from mkv_file._split_options  # noqa: SLF001
