""":class:`~pymkv.MKVFile` is the core class of pymkv. It is used to import, create, modify, and mux MKV files.

Examples
--------
Below are some basic examples of how the :class:`~pymkv.MKVFile` objects can be used.

Create and mux a new MKV. This example takes an standalone video and audio track and combines them into an MKV file.

>>> from pymkv import MKVFile
>>> mkv = MKVFile()
>>> mkv.add_track('/path/to/track.h264')
>>> mkv.add_track(MKVTrack('/path/to/another/track.aac'))
>>> mkv.mux('/path/to/output.mkv')

Generate the mkvmerge command to mux an MKV. This is example is identical to the first example except the command is
only generated, not executed.

>>> mkv = MKVFile()
>>> mkv.add_track('/path/to/track.h264')
>>> mkv.add_track(MKVTrack('/path/to/another/track.aac'))
>>> mkv.command('/path/to/output.mkv')

Import an existing MKV and remove a track. This example will import an MKV that already exists on your filesystem,
remove a track and allow you to mux that change into a new file.

>>> mkv = MKVFile('/path/to/file.mkv')
>>> mkv.remove_track(0)
>>> mkv.mux('/path/to/output.mkv')

Combine two MKVs. This example takes two existing MKVs and combines their tracks into a single MKV file.

>>> mkv1 = MKVFile('/path/to/file1.mkv')
>>> mkv2 = MKVFile('/path/to/file2.mkv')
>>> mkv1.add_file(mkv2)
>>> mkv1.mux('/path/to/output.mkv')
"""

from __future__ import annotations

import logging
import os
import subprocess as sp
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, TypeVar, cast

import bitmath

from pymkv.ISO639_2 import is_iso639_2
from pymkv.MKVAttachment import MKVAttachment
from pymkv.MKVTrack import MKVTrack
from pymkv.Timestamp import Timestamp
from pymkv.utils import prepare_mkvtoolnix_path
from pymkv.Verifications import (
    checking_file_path,
    get_file_info,
    verify_mkvmerge,
    verify_supported,
)

T = TypeVar("T")


