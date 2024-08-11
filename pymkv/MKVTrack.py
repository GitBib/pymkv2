"""
:class:`~pymkv.MKVTrack` classes are used to represent tracks within an MKV or to be used in an MKV. They can
represent a video, audio, or subtitle track.

Examples
--------

Below are some basic examples of how the :class:`~pymkv.MKVTrack` objects can be used.

Create a new :class:`~pymkv.MKVTrack` from a track file. This example takes a standalone track file and uses it in an
:class:`~pymkv.MKVTrack`.

>>> from pymkv import MKVTrack
>>> track1 = MKVTrack("path/to/track.h264")
>>> track1.track_name = "Some Name"
>>> track1.language = "eng"

Create a new :class:`~pymkv.MKVTrack` from an MKV file. This example will take a specific track from an MKV and also
prevent any global tags from being included if the :class:`~pymkv.MKVTrack` is muxed into an :class:`~pymkv.MKVFile`.

>>> track2 = MKVTrack("path/to/track.aac")
>>> track2.language = "eng"

Create a new :class:`~pymkv.MKVTrack` from an MKV file. This example will take a specific track from an MKV and also
prevent any global tags from being included if the :class:`~pymkv.MKVTrack` is muxed into an :class:`~pymkv.MKVFile`.

>>> track3 = MKVTrack("path/to/MKV.mkv", track_id=1)
>>> track3.no_global_tags = True

Now all these tracks can be added to an :class:`~pymkv.MKVFile` object and muxed together.

>>> from pymkv import MKVFile
>>> file = MKVFile()
>>> file.add_track(track1)
>>> file.add_track(track2)
>>> file.add_track(track3)
>>> file.mux("path/to/output.mkv")
"""

from __future__ import annotations

import os
import subprocess as sp
from os import devnull
from pathlib import Path

from pymkv.BCP47 import is_bcp47
from pymkv.ISO639_2 import is_iso639_2
from pymkv.TypeTrack import get_track_extension
from pymkv.utils import ensure_info, prepare_mkvtoolnix_path
from pymkv.Verifications import checking_file_path, get_file_info, verify_supported


