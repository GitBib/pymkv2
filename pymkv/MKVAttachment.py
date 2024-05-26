from __future__ import annotations

from mimetypes import guess_type
from pathlib import Path

""":class:`~pymkv.MKVAttachment` classes are used to represent attachment files within an MKV or to be used in an
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
"""


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
        self.mime_type = None
        self._file_path = None
        self.file_path = file_path
        self.name = name
        self.description = description
        self.attach_once = attach_once

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
        file_path = Path(file_path).expanduser()
        if not file_path.is_file():
            msg = f'"{file_path}" does not exist'
            raise FileNotFoundError(msg)
        self.mime_type = guess_type(file_path)[0]
        self.name = None
        self._file_path = str(file_path)
