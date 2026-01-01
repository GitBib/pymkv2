from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pymkv.MKVFile import MKVFile

from .base import CommandGeneratorBase


class TrackOrderOptions(CommandGeneratorBase):
    """Handles track ordering."""

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
        # Logic from original command()
        track_order = [f"{track.file_id}:{track.track_id}" for track in mkv_file.tracks if track.file_id is not None]

        # NOTE: logic in original was relying on assigning file_id during iteration
        # We need to preserve that side-effect or calculating it beforehand
        # In this refactor, we should separate calculation from generation if possible
        # But for now, let's implement the generation assuming file_id is correct
        # OR we need a PreProcessing step.
        # MKVFile.command() assigned file_ids. "unique_file_dict"

        # Let's handle this in MKVFile.command *before* calling generators
        # so this class just reads them.
        if track_order:
            yield "--track-order"
            yield ",".join(track_order)
