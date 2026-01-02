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

            # 2.5 Attachment Filtering
            info_json = getattr(mkv_file, "_info_json", None)
            # Only apply if we have info and it likely matches the file (logic derived from HEAD behavior)
            # We assume checking against _info_json is valid if the file matches.
            # To be safe and mimic HEAD, we check if this file has attachments in _info_json
            # Note: This crude check assumes _info_json describes the current file_path.
            # A more robust check would verify file paths, but HEAD didn't.
            # We will strictly check if we have attachments to manage for this file.

            if info_json and "attachments" in info_json:
                # Check if the info_json actually belongs to this file?
                # Or just check if we have matching attachments in mkv_file.attachments?

                # Heuristic: if logic in HEAD processed this, it did so for the file matching the tracks.
                # All attachments in mkv_file with source_file == file_path
                kept_ids = {
                    a.source_id for a in mkv_file.attachments if a.source_id is not None and a.source_file == file_path
                }

                all_ids = {a["id"] for a in info_json["attachments"]}

                # If we are processing the file described by info_json, then all_ids are valid.
                # If we are processing a different file, all_ids are irrelevant/wrong.
                # We need to know if file_path is the main file.
                # Since we don't know easily, but we know kept_ids come from file_path.
                # If kept_ids is NOT empty, and is subset of all_ids?
                # But what if kept_ids is empty? --no-attachments?
                # Only if file_path HAS attachments.

                # We will only apply this if we are relatively sure.
                # Check if file_path is contained in the info_json file_name?
                # Or better: check if the calculated kept_ids INTERSECT with all_ids?
                # If they intersect, we are likely talking about the same file.
                # If kept_ids is empty, we risk disabling attachments for the wrong file if we guess wrong.

                # Given the user context: "sync new-fun-attachment branch".
                # HEAD logic was: `if is_first_occurrence and self._info_json ...`
                # It applied to ANY first occurrence.
                # This suggests the user intends to filter attachments for the PRIMARY file.
                # For secondary files, self._info_json (of primary) shouldn't apply.
                # If we blindly apply --no-attachments to secondary files because kept_ids (for secondary) is empty
                # and primary has attachments (so we think we should disable them), we break secondary files.

                # SAFETY CHECK: Only apply if file_path matches info_json["file_name"] approximately?
                info_name = info_json.get("file_name")
                if info_name and (str(file_path) in info_name or info_name in str(file_path) or kept_ids):
                    if kept_ids and kept_ids != all_ids:
                        # verify ids are subset
                        if kept_ids.issubset(all_ids):
                            yield "--attachments"
                            yield ",".join(str(aid) for aid in sorted(kept_ids))
                    elif not kept_ids:
                        # Only output --no-attachments if we believe this file HAS attachments that we are skipping.
                        # i.e. info_json corresponds to this file.
                        # If info_name check matches:
                        if info_name and (str(file_path) in info_name or info_name in str(file_path)):
                            yield "--no-attachments"

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