class MKVTrack:
    """A class that represents a track for an :class:`~pymkv.MKVFile` object.
    :class:`~pymkv.MKVTrack` objects are video, audio, or subtitles. Tracks can be standalone files or a single track
    within an MKV file, both can be handled by pymkv. An :class:`~pymkv.MKVTrack` object can be added to an
    :class:`~pymkv.MKVFile` and will be included when the MKV is muxed.
    Parameters
    ----------
    file_path : str
        Path to the track file. This can also be an MKV where the `track_id` is the track represented in the MKV.
    track_id : int, optional
        The id of the track to be used from the file. `track_id` only needs to be set when importing a track from
        an MKV. In this case, you can specify `track_id` to indicate which track from the MKV should be used. If not
        set, it will import the first track. Track 0 is imported by default because mkvmerge sees standalone
        track files as having one track with track_id set as 0.
    track_name : str, optional
        The name that will be given to the track when muxed into a file.
    language : str, optional
        The language of the track. It must be an ISO639-2 language code.
    language_ietf : str, optional
        The language of the track. It must be a BCP47 language code. Has priority over 'language'.
    default_track : bool, optional
        Determines if the track should be the default track of its type when muxed into an MKV file.
    forced_track : bool, optional
        Determines if the track should be a forced track when muxed into an MKV file.
    mkvmerge_path : str, list, os.PathLike, optional
        The path where pymkv looks for the mkvmerge executable. pymkv relies on the mkvmerge executable to parse
        files. By default, it is assumed mkvmerge is in your shell's $PATH variable. If it is not, you need to set
        *mkvmerge_path* to the executable location.
    mkvextract_path : str, list, os.PathLike, optional
        The path where pymkv looks for the mkvextract executable. pymkv relies on the mkvextract executable to extract
        files. By default, it is assumed mkvextract is in your shell's $PATH variable. If it is not, you need to set
        *mkvextract_path* to the executable location.
    Attributes
    ----------
    mkvmerge_path : list
        The path of the mkvmerge executable.
    mkvextract_path : list
        The path of the mkvextract executable.
    track_name : str
        The name that will be given to the track when muxed into a file.
    default_track : bool
        Determines if the track should be the default track of its type when muxed into an MKV file.
    forced_track : bool
        Determines if the track should be a forced track when muxed into an MKV file.
    no_chapters : bool
        If chapters exist in the track file, don't include them when this :class:`~pymkv.MKVTrack` object is a track
        in an :class:`~pymkv.MKVFile` mux operation. This option has no effect on standalone track files, only tracks
        that are already part of an MKV file.
    no_global_tags : bool
        If global tags exist in the track file, don't include them when this :class:`~pymkv.MKVTrack` object is a track
        in an :class:`~pymkv.MKVFile` mux operation. This option has no effect on standalone track files, only tracks
        that are already part of an MKV file.
    no_track_tags : bool
        If track tags exist in the specified track within the track file, don't include them when this
        :class:`~pymkv.MKVTrack` object is a track in an :class:`~pymkv.MKVFile` mux operation. This option has no
        effect on standalone track files, only tracks that are already part of an MKV file.
    no_attachments : bool
        If attachments exist in the track file, don't include them when this :class:`~pymkv.MKVTrack` object is a track
        in an :class:`~pymkv.MKVFile` mux operation. This option has no effect on standalone track files, only tracks
        that are already part of an MKV file.
    """

    def __init__(  # noqa: PLR0913
        self,
        file_path: str,
        track_id: int | None = 0,
        track_name: str | None = None,
        language: str | None = None,
        language_ietf: str | None = None,
        default_track: bool | None = False,
        forced_track: bool | None = False,
        flag_commentary: bool | None = False,
        flag_hearing_impaired: bool | None = False,
        flag_visual_impaired: bool | None = False,
        flag_original: bool | None = False,
        mkvmerge_path: str | list | tuple[str, ...] | os.PathLike | None = "mkvmerge",
        mkvextract_path: str | list | tuple[str, ...] | os.PathLike | None = "mkvextract",
        sync: int | None = None,
        existing_info: dict | None = None,
    ) -> None:
        # track info
        self._track_codec = None
        self._track_type = None

        # base
        self.mkvmerge_path = prepare_mkvtoolnix_path(mkvmerge_path)
        self._info_json: dict = existing_info
        self._file_path = None
        self.file_path = file_path
        self._track_id = None
        self.track_id = track_id
        self._file_id = 0
        self._pts = 0

        # flags
        self.track_name = track_name
        self._language = None
        self.language = language
        self._sync = None
        self.sync = sync
        self._language_ietf = None
        self.language_ietf = language_ietf
        self._tags = None
        self.default_track = default_track
        self.forced_track = forced_track
        self.flag_commentary = flag_commentary
        self.flag_hearing_impaired = flag_hearing_impaired
        self.flag_visual_impaired = flag_visual_impaired
        self.flag_original = flag_original

        # exclusions
        self.no_chapters = False
        self.no_global_tags = False
        self.no_track_tags = False
        self.no_attachments = False

        # mkvextract
        self.mkvextract_path = prepare_mkvtoolnix_path(mkvextract_path)
        self.extension = get_track_extension(self)

    def __repr__(self) -> str:
        """
        Return a string representation of the MKVTrack object.

        Returns:
            str: A string representation of the object's dictionary.
        """
        return repr(self.__dict__)

    @property
    def file_path(self) -> str:
        """
        Get the path to the track or MKV file containing the desired track.

        Returns:
            str: The file path.

        Raises:
            ValueError: If `file_path` is not a supported file type.
        """
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: str) -> None:
        """
        Set the file path for the track.

        This method checks if the provided file path is valid and supported by mkvmerge.
        If the file is valid, it sets the file path and resets the track_id to 0.

        Args:
            file_path (str): The path to the file containing the track.

        Raises:
            ValueError: If the file is not a valid Matroska file or is not supported.
        """
        file_path = checking_file_path(file_path)
        if not verify_supported(file_path, mkvmerge_path=self.mkvmerge_path):
            msg = f"The file '{file_path}' is not a valid Matroska file or is not supported."
            raise ValueError(msg)
        self._file_path = file_path
        self.track_id = 0

    @property
    def file_id(self) -> int:
        """
        Get the ID of the file the track belongs to.

        The file ID represents which file the current track is associated with. This is particularly useful
        when handling multiple files.

        Returns:
            int: The file ID.

        Raises:
            IndexError: If the passed in index is out of range of the file's tracks.
        """
        return self._file_id

    @file_id.setter
    def file_id(self, file_id: int) -> None:
        """
        Set the ID of the file the track belongs to.

        Args:
            file_id (int): The file ID to set.

        Raises:
            ValueError: If file_id is not an integer.
        """
        if isinstance(file_id, int):
            self._file_id = file_id
        else:
            msg = "file_id must be an integer"
            raise ValueError(msg)  # noqa: TRY004

    @property
    def track_id(self) -> int:
        """
        Get the ID of the track within the file.

        Returns:
            int: The track ID.

        Raises:
            IndexError: If the passed in index is out of range of the file's tracks.
        """
        return self._track_id

    @track_id.setter
    @ensure_info(
        "_info_json",
        get_file_info,
        ["file_path", "mkvmerge_path"],
        check_path=False,
    )
    def track_id(self, track_id: int) -> None:
        """
        Set the ID of the track within the file.

        This method checks that the ID passed in exists in the file. It then looks at the new track
        and sets the codec and track type. Should be left at 0 unless extracting a specific track from an MKV.

        Args:
            track_id (int): The track ID to set.

        Raises:
            IndexError: If the passed in index is out of range of the file's tracks.
        """
        if not 0 <= track_id < len(self._info_json["tracks"]):
            msg = "track index out of range"
            raise IndexError(msg)
        self._track_id = track_id
        try:
            self._pts = self._info_json["tracks"][track_id]["start_pts"]
        except KeyError:
            self._pts = 0
        self._track_codec = self._info_json["tracks"][track_id]["codec"]
        self._track_type = self._info_json["tracks"][track_id]["type"]

    @property
    def language(self) -> str:
        """
        Get the language of the track.

        Returns:
            str: The language of the track.

        Raises:
            ValueError: If the passed in language is not an ISO 639-2 language code.
        """
        return self._language

    @language.setter
    def language(self, language: str) -> None:
        """
        Set the language of the MKVTrack.

        Args:
            language (str): The language to be set for the MKVTrack.

        Raises:
            ValueError: If the provided language is not a valid ISO639-2 language code.
        """
        if language is None or is_iso639_2(language):
            self._language = language
        else:
            msg = "not an ISO639-2 language code"
            raise ValueError(msg)

    @property
    def pts(self) -> int:
        """
        Get the Presentation Timestamp (PTS) of the track.

        The PTS in multimedia files indicates the exact time when a frame or audio sample
        should be presented to the user, ensuring accurate synchronization between audio and video streams.

        Returns:
            int: The PTS value.
        """
        return self._pts

    @property
    def sync(self) -> int:
        """
        Get the synchronization offset for the track.

        This property represents the synchronization offset for the track.
        Positive values delay the track, while negative values advance it.

        Returns:
            int: The current synchronization offset in milliseconds.

        Note:
            Setting this property allows you to adjust the track timing:
            - Positive values delay the track (shift it later in time)
            - Negative values advance the track (shift it earlier in time)

        Example:
            track.sync = 1000  # Delay the track by 1 second
            track.sync = -500  # Advance the track by 0.5 seconds
        """
        return self._sync

    @sync.setter
    def sync(self, sync: int) -> None:
        """
        Set the synchronization offset for the track.

        Args:
            sync (int): The synchronization offset in milliseconds.
        """
        self._sync = sync

    @property
    def language_ietf(self) -> str:
        """
        Get the language of the track with BCP47 format.

        Returns:
            str: The language of the track in BCP47 format.

        Raises:
            ValueError: If the passed in language is not a BCP47 language code.
        """
        return self._language_ietf

    @language_ietf.setter
    def language_ietf(self, language_ietf: str) -> None:
        """
        Set the language of the track with BCP47 format.

        Args:
            language_ietf (str): The language to set in BCP47 format.

        Raises:
            ValueError: If the passed in language is not a BCP47 language code.
        """
        if language_ietf is None or is_bcp47(language_ietf):
            self._language_ietf = language_ietf
        else:
            msg = "not a BCP47 language code"
            raise ValueError(msg)

    @property
    def tags(self) -> str:
        """
        Get the tags file to include with the track.

        Returns:
            str: The path to the tags file.

        Raises:
            FileNotFoundError: If the passed in file does not exist or is not a file.
            TypeError: If the passed in file is not of type str.
        """
        return self._tags

    @tags.setter
    def tags(self, file_path: str) -> None:
        """
        Set the tags file for the track.

        Args:
            file_path (str): The path to the tags file.

        Raises:
            TypeError: If the file_path is not a string.
            FileNotFoundError: If the file does not exist or is not a file.
        """
        if not isinstance(file_path, str):
            msg = f'"{file_path}" is not of type str'
            raise TypeError(msg)
        file_path = Path(file_path).expanduser()
        if not file_path.is_file():
            msg = f'"{file_path}" does not exist'
            raise FileNotFoundError(msg)
        self._tags = str(file_path)

    @property
    def track_codec(self) -> str:
        """
        Get the codec of the track.

        Returns:
            str: The codec of the track, such as h264 or AAC.
        """
        return self._track_codec

    @property
    def track_type(self) -> str:
        """
        Get the type of the track.

        Returns:
            str: The type of track, such as video or audio.
        """
        return self._track_type

    def extract(self, output_path: str | os.PathLike | None = None, silent: bool | None = False) -> str:
        """
        Extract the track as a file.

        Args:
            output_path (str | os.PathLike | None, optional): The path to be used as the output file
            in the mkvextract command.
            silent (bool | None, optional): By default the mkvmerge output will be shown unless silent is True.

        Returns:
            str: The path of the extracted file.
        """
        extract_info_file = f"_[{self.track_id}]"
        if self.language:
            extract_info_file += f"_{self.language}"
        if self.extension:
            extract_info_file += f".{self.extension}"
        if (not self.language and not self.expansion) and self.track_name:
            extract_info_file += f"_{self.track_name}"
        if output_path is None:
            output_path = f"{self.file_path}{extract_info_file}"
        else:
            file = Path(self.file_path)
            output_path = Path(output_path, f"{file.name}{extract_info_file}")
        output_path = str(Path(output_path).expanduser())
        command = [*self.mkvextract_path, "tracks", f"{self.file_path}", f"{self.track_id}:{output_path}"]
        if silent:
            sp.run(command, stdout=open(devnull, "wb"), check=True)  # noqa: S603, PTH123, SIM115
        else:
            sp.run(command, check=True, capture_output=True)  # noqa: S603
        return output_path
