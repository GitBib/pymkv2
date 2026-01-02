"""
:class:`~pymkv.MKVAttachment` classes are used to represent attachment files within an MKV or to be used in an
MKV.

Examples
--------
Below are some basic examples of how the :class:`~pymkv.MKVAttachment` objects can be used.

Create a new :class:`~pymkv.MKVAttachment` and add it to an :class:`~pymkv.MKVFile`.

>>> from pymkv import MKVAttachment
>>> attachment = MKVAttachment('path/to/attachment.jpg', name='NAME')  # doctest: +SKIP
>>> attachment.description = 'DESCRIPTION'  # doctest: +SKIP

Attachments can also be added directly to an :class:`~pymkv.MKVFile`.

>>> from pymkv import MKVFile
>>> mkv = MKVFile('path/to/file.mkv')  # doctest: +SKIP
>>> mkv.add_attachment('path/to/other/attachment.png')  # doctest: +SKIP

Now, the MKV can be muxed with both attachments.

>>> mkv.add_attachment(attachment)  # doctest: +SKIP
>>> mkv.mux('path/to/output.mkv')  # doctest: +SKIP
"""

from __future__ import annotations

from mimetypes import guess_type
from pathlib import Path


class MKVAttachment:
    """A class that represents an MKV attachment for an :class:`~pymkv.MKVFile` object.

    Parameters
    ----------
    file_path : str
        The path to the attachment file.
    name : str, optional
        The name that will be given to the attachment when muxed into a file.
    description : str, optional
        The description that will be given to the attachment when muxed into a file.
    attach_once : bool, optional
        Determines if the attachment should be added to all split files or only the first. Default is False,
        which will attach to all files.

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
    """

    def __init__(
        self,
        file_path: str,
        name: str | None = None,
        description: str | None = None,
        attach_once: bool | None = False,
    ) -> None:
        self._mime_type: str | None = None
        self._file_path: str
        self.file_path = file_path
        self._name = name
        self._description = description
        self._attach_once = attach_once
        self._source_id: int | None = None
        self._source_file: str | None = None

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
    def file_path(self) -> str:
        """str: The path to the attachment file.

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
        self._mime_type = guess_type(fp)[0]
        self._name = None
        self._file_path = str(fp)

    @property
    def name(self) -> str | None:
        """
        Get the name of the attachment.

        Returns:
            str | None: The name of the attachment or None if not set.
        """
        return self._name

    @name.setter
    def name(self, name: str | None) -> None:
        """
        Set the name of the attachment.

        Parameters:
            name (str | None): The name to set for the attachment.
        """
        self._name = name

    @property
    def description(self) -> str | None:
        """
        Get the description of the attachment.

        Returns:
            str | None: The description of the attachment or None if not set.
        """
        return self._description

    @description.setter
    def description(self, description: str | None) -> None:
        """
        Set the description of the attachment.

        Parameters:
            description (str | None): The description to set for the attachment.
        """
        self._description = description

    @property
    def mime_type(self) -> str | None:
        """
        Get the MIME type of the attachment.

        Returns:
            str | None: The MIME type of the attachment or None if not detected.
        """
        return self._mime_type

    @mime_type.setter
    def mime_type(self, mime_type: str | None) -> None:
        """
        Set the MIME type of the attachment.

        Parameters:
            mime_type (str | None): The MIME type to set for the attachment.
        """
        self._mime_type = mime_type

    @property
    def attach_once(self) -> bool | None:
        """
        Get whether the attachment should be added only to the first split file.

        Returns:
            bool | None: True if attachment should only be added to the first split file,
                        False if it should be added to all split files.
        """
        return self._attach_once

    @attach_once.setter
    def attach_once(self, attach_once: bool | None) -> None:
        """
        Set whether the attachment should be added only to the first split file.

        Parameters:
            attach_once (bool | None): True to add attachment only to the first split file,
                                      False to add it to all split files.
        """
        self._attach_once = attach_once

    @property
    def source_id(self) -> int | None:
        """
        Get the ID of the attachment from the source file.

        Returns:
            int | None: The ID of the attachment in the source file or None if not from a source file.
        """
        return self._source_id

    @source_id.setter
    def source_id(self, source_id: int | None) -> None:
        """
        Set the ID of the attachment from the source file.

        Parameters:
            source_id (int | None): The ID to set for the attachment in the source file.
        """
        self._source_id = source_id

    @property
    def source_file(self) -> str | None:
        """
        Get the path to the source file containing the attachment.

        Returns:
            str | None: The path to the source file or None if not from a source file.
        """
        return self._source_file

    @source_file.setter
    def source_file(self, source_file: str | None) -> None:
        """
        Set the path to the source file containing the attachment.

        Parameters:
            source_file (str | None): The path to set for the source file.
        """
        self._source_file = source_file