class MKVFile:
    """
    A class that represents an MKV file.

    The :class:`~pymkv.MKVFile` class can either import a pre-existing MKV file or create a new one. After an
    :class:`~pymkv.MKVFile` object has been instantiated, :class:`~pymkv.MKVTrack` objects or other
    :class:`~pymkv.MKVFile` objects can be added using :meth:`~pymkv.MKVFile.add_track` and
    :meth:`~pymkv.MKVFile.add_file` respectively.

    Tracks are always added in the same order that they exist in a file or are added in. They can be reordered
    using :meth:`~pymkv.MKVFile.move_track_front`, :meth:`~pymkv.MKVFile.move_track_end`,
    :meth:`~pymkv.MKVFile.move_track_forward`, :meth:`~pymkv.MKVFile.move_track_backward`,
    or :meth:`~pymkv.MKVFile.swap_tracks`.

    After an :class:`~pymkv.MKVFile` has been created, an mkvmerge command can be generated using
    :meth:`~pymkv.MKVFile.command` or the file can be muxed using :meth:`~pymkv.MKVFile.mux`.

    Parameters
    ----------
    file_path : str, optional
        Path to a pre-existing MKV file. The file will be imported into the new :class:`~pymkv.MKVFile` object.
    title : str, optional
        The internal title given to the :class:`~pymkv.MKVFile`. If `title` is not specified, the title of the
        pre-existing file will be used if it exists.
    mkvmerge_path : str, optional
        The path where pymkv looks for the mkvmerge executable. pymkv relies on the mkvmerge executable to parse
        files. By default, it is assumed mkvmerge is in your shell's $PATH variable. If it is not, you need to set
        *mkvmerge_path* to the executable location.

    Raises
    ------
    FileNotFoundError
        Raised if the path to mkvmerge could not be verified.
    """

    def __init__(
        self,
        file_path: str | os.PathLike | None = None,
        title: str | None = None,
        mkvmerge_path: str | os.PathLike | Iterable[str] = "mkvmerge",
    ) -> None:
        self.mkvmerge_path: tuple[str, ...] = prepare_mkvtoolnix_path(mkvmerge_path)
        self.title = title
        self._chapters_file: str | None = None
        self._chapter_language: str | None = None
        self._global_tags_file: str | None = None
        self._link_to_previous_file: str | None = None
        self._link_to_next_file: str | None = None
        self.tracks: list[MKVTrack] = []
        self.attachments: list[MKVAttachment] = []
        self._number_file = 0
        self._info_json: dict[str, Any] | None = None
        self._global_tag_entries = 0

        # exclusions
        self.no_track_statistics_tags = False

        if not verify_mkvmerge(mkvmerge_path=self.mkvmerge_path):
            msg = "mkvmerge is not at the specified path, add it there or changed mkvmerge_path property"
            raise FileNotFoundError(msg)

        if file_path is not None:
            if not verify_supported(file_path, mkvmerge_path=self.mkvmerge_path):
                msg = f"The file '{file_path}' is not a valid Matroska file or is not supported."
                raise ValueError(msg)
            # add file title
            file_path = checking_file_path(file_path)
            try:
                info_json = get_file_info(
                    file_path,
                    self.mkvmerge_path,
                    check_path=False,
                )
                self._info_json = info_json
            except sp.CalledProcessError as e:
                error_output = e.output.decode()
                raise sp.CalledProcessError(
                    e.returncode,
                    e.cmd,
                    output=error_output,
                ) from e
            if self.title is None and "title" in info_json["container"]["properties"]:
                self.title = info_json["container"]["properties"]["title"]

            self._global_tag_entries = sum(t["num_entries"] for t in info_json.get("global_tags", []))

            # dictionary associating track_id to the number of tag entries:
            track_tag_entries: dict[int, int] = {
                t["track_id"]: t["num_entries"] for t in self._info_json.get("track_tags", [])
            }

            # add tracks with info
            for track in info_json["tracks"]:
                track_id = track["id"]
                new_track = MKVTrack(
                    file_path,
                    track_id=track_id,
                    mkvmerge_path=self.mkvmerge_path,
                    existing_info=self._info_json,
                    tag_entries=track_tag_entries.get(track_id, 0),
                )
                if "track_name" in track["properties"]:
                    new_track.track_name = track["properties"]["track_name"]
                if "language" in track["properties"]:
                    new_track.language = track["properties"]["language"]
                if "language_ietf" in track["properties"]:
                    new_track.language_ietf = track["properties"]["language_ietf"]
                if "default_track" in track["properties"]:
                    new_track.default_track = track["properties"]["default_track"]
                if "forced_track" in track["properties"]:
                    new_track.forced_track = track["properties"]["forced_track"]
                if "flag_commentary" in track["properties"]:
                    new_track.flag_commentary = track["properties"]["flag_commentary"]
                if "flag_hearing_impaired" in track["properties"]:
                    new_track.flag_hearing_impaired = track["properties"]["flag_hearing_impaired"]
                if "flag_visual_impaired" in track["properties"]:
                    new_track.flag_visual_impaired = track["properties"]["flag_visual_impaired"]
                if "flag_original" in track["properties"]:
                    new_track.flag_original = track["properties"]["flag_original"]

                self.add_track(new_track, new_file=False)

        # split options
        self._split_options: list[str] = []

    def __repr__(self) -> str:
        """
        Return a string representation of the MKVFile object.

        Returns:
            str: A string representation of the object's attributes.
        """
        return repr(self.__dict__)

    @property
    def chapter_language(self) -> str | None:
        """
        Get the language code of the chapters in the MKVFile object.

        Returns:
            str: The ISO 639-2 language code of the chapters.

        Raises:
            ValueError: If the stored language code is not a valid ISO 639-2 language code.
        """
        return self._chapter_language

    @chapter_language.setter
    def chapter_language(self, language: str | None) -> None:
        """
        Set the language code of the chapters in the MKVFile object.

        Args:
            language (str): The language code for the chapters. Must be a valid ISO 639-2 language code.

        Raises:
            ValueError: If the provided language code is not a valid ISO 639-2 language code.
        """
        if language is not None and not is_iso639_2(language):
            msg = "The provided language code is not a valid ISO 639-2 language code."
            raise ValueError(msg)
        self._chapter_language = language

    @property
    def global_tag_entries(self) -> int:
        """
        Gets the number of global tag entries in the MKVFile object.

        Returns:
            int: The number of entries.
        """
        return self._global_tag_entries

    def command(  # noqa: PLR0912,PLR0915
        self,
        output_path: str,
        subprocess: bool = False,
    ) -> str | list:
        """
        Generates an mkvmerge command based on the configured :class:`~pymkv.MKVFile`.

        Parameters
        ----------
        output_path : str
            The path to be used as the output file in the mkvmerge command.
        subprocess : bool
            Will return the command as a list so it can be used easily with the :mod:`subprocess` module.

        Returns
        -------
        str, list of str
            The full command to mux the :class:`~pymkv.MKVFile` as a string containing spaces. Will be returned as a
            list of strings with no spaces if `subprocess` is True.
        """
        output_path = str(Path(output_path).expanduser())
        command = [*self.mkvmerge_path, "-o", output_path]
        if self.title is not None:
            command.extend(["--title", self.title])
        if self.no_track_statistics_tags:
            # Do not write tags with track statistics.
            command.append("--disable-track-statistics-tags")
        track_order = []
        for track in self.tracks:
            # for track_order
            track_order.append(f"{track.file_id}:{track.track_id}")
            # flags
            if track.track_name is not None:
                command.extend(
                    ["--track-name", f"{track.track_id!s}:{track.track_name}"],
                )
            if track.language_ietf is not None:
                command.extend(
                    ["--language", f"{track.track_id!s}:{track.language_ietf}"],
                )
            elif track.language is not None:
                command.extend(["--language", f"{track.track_id!s}:{track.language}"])
            if track.sync is not None:
                command.extend(["--sync", f"{track.track_id!s}:{track.sync}"])
            if track.tags is not None:
                command.extend(["--tags", f"{track.track_id!s}:{track.tags}"])
            if track.default_track:
                command.extend(["--default-track", f"{track.track_id!s}:1"])
            else:
                command.extend(["--default-track", f"{track.track_id!s}:0"])
            if track.forced_track:
                command.extend(["--forced-track", f"{track.track_id!s}:1"])
            else:
                command.extend(["--forced-track", f"{track.track_id!s}:0"])
            if track.flag_hearing_impaired:
                command.extend(["--hearing-impaired-flag", f"{track.track_id!s}:1"])
            else:
                command.extend(["--hearing-impaired-flag", f"{track.track_id!s}:0"])
            if track.flag_visual_impaired:
                command.extend(["--visual-impaired-flag", f"{track.track_id!s}:1"])
            else:
                command.extend(["--visual-impaired-flag", f"{track.track_id!s}:0"])
            if track.flag_original:
                command.extend(["--original-flag", f"{track.track_id!s}:1"])
            else:
                command.extend(["--original-flag", f"{track.track_id!s}:0"])
            if track.flag_commentary:
                command.extend(["--commentary-flag", f"{track.track_id!s}:1"])
            else:
                command.extend(["--commentary-flag", f"{track.track_id!s}:0"])
            if track.compression is not None:
                command.extend(
                    ["--compression", f"{track.track_id!s}:{'zlib' if track.compression else 'none'}"],
                )

            # remove extra tracks
            if track.track_type == "audio":
                command.append("-D")
                command.extend(["-a", str(track.track_id), "-S"])
            elif track.track_type == "subtitles":
                command.extend(("-D", "-A", "-s", str(track.track_id)))
            elif track.track_type == "video":
                command.extend(["-d", str(track.track_id), "-A", "-S"])
            else:
                command.extend(("-D", "-A", "-S"))
            # exclusions
            if track.no_chapters:
                command.append("--no-chapters")
            if track.no_global_tags:
                command.append("--no-global-tags")
            if track.no_track_tags:
                command.append("--no-track-tags")
            if track.no_attachments:
                command.append("--no-attachments")

            command.append(track.file_path)

        # add attachments
        for attachment in self.attachments:
            # info
            if attachment.name is not None:
                command.extend(["--attachment-name", attachment.name])
            if attachment.description is not None:
                command.extend(["--attachment-description", attachment.description])
            if attachment.mime_type is not None:
                command.extend(["--attachment-mime-type", attachment.mime_type])

            # add path
            if not attachment.attach_once:
                command.extend(["--attach-file", attachment.file_path])
            else:
                command.extend(["--attach-file-once", attachment.file_path])

        # chapters
        if self._chapter_language is not None:
            command.extend(["--chapter-language", self._chapter_language])
        if self._chapters_file is not None:
            command.extend(["--chapters", self._chapters_file])

        # global tags
        if self._global_tags_file is not None:
            command.extend(["--global-tags", self._global_tags_file])

        # linking
        if self._link_to_previous_file is not None:
            command.extend(["--link-to-previous", f"={self._link_to_previous_file}"])
        if self._link_to_next_file is not None:
            command.extend(["--link-to-next", f"={self._link_to_next_file}"])

        # tracks order
        if track_order:
            command.extend(["--track-order", ",".join(track_order)])

        # split options
        command.extend(self._split_options)

        return command if subprocess else " ".join(command)

    def mux(self, output_path: str | os.PathLike, silent: bool = False, ignore_warning: bool = False) -> int:
        """
        Mixes the specified :class:`~pymkv.MKVFile`.

        Parameters
        ----------
        output_path : str
            The path to be used as the output file in the mkvmerge command.
        silent : bool, optional
            By default the mkvmerge output will be shown unless silent is True.
        ignore_warning : bool, optional
            If set to True, the muxing process will ignore any warnings (exit code 1) from mkvmerge.
        Returns
        -------
        int of Any
            return code

        Raises
        ------
        ValueError
            Raised if the external mkvmerge command fails with a non-zero exit status
            (except for warnings when ignore_warning is True). This includes scenarios
            such as invalid command arguments, errors in processing the :class:`~pymkv.MKVFile`,
            or issues with output file writing. The error message provides details about
            the failure based on the output of the command.
        """
        output_path = str(Path(output_path).expanduser())
        args = self.command(output_path, subprocess=True)

        stdout = sp.DEVNULL if silent else None
        stderr = sp.PIPE

        proc = sp.Popen(args, stdout=stdout, stderr=stderr)  # noqa: S603
        _, err = proc.communicate()

        if proc.returncode != 0:
            # Handle warnings (exit code 1) if ignore_warning is True
            if proc.returncode == 1 and ignore_warning:
                logging.warning("Process completed with warnings, but ignored as per the setting.")
                return proc.returncode

            # For other non-zero exit codes, raise an exception
            error_message = f"Command failed with non-zero exit status {proc.returncode}"
            if err:
                error_details = err.decode()
                error_message += f"\nError Output:\n{error_details}"
                logging.error(error_details)
            logging.error(
                "Non-zero exit status when running %s (%s)",
                args,
                proc.returncode,
            )
            raise ValueError(error_message)

        return proc.returncode

    def add_file(self, file: MKVFile | str | os.PathLike) -> None:
        """
        Add an MKV file into the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        file : str, :class:`~pymkv.MKVFile`, os.PathLike
            The file to be combined with the :class:`~pymkv.MKVFile` object.

        Raises
        ------
        TypeError
            Raised if if `file` is not a string-like path to an MKV file or an :class:`~pymkv.MKVFile` object.
        """
        if isinstance(file, (str, os.PathLike)):
            self._number_file += 1
            new_tracks = MKVFile(file).tracks
            for track in new_tracks:
                track.file_id = self._number_file
            self.tracks = self.tracks + new_tracks
        elif isinstance(file, MKVFile):
            self._number_file += 1
            for track in file.tracks:
                track.file_id = self._number_file
            self.tracks = self.tracks + file.tracks
        else:
            msg = "track is not str or MKVFile"
            raise TypeError(msg)
        self.order_tracks_by_file_id()

    def add_track(self, track: str | MKVTrack, new_file: bool = True) -> None:
        """
        Add a track to the :class:`~pymkv.MKVFile`.

        Parameters
        ----------
        track : str, :class:`~pymkv.MKVTrack`
            The track to be added to the :class:`~pymkv.MKVFile` object.
        new_file : bool, optional
            If set to True, the file_id for the added track is not incremented. This can be used to preserve
            original track numbering from a source file.

        Raises
        ------
        TypeError
            Raised if `track` is not a string-like path to a track file or an :class:`~pymkv.MKVTrack`.
        """
        if isinstance(track, str):
            new_track = MKVTrack(
                track,
                mkvmerge_path=self.mkvmerge_path,
                existing_info=self._info_json,
            )
            self._extracted_from_add_track(new_track, new_file)
        elif isinstance(track, MKVTrack):
            self._extracted_from_add_track(track, new_file)
        else:
            msg = "track is not str or MKVTrack"
            raise TypeError(msg)
        self.order_tracks_by_file_id()

    def _extracted_from_add_track(
        self,
        track: MKVTrack,
        new_file: bool = False,
    ) -> None:
        if new_file:
            self._number_file += 1
        track.file_id = self._number_file
        self.tracks.append(track)

    def add_attachment(self, attachment: str | MKVAttachment) -> None:
        """
        Add an attachment to the :class:`~pymkv.MKVFile`.

        Parameters
        ----------
        attachment : str, :class:`~pymkv.MKVAttachment`
            The attachment to be added to the :class:`~pymkv.MKVFile` object.

        Raises
        ------
        TypeError
            Raised if if `attachment` is not a string-like path to an attachment file
            or an :class:`~pymkv.MKVAttachment`.
        """
        if isinstance(attachment, str):
            self.attachments.append(MKVAttachment(attachment))
        elif isinstance(attachment, MKVAttachment):
            self.attachments.append(attachment)
        else:
            msg = "Attachment is not str of MKVAttachment"
            raise TypeError(msg)

    def get_track(self, track_num: int | None = None) -> MKVTrack | list[MKVTrack]:
        """
        Get a :class:`~pymkv.MKVTrack` from the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        track_num : int, optional
            Index of track to retrieve. Will return list of :class:`~pymkv.MKVTrack` objects if argument is not
            provided.

        Returns
        -------
        :class:`~pymkv.MKVTrack`, list of :class:`~pymkv.MKVTrack`
            A list of all :class:`~pymkv.MKVTrack` objects in an :class:`~pymkv.MKVFile`. Returns a specific
            :class:`~pymkv.MKVTrack` if `track_num` is specified.
        """
        return self.tracks if track_num is None else self.tracks[track_num]

    def move_track_front(self, track_num: int) -> None:
        """
        Set a track as the first in the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        track_num : int
            The track number of the track to move to the front.

        Raises
        ------
        IndexError
            Raised if `track_num` is is out of range of the track list.
        """
        if not 0 <= track_num < len(self.tracks):
            msg = "track index out of range"
            raise IndexError(msg)
        self.tracks.insert(0, self.tracks.pop(track_num))
        self.order_tracks_by_file_id()

    def move_track_end(self, track_num: int) -> None:
        """
        Set as track as the last in the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        track_num : int
            The track number of the track to move to the back.

        Raises
        ------
        IndexError
            Raised if `track_num` is is out of range of the track list.
        """
        if not 0 <= track_num < len(self.tracks):
            msg = "track index out of range"
            raise IndexError(msg)
        self.tracks.append(self.tracks.pop(track_num))
        self.order_tracks_by_file_id()

    def move_track_forward(self, track_num: int) -> None:
        """
        Move a track forward in the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        track_num : int
            The track number of the track to move forward.

        Raises
        ------
        IndexError
            Raised if `track_num` is is out of range of the track list.
        """
        if not 0 <= track_num < len(self.tracks) - 1:
            msg = "Track index out of range"
            raise IndexError(msg)
        self.tracks[track_num], self.tracks[track_num + 1] = (
            self.tracks[track_num + 1],
            self.tracks[track_num],
        )
        self.order_tracks_by_file_id()

    def move_track_backward(self, track_num: int) -> None:
        """
        Move a track backward in the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        track_num : int
            The track number of the track to move backward.

        Raises
        ------
        IndexError
            Raised if `track_num` is is out of range of the track list.
        """
        if not 0 < track_num < len(self.tracks):
            msg = "Track index out of range"
            raise IndexError(msg)
        self.tracks[track_num], self.tracks[track_num - 1] = (
            self.tracks[track_num - 1],
            self.tracks[track_num],
        )
        self.order_tracks_by_file_id()

    def swap_tracks(self, track_num_1: int, track_num_2: int) -> None:
        """
        Swap the position of two tracks in the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        track_num_1 : int
            The track number of one track to swap.
        track_num_2 : int
            The track number of the other track to swap

        Raises
        ------
        IndexError
            Raised if `track_num_1` or `track_num_2` are out of range of the track list.
        """
        if not 0 <= track_num_1 < len(self.tracks) or not 0 <= track_num_2 < len(
            self.tracks,
        ):
            msg = "Track index out of range"
            raise IndexError(msg)
        self.tracks[track_num_1], self.tracks[track_num_2] = (
            self.tracks[track_num_2],
            self.tracks[track_num_1],
        )
        self.order_tracks_by_file_id()

    def replace_track(self, track_num: int, track: MKVTrack) -> None:
        """
        Replace a track with another track in the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        track_num : int
            The track number of the track to replace.
        track : :class:`~pymkv.MKVTrack`
            The :class:`~pymkv.MKVTrack` to be replaced into the file.

        Raises
        ------
        IndexError
            Raised if `track_num` is is out of range of the track list.
        """
        if not 0 <= track_num < len(self.tracks):
            msg = "track index out of range"
            raise IndexError(msg)
        self.tracks[track_num] = track
        self.order_tracks_by_file_id()

    def remove_track(self, track_num: int) -> None:
        """
        Remove a track from the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        track_num : int
            The track number of the track to remove.

        Raises
        ------
        IndexError
            Raised if `track_num` is is out of range of the track list.
        """
        if not 0 <= track_num < len(self.tracks):
            msg = "track index out of range"
            raise IndexError(msg)
        del self.tracks[track_num]
        self.order_tracks_by_file_id()

    def split_none(self) -> None:
        """Remove all splitting options."""
        self._split_options = []

    def split_size(
        self,
        size: bitmath.Bitmath | int,
        link: bool | None = False,
    ) -> None:
        """
        Split the output file into parts by size.

        Parameters
        ----------
        size : :obj:`bitmath`, int
            The size of each split file. Takes either a :obj:`bitmath` size object or an integer representing the
            number of bytes.
        link : bool, optional
            Determines if the split files should be linked together after splitting.

        Raises
        ------
        TypeError
            Raised if if `size` is not a bitmath object or an integer.
        """
        if getattr(size, "__module__", None) == bitmath.__name__:
            size = cast("bitmath.Bitmath", size).bytes
        elif not isinstance(size, int):
            msg = "size is not a bitmath object or integer"
            raise TypeError(msg)
        self._split_options = ["--split", f"size:{size}"]
        if link:
            self._split_options.append("--link")

    def split_duration(self, duration: str | int, link: bool | None = False) -> None:
        """
        Split the output file into parts by duration.

        Parameters
        ----------
        duration : str, int
            The duration of each split file. Takes either a str formatted to HH:MM:SS.nnnnnnnnn or an integer
            representing the number of seconds. The duration string requires formatting of at least M:S.
        link : bool, optional
            Determines if the split files should be linked together after splitting.
        """
        self._split_options = ["--split", f"duration:{Timestamp(duration)!s}"]
        if link:
            self._split_options.append("--link")

    def split_timestamps(
        self,
        *timestamps: Iterable[str | int],
        link: bool | None = False,
    ) -> None:
        """
        Split the output file into parts by timestamps.

        Parameters
        ----------
        *timestamps : Iterable[str | int]
            The timestamps to split the file by. Can be passed as any combination of strs and ints, inside or outside
            an :obj:`Iterable` object. Any lists will be flattened. Timestamps must be ints, representing seconds,
            or strs in the form HH:MM:SS.nnnnnnnnn. The timestamp string requires formatting of at least M:S.
        link : bool, optional
            Determines if the split files should be linked together after splitting.

        Raises
        ------
        ValueError
            Raised if invalid or improperly formatted timestamps are passed in for `*timestamps`.
        """
        # check if in timestamps form
        ts_flat: list[str | int] = MKVFile.flatten(timestamps)
        if not ts_flat:
            msg = f'"{timestamps}" are not properly formatted timestamps'
            raise ValueError(msg)
        if None in ts_flat:
            msg = f'"{timestamps}" are not properly formatted timestamps'
            raise ValueError(msg)
        for ts_1, ts_2 in zip(ts_flat[:-1], ts_flat[1:], strict=False):
            if Timestamp(ts_1) >= Timestamp(ts_2):
                msg = f'"{timestamps}" are not properly formatted timestamps'
                raise ValueError(msg)

        # build ts_string from timestamps
        ts_string = "timestamps:"
        for ts in ts_flat:
            ts_string += f"{Timestamp(ts)!s},"
        self._split_options = ["--split", ts_string[:-1]]
        if link:
            self._split_options.append("--link")

    def split_frames(
        self,
        *frames: int | Iterable[int],
        link: bool | None = False,
    ) -> None:
        """
        Split the output file into parts by frames.

        Parameters
        ----------
        *frames : int, list, tuple
            The frames to split the file by. Can be passed as any combination of ints, inside or outside an
            :obj:`Iterable` object. Any lists will be flattened. Frames must be ints.
        link : bool, optional
            Determines if the split files should be linked together after splitting.

        Raises
        ------
        TypeError
            Raised if non-int frames are passed in for `*frames` or within the `*frames` iterable.
        ValueError
            Raised if improperly formatted frames are passed in for `*frames`.
        """
        # check if in frames form
        frames_flat: list[int] = MKVFile.flatten(frames)
        if not frames_flat:
            msg = f'"{frames}" are not properly formatted frames'
            raise ValueError(msg)
        for f in frames_flat:
            if not isinstance(f, int):
                msg = f'frame "{f}" not an int'
                raise TypeError(msg)
        for f_1, f_2 in zip(frames_flat[:-1], frames_flat[1:], strict=False):
            if f_1 >= f_2:
                msg = f'"{frames}" are not properly formatted frames'
                raise ValueError(msg)

        # build f_string from frames
        f_string = "frames:"
        for f in frames_flat:
            f_string += f"{f!s},"
        self._split_options = ["--split", f_string[:-1]]
        if link:
            self._split_options.append("--link")

    def split_timestamp_parts(
        self,
        timestamp_parts: Iterable[list[str] | tuple[str, ...]],
        link: bool | None = False,
    ) -> None:
        """
        Split the output in parts by time parts.

        Parameters
        ----------
        timestamp_parts : list, tuple
            An Iterable of timestamp sets. Each timestamp set should be an Iterable of an even number of timestamps
            or any number of timestamp pairs. The very first and last timestamps are permitted to be None. Timestamp
            sets containing 4 or more timestamps will output as one file containing the parts specified.
        link : bool, optional
            Determines if the split files should be linked together after splitting.

        Raises
        ------
        TypeError
            Raised if any of the timestamp sets are not a list or tuple.
        ValueError
            Raised if `timestamp_parts` contains improperly formatted parts.
        """
        ts_flat: list[str | int | Timestamp] = MKVFile.flatten(timestamp_parts)
        if not ts_flat:
            msg = f'"{timestamp_parts}" are not properly formatted parts'
            raise ValueError(msg)

        if None in ts_flat[1:-1]:
            msg = f'"{timestamp_parts}" are not properly formatted parts'
            raise ValueError(msg)

        for ts_1, ts_2 in zip(ts_flat[:-1], ts_flat[1:], strict=False):
            if None not in (ts_1, ts_2) and Timestamp(ts_1) >= Timestamp(ts_2):
                msg = f'"{timestamp_parts}" are not properly formatted parts'
                raise ValueError(msg)

        ts_string = "parts:"
        for ts_set in timestamp_parts:
            ts_set = MKVFile.flatten(ts_set)  # noqa: PLW2901
            if not isinstance(ts_set, (list, tuple)):
                msg = "set is not of type list or tuple"
                raise TypeError(msg)
            if len(ts_set) < 2 or len(ts_set) % 2 != 0:  # noqa: PLR2004
                msg = f'"{ts_set}" is not a properly formatted set'
                raise ValueError(msg)
            for index, ts in enumerate(ts_set):
                if index % 2 == 0 and index > 0:
                    ts_string += "+"
                if ts is not None:
                    ts_string += str(Timestamp(ts))
                ts_string += "-" if index % 2 == 0 else ","
        self._split_options = ["--split", ts_string[:-1]]
        if link:
            self._split_options.append("--link")

    def split_parts_frames(
        self,
        frame_parts: Iterable[int],
        link: bool | None = False,
    ) -> None:
        """
        Split the output in parts by frames.

        Parameters
        ----------
        frame_parts : list, tuple
            An Iterable of frame sets. Each frame set should be an :obj:`Iterable` object of an even number of frames
            or any
            number of frame pairs. The very first and last frames are permitted to be None. Frame sets containing four
            or more frames will output as one file containing the parts specified.
        link : bool, optional
            Determines if the split files should be linked together after splitting.

        Raises
        ------
        TypeError
            Raised if any of the frame sets are not a list or tuple.
        ValueError
            Raised if `frame_parts` contains improperly formatted parts.
        """
        f_flat: list[int] = MKVFile.flatten(frame_parts)
        if not f_flat:
            msg = f'"{frame_parts}" are not properly formatted parts'
            raise ValueError(msg)
        if None in f_flat[1:-1]:
            msg = f'"{frame_parts}" are not properly formatted parts'
            raise ValueError(msg)
        for f_1, f_2 in zip(f_flat[:-1], f_flat[1:], strict=False):
            if None not in (f_1, f_2) and f_1 >= f_2:
                msg = f'"{frame_parts}" are not properly formatted parts'
                raise ValueError(msg)
        f_string = "parts:"
        for fp in frame_parts:
            f_set = MKVFile.flatten(fp)
            if not isinstance(f_set, (list, tuple)):
                msg = "set is not of type list or tuple"
                raise TypeError(msg)
            if len(f_set) < 2 or len(f_set) % 2 != 0:  # noqa: PLR2004
                msg = f'"{f_set}" is not a properly formatted set'
                raise ValueError(msg)
            for index, f in enumerate(f_set):
                if not isinstance(f, int) and f is not None:
                    msg = f'frame "{f}" not an int'
                    raise TypeError(msg)
                if index % 2 == 0 and index > 0:
                    f_string += "+"
                if f is not None:
                    f_string += str(f)
                f_string += "-" if index % 2 == 0 else ","
        self._split_options = ["--split", f_string[:-1]]
        if link:
            self._split_options.append("--link")

    def split_chapters(
        self,
        *chapters: int | Iterable[int],
        link: bool = False,
    ) -> None:
        """
        Split the output file into parts by chapters.

        Parameters
        ----------
        *chapters : int, list, tuple
           The chapters to split the file by. Can be passed as any combination of ints, inside or outside an
           :obj:`Iterable` object. Any lists will be flattened. Chapters must be ints.
        link : bool, optional
            Determines if the split files should be linked together after splitting.

        Raises
        ------
        TypeError
            Raised if any chapters in `*chapters` are not of type int.
        ValueError
            Raised if `*chapters` contains improperly formatted chapters.
        """
        c_flat: list[int] = MKVFile.flatten(chapters)
        if not chapters:
            self._split_options = ["--split", "chapters:all"]
            return
        for c in c_flat:
            if not isinstance(c, int):
                msg = f'chapter "{c}" not an int'
                raise TypeError(msg)
            if c < 1:
                msg = f'"{chapters}" are not properly formatted chapters'
                raise ValueError(msg)
        for c_1, c_2 in zip(c_flat[:-1], c_flat[1:], strict=False):
            if c_1 >= c_2:
                msg = f'"{chapters}" are not properly formatted chapters'
                raise ValueError(msg)
        c_string = "chapters:"
        for c in c_flat:
            c_string += f"{c!s},"
        self._split_options = ["--split", c_string[:-1]]
        if link:
            self._split_options.append("--link")

    def link_to_previous(self, file_path: str) -> None:
        """
        Link the output file as the predecessor of the `file_path` file.

        Parameters
        ----------
        file_path : str
            Path of the file to be linked to.

        Raises
        ------
        TypeError
            Raised if `file_path` is not of type str.
        ValueError
            Raised if file at `file_path` cannot be verified as an MKV.
        """
        self._link_to_previous_file = checking_file_path(file_path)

    def link_to_next(self, file_path: str) -> None:
        """
        Link the output file as the successor of the `file_path` file.

        Parameters
        ----------
        file_path : str
            Path of the file to be linked to.

        Raises
        ------
        TypeError
            Raised if `file_path` is not of type str.
        ValueError
            Raised if file at `file_path` cannot be verified as an MKV.
        """
        self._link_to_next_file = checking_file_path(file_path)

    def link_to_none(self) -> None:
        """
        Remove all linking to previous and next files.

        This method clears any existing links to previous or next files,
        effectively removing the file linking options for the current MKVFile object.
        """
        self._link_to_previous_file = None
        self._link_to_next_file = None

    def chapters(self, file_path: str, language: str | None = None) -> None:
        """
        Add a chapters file to the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        file_path : str
            The chapters file to be added to the :class:`~pymkv.MKVFile` object.
        language : str, optional
            Must be an ISO639-2 language code. Only applied if no existing language information exists in chapters.

        Raises
        ------
        FileNotFoundError
            Raised if the file at `file_path` does not exist.
        TypeError
            Raised if `file_path` is not of type str.
        """
        self._chapters_file = checking_file_path(file_path)
        self.chapter_language = language

    def global_tags(self, file_path: str) -> None:
        """
        Add global tags to the :class:`~pymkv.MKVFile` object.

        Parameters
        ----------
        file_path : str
            The tags file to be added to the :class:`~pymkv.MKVFile` object.

        Raises
        ------
        FileNotFoundError
            Raised if the file at `file_path` does not exist.
        TypeError
            Raised if `file_path` is not of type str.
        """
        self._global_tags_file = checking_file_path(file_path)

    def track_tags(
        self,
        *track_ids: int | list | tuple,
        exclusive: bool | None = False,
    ) -> None:
        """
        Include or exclude tags from specific tracks.

        Parameters
        ----------
        *track_ids : int, list, tuple
            Track ids to have tags included or excluded from.
        exclusive : bool, optional
            Determines if the `track_ids` should have their tags kept or removed. `exclusive` is False by default and
            will remove tags from unspecified tracks.

        Raises
        ------
        IndexError
            Raised if any ids from `*track_ids` is is out of range of the track list.
        TypeError
            Raised if an ids from `*track_ids` are not of type int.
        ValueError
            Raised if `*track_ids` are improperly formatted.
        """
        ids_flat: list[int] = MKVFile.flatten(track_ids)
        if not track_ids:
            msg = f'"{track_ids}" are not properly formatted track ids'
            raise ValueError(msg)
        for tid in ids_flat:
            if not isinstance(tid, int):
                msg = f'track id "{tid}" not an int'
                raise TypeError(msg)
            if tid < 0 or tid >= len(self.tracks):
                msg = "track id out of range"
                raise IndexError(msg)
        for tid in ids_flat if exclusive else list(set(range(len(self.tracks))) - set(ids_flat)):
            self.tracks[tid].no_track_tags = True

    def no_chapters(self) -> None:
        """
        Ignore the existing chapters of all tracks in the :class:`~pymkv.MKVFile` object.

        This method sets the `no_chapters` attribute to True for all tracks in the MKVFile.
        """
        for track in self.tracks:
            track.no_chapters = True

    def no_global_tags(self) -> None:
        """
        Ignore the existing global tags of all tracks in the :class:`~pymkv.MKVFile` object.

        This method sets the `no_global_tags` attribute to True for all tracks in the MKVFile.
        """
        for track in self.tracks:
            track.no_global_tags = True

    def no_track_tags(self) -> None:
        """
        Ignore the existing track tags of all tracks in the :class:`~pymkv.MKVFile` object.

        This method sets the `no_track_tags` attribute to True for all tracks in the MKVFile.
        """
        for track in self.tracks:
            track.no_track_tags = True

    def no_attachments(self) -> None:
        """
        Ignore the existing attachments of all tracks in the :class:`~pymkv.MKVFile` object.

        This method sets the `no_attachments` attribute to True for all tracks in the MKVFile.
        """
        for track in self.tracks:
            track.no_attachments = True

    @staticmethod
    def flatten(item: T | Iterable[T | Iterable[T]]) -> list[T]:
        """
        Flatten a list or a tuple.

        Takes a list or a tuple that contains other lists or tuples and flattens into a non-nested list.

        Examples
        --------
        >>> tup = ((1, 2), (3, (4, 5)))
        >>> MKVFile.flatten(tup)
        [1, 2, 3, 4, 5]

        >>> tup = (["abc", "d"])
        >>> MKVFile.flatten(tup)
        ['abc', 'd']

        Parameters
        ----------
        item : list, tuple
            A list or a tuple object with nested lists or tuples to be flattened.

        Returns
        -------
        list
            A flattened version of `item`.
        """

        def _flatten(item: T | Iterable[T | Iterable[T]]) -> Iterable[T]:
            if isinstance(item, Sequence) and not isinstance(item, str):
                for subitem in item:
                    yield from _flatten(subitem)
            else:
                yield cast("T", item)

        return list(_flatten(item))

    def order_tracks_by_file_id(self) -> None:
        """
        Assigns file IDs to tracks based on their source files.

        Creates a mapping of unique file paths to numeric IDs,
        then assigns each track a file ID corresponding to its source file.
        Tracks from the same file will have the same file ID.

        This method modifies the file_id attribute of each track in self.tracks.
        """
        unique_file_dict: dict[str, int] = {}
        try:
            for track in self.tracks:
                if track.file_path not in unique_file_dict:
                    unique_file_dict[track.file_path] = len(unique_file_dict)

            for track in self.tracks:
                track.file_id = unique_file_dict[track.file_path]
        except KeyError as e:
            raise ValueError from e
