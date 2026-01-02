from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pymkv.MKVFile import MKVFile

from .base import CommandGeneratorBase


class AttachmentOptions(CommandGeneratorBase):
    """Handles attachment flags."""

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
        for attachment in mkv_file.attachments:
            if attachment.source_id is not None:
                continue
            if attachment.name:
                yield "--attachment-name"
                yield attachment.name
            if attachment.description:
                yield "--attachment-description"
                yield attachment.description
            if attachment.mime_type:
                yield "--attachment-mime-type"
                yield attachment.mime_type

            yield "--attach-file" if not attachment.attach_once else "--attach-file-once"
            yield attachment.file_path
