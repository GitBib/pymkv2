"""
:class:`~pymkv.MKVAttachment` classes are used to represent attachment files within an MKV or to be used in an
MKV.

Examples
--------
Below are some basic examples of how the :class:`~pymkv.MKVAttachment` objects can be used.

Create a new :class:`~pymkv.MKVAttachment` and add it to an :class:`~pymkv.MKVFile`.

>>> from pymkv import MKVAttachment
>>> attachment = MKVAttachment('path/to/attachment.jpg', name='NAME')
>>> attachment.description = 'DESCRIPTION'

Attachments can also be added directly to an :class:`~pymkv.MKVFile`.

>>> from pymkv import MKVFile
>>> mkv = MKVFile('path/to/file.mkv')
>>> mkv.add_attachment('path/to/other/attachment.png')

Now, the MKV can be muxed with both attachments.

>>> mkv.add_attachment(attachment)
>>> mkv.mux('path/to/output.mkv')

Extract an attachment from an existing MKV file.

>>> mkv = MKVFile('path/to/file.mkv')
>>> attachment = mkv.attachments[0]
>>> attachment.extract('path/to/output/directory')
"""

from __future__ import annotations

import os
import subprocess as sp
from collections.abc import Iterable
from mimetypes import guess_type
from pathlib import Path

from pymkv.utils import prepare_mkvtoolnix_path


class MKVAttachment:
    """A class that represents an MKV attachment for an :class:`~pymkv.MKVFile` object.

    Parameters
    ----------
    file_path : str, optional
        The path to the attachment file. For new attachments to be added to an MKV.
        For existing attachments from an MKV, this is the source MKV file path.
    name : str, optional
        The name that will be given to the attachment when muxed into a file.
    description : str, optional
        The description that will be given to the attachment when muxed into a file.
    attach_once : bool, optional
        Determines if the attachment should be added to all split files or only the first. Default is False,
        which will attach to all files.
    attachment_id : int, optional
        The ID of an existing attachment in an MKV file. Used when representing attachments from existing files.
    mkvextract_path : str, list, os.PathLike, optional
        The path where pymkv looks for the mkvextract executable. Only needed for extracting attachments.

    Attributes
    ----------
    mime_type : str
        The attachment's MIME type. The type will be guessed when :attr:`~pymkv.MKVAttachment.file_path` is set.
    name : str
        The name that will be given to the attachment when muxed into a file.
    description : str
        The description that will be given to the attachment when muxed into a file.
    attach_once : bool
        Determines if the attachment should be added to all split files or only the first. Default is False,
        which will attach to all files.
    attachment_id : int, optional
        The ID of the attachment in the source MKV file. Only set for existing attachments.
    file_name : str, optional
        The original file name of the attachment in the MKV. Only set for existing attachments.
    size : int, optional
        The size of the attachment in bytes. Only set for existing attachments.
    """

    def __init__(  # noqa: PLR0913
        self,
        file_path: str | None = None,
        name: str | None = None,
        description: str | None = None,
        attach_once: bool | None = False,
        *,
        attachment_id: int | None = None,
        mkvextract_path: str | os.PathLike | Iterable[str] = "mkvextract",
        file_name: str | None = None,
        size: int | None = None,
    ) -> None:
        self.mime_type: str | None = None
        self._file_path: str | None = None
        self.attachment_id = attachment_id
        self.file_name = file_name
        self.size = size
        self.mkvextract_path = prepare_mkvtoolnix_path(mkvextract_path)

        # Set these before file_path since the setter checks them
        self.name = name
        self.description = description
        self.attach_once = attach_once

        if file_path is not None:
            self.file_path = file_path

    def __repr__(self) -> str:
        """
        Return a string representation of the object.

        Parameters:
            self (object): The object for which the string representation is generated.

        Returns:
            str: The string representation of the object. It is the representation of the object's __dict__ attribute.
        """
        return repr(self.__dict__)

    @property
    def file_path(self) -> str | None:
        """str | None: The path to the attachment file.

        For new attachments, this is the path to the file to be attached.
        For existing attachments, this is the path to the source MKV file.

        Raises
        ------
        FileNotFoundError
            Raised if `file_path` does not exist.
        """
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: str) -> None:
        """
        Parameters
        ----------
        file_path : str
            The file path to be set.

        Raises
        ------
        FileNotFoundError
            If the specified file does not exist.

        Returns
        -------
        None
        """
        fp = Path(file_path).expanduser()
        if not fp.is_file():
            msg = f'"{fp}" does not exist'
            raise FileNotFoundError(msg)
        self.mime_type = guess_type(fp)[0]
        # Only reset name if it's not already set (for existing attachments)
        if self.name is None and self.attachment_id is None:
            self.name = None
        self._file_path = str(fp)

    def extract(
        self,
        output_path: str | os.PathLike | None = None,
        silent: bool | None = False,
    ) -> str:
        """
        Extract the attachment from an MKV file.

        This method can only be used for attachments that were loaded from an existing MKV file
        (i.e., attachments with an attachment_id set).

        Args:
            output_path (str | os.PathLike | None, optional): The directory or file path where the attachment
                should be extracted. If a directory is provided, the original file name will be used.
                If None, extracts to the same directory as the source MKV file.
            silent (bool | None, optional): By default the mkvextract output will be shown unless silent is True.

        Returns:
            str: The path of the extracted file.

        Raises:
            ValueError: If this attachment doesn't have an attachment_id (not from an existing file).
            FileNotFoundError: If the source file_path doesn't exist.
        """
        if self.attachment_id is None:
            msg = (
                "Cannot extract attachment without an attachment_id. This attachment is not from an existing MKV file."
            )
            raise ValueError(msg)

        if self.file_path is None:
            msg = "Source file_path is not set for this attachment."
            raise ValueError(msg)

        # Determine output path
        if output_path is None:
            output_path = Path(self.file_path).parent / (self.file_name or f"attachment_{self.attachment_id}")
        else:
            output_path = Path(output_path) / (self.file_name or f"attachment_{self.attachment_id}")
        output_path = str(output_path.expanduser())

        # Build mkvextract command
        command = [
            *self.mkvextract_path,
            "attachments",
            str(self.file_path),
            f"{self.attachment_id}:{output_path}",
        ]

        if silent:
            sp.run(  # noqa: S603
                command,
                stdout=sp.DEVNULL,
                check=True,
            )
        else:
            sp.run(command, check=True, capture_output=True)  # noqa: S603

        return output_path
