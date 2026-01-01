from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pymkv.MKVFile import MKVFile
    from pymkv.MKVTrack import MKVTrack

from .base import CommandGeneratorBase


class TrackOptions(CommandGeneratorBase):
    """Handles track-specific flags using declarative dispatch."""

    property_flags = {
        "track_name": ("--track-name", False),
        "language_ietf": ("--language", False),  # Handled via effective_language now
        "language": ("--language", False),  # Handled via effective_language now
        "tags": ("--tags", False),
        "default_track": ("--default-track", True),
        "forced_track": ("--forced-track", True),
        "flag_hearing_impaired": ("--hearing-impaired-flag", True),
        "flag_visual_impaired": ("--visual-impaired-flag", True),
        "flag_original": ("--original-flag", True),
        "flag_commentary": ("--commentary-flag", True),
        "sync": ("--sync", False),
    }

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
        # Group tracks by file_path to avoid repeating input files
        files: dict[str, list[MKVTrack]] = {}
        for track in mkv_file.tracks:
            if track.file_path not in files:
                files[track.file_path] = []
            files[track.file_path].append(track)

        for file_path, tracks in files.items():
            # 1. Properties for all tracks in this file
            for track in tracks:
                yield from self._generate_properties(track)
                yield from self._generate_exclusions(track)

            # 2. Track Selection (consolidated by type)
            audio_ids = []
            video_ids = []
            subtitle_ids = []

            for track in tracks:
                t_type = track.track_type
                t_id = str(track.track_id)
                if t_type == "audio":
                    audio_ids.append(t_id)
                elif t_type == "video":
                    video_ids.append(t_id)
                elif t_type == "subtitles":
                    subtitle_ids.append(t_id)

            # Generate selection flags
            if audio_ids:
                yield "--audio-tracks"
                yield ",".join(audio_ids)
            else:
                yield "--no-audio"

            if video_ids:
                yield "--video-tracks"
                yield ",".join(video_ids)
            else:
                yield "--no-video"

            if subtitle_ids:
                yield "--subtitle-tracks"
                yield ",".join(subtitle_ids)
            else:
                yield "--no-subtitles"

            # 3. Input file path (once per file)
            yield file_path

    def _generate_properties(self, track: MKVTrack) -> Iterator[str]:
        # Language (Precedence handled by effective_language)
        if track.effective_language:
            yield "--language"
            yield f"{track.track_id}:{track.effective_language}"

        # Standard Properties
        for attr, (flag, is_bool) in self.property_flags.items():
            if attr in ("language", "language_ietf"):
                continue

            val = getattr(track, attr, None)
            if val is not None:
                yield flag
                if is_bool:
                    yield f"{track.track_id}:{1 if val else 0}"
                else:
                    yield f"{track.track_id}:{val}"

        # Compression
        if track.compression is not None:
            yield "--compression"
            yield f"{track.track_id}:{'zlib' if track.compression else 'none'}"

    def _generate_exclusions(self, track: MKVTrack) -> Iterator[str]:
        exclusions = {
            "no_chapters": "--no-chapters",
            "no_global_tags": "--no-global-tags",
            "no_track_tags": "--no-track-tags",
            "no_attachments": "--no-attachments",
        }
        for attr, flag in exclusions.items():
            if getattr(track, attr, False):
                yield flag
