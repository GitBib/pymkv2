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
    size : int | None
        The size of the attachment in bytes, as reported by the file it was read from. It is ``None`` for an
        attachment built from a local path, since that attachment is not part of an MKV yet.
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
        self._size: int | None = None

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

        For an attachment read out of an MKV this is the containing file, and the path cannot be changed.
        Replace such an attachment with :meth:`~pymkv.MKVFile.remove_attachment` followed by
        :meth:`~pymkv.MKVFile.add_attachment`.

        Raises
        ------
        FileNotFoundError
            Raised if `file_path` does not exist.
        ValueError
            Raised when changing the path of an attachment that was read from a file.
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
        ValueError
            If this attachment was read from a file and `file_path` names a different one.

        Returns
        -------
        None
        """
        current = getattr(self, "_file_path", None)
        if current is not None and str(file_path) == current:
            # Byte-identical path. Nothing to validate, and nothing learned about the file has gone stale,
            # so this stays a no-op even if the file has since been deleted.
            return
        fp = Path(file_path).expanduser()
        if not fp.is_file():
            msg = f'"{fp}" does not exist'
            raise FileNotFoundError(msg)
        if current is not None and Path(current).is_file() and fp.samefile(current):
            # Same file spelled differently, e.g. after the caller normalized the path.
            return
        if getattr(self, "_source_id", None) is not None:
            # This attachment is a reference into an MKV, not a local file. Repointing it used to look like
            # it worked while AttachmentOptions skipped it, so the old embedded payload was muxed instead.
            msg = (
                f"attachment {self._name!r} (id {self._source_id}) was read from "
                f'"{current}", so its path cannot be changed. '
                "Remove this attachment and add a new MKVAttachment for the replacement instead."
            )
            raise ValueError(msg)
        self._mime_type = guess_type(fp)[0]
        self._name = None
        # The name and size described the attachment this object used to point at.
        self._size = None
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

        Pointing at a different attachment invalidates the size, which described the previous one.

        Parameters:
            source_id (int | None): The ID to set for the attachment in the source file.
        """
        if source_id != self._source_id:
            self._size = None
        self._source_id = source_id

    @property
    def size(self) -> int | None:
        """
        Get the size of the attachment in bytes.

        The value comes from the file the attachment was read from, not from
        :attr:`~pymkv.MKVAttachment.file_path`, which points at the containing MKV for an attachment read
        out of one.

        It stays None for an attachment built from a local path, including after
        :meth:`~pymkv.MKVFile.mux`: this object is never refreshed from the output. Load the muxed file into
        a new :class:`~pymkv.MKVFile` to read the sizes it ended up with.

        Returns:
            int | None: The size in bytes, or None for an attachment that was not read from a file.
        """
        return self._size

    @size.setter
    def size(self, size: int | None) -> None:
        """
        Set the size of the attachment in bytes.

        Parameters:
            size (int | None): The size in bytes.
        """
        self._size = size

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

        Pointing at a different file invalidates the size, which described the previous one.

        Parameters:
            source_file (str | None): The path to set for the source file.
        """
        if source_file != self._source_file:
            self._size = None
        self._source_file = source_file
