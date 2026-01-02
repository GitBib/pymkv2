from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pymkv.MKVFile import MKVFile

from .base import CommandGeneratorBase


class LinkingOptions(CommandGeneratorBase):
    """Handles file linking options."""

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
        if mkv_file._link_to_previous_file:  # noqa: SLF001
            yield "--link-to-previous"
            yield f"={mkv_file._link_to_previous_file}"  # noqa: SLF001
        if mkv_file._link_to_next_file:  # noqa: SLF001
            yield "--link-to-next"
            yield f"={mkv_file._link_to_next_file}"  # noqa: SLF001
