"""Integration tests that perform real mkvmerge mux operations.

These tests mux files to disk, then re-read them with MKVFile to verify
that the expected properties were correctly applied by mkvmerge.
"""

from __future__ import annotations

import json
import subprocess as sp
from pathlib import Path
from typing import Any, cast

from pymkv import MKVAttachment, MKVFile, MKVTrack
from pymkv.chapters import ChapterAtom, ChapterDisplay


def _mkvmerge_json(path: str | Path) -> dict[str, Any]:
    """Run mkvmerge -J on a file and return parsed JSON."""
    result = sp.run(  # noqa: S603
        ["mkvmerge", "-J", str(path)],  # noqa: S607
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


class TestDefaultTrackFlag:
    """Verify --default-track-flag persists through mux."""

    def test_default_track_flag_true(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_default_true.mkv"
        mkv = MKVFile(get_path_test_file)
        video = cast("MKVTrack", mkv.get_track(0))
        video.default_track = True

        audio = cast("MKVTrack", mkv.get_track(1))
        audio.default_track = False

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert cast("MKVTrack", result.get_track(0)).default_track is True
        assert cast("MKVTrack", result.get_track(1)).default_track is False

    def test_default_track_flag_false(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_default_false.mkv"
        mkv = MKVFile(get_path_test_file)
        video = cast("MKVTrack", mkv.get_track(0))
        video.default_track = False

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert cast("MKVTrack", result.get_track(0)).default_track is False


class TestForcedTrackFlag:
    """Verify --forced-display-flag persists through mux."""

    def test_forced_track_flag_true(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_forced_true.mkv"
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.forced_track = True

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert cast("MKVTrack", result.get_track(1)).forced_track is True

    def test_forced_track_flag_false(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_forced_false.mkv"
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.forced_track = False

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert cast("MKVTrack", result.get_track(1)).forced_track is False


class TestAccessibilityFlags:
    """Verify hearing-impaired, visual-impaired, original, commentary flags."""

    def test_hearing_impaired_flag(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_hearing.mkv"
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.flag_hearing_impaired = True

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert cast("MKVTrack", result.get_track(1)).flag_hearing_impaired is True

    def test_visual_impaired_flag(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_visual.mkv"
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.flag_visual_impaired = True

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert cast("MKVTrack", result.get_track(1)).flag_visual_impaired is True

    def test_original_flag(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_original.mkv"
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.flag_original = True

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert cast("MKVTrack", result.get_track(1)).flag_original is True

    def test_commentary_flag(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_commentary.mkv"
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.flag_commentary = True

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert cast("MKVTrack", result.get_track(1)).flag_commentary is True


class TestAddFileFromPath:
    """Verify add_file merges tracks from a second MKV."""

    def test_add_file_path(self, get_base_path: Path, get_path_test_file: Path, get_path_test_file_two: Path) -> None:
        output = get_base_path / "integ_add_file.mkv"
        mkv = MKVFile(get_path_test_file)
        original_count = len(mkv.tracks)

        mkv.add_file(get_path_test_file_two)
        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert len(result.tracks) >= original_count

    def test_add_file_mkvfile_object(
        self, get_base_path: Path, get_path_test_file: Path, get_path_test_file_two: Path
    ) -> None:
        output = get_base_path / "integ_add_file_obj.mkv"
        mkv1 = MKVFile(get_path_test_file)
        mkv2 = MKVFile(get_path_test_file_two)
        original_count = len(mkv1.tracks)

        mkv1.add_file(mkv2)
        mkv1.mux(output, silent=True)

        result = MKVFile(output)
        assert len(result.tracks) >= original_count


class TestChaptersIntegration:
    """Verify chapters are written and readable after mux."""

    def test_chapters_persist(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_chapters.mkv"
        mkv = MKVFile(get_path_test_file)

        mkv.add_chapter(ChapterAtom(time_start="00:00:00.000", displays=[ChapterDisplay(string="Intro")]))
        mkv.add_chapter(ChapterAtom(time_start="00:01:00.000", displays=[ChapterDisplay(string="Part 1")]))
        mkv.add_chapter(ChapterAtom(time_start="00:02:00.000", displays=[ChapterDisplay(string="Part 2")]))

        mkv.mux(output, silent=True)

        info = _mkvmerge_json(output)
        # mkvmerge -J returns chapters as a list of edition entries; each has num_entries
        chapters = info.get("chapters", [])
        assert len(chapters) >= 1
        total_atoms = sum(c.get("num_entries", 0) for c in chapters)
        assert total_atoms == 3  # noqa: PLR2004


class TestSubtitleTrack:
    """Verify adding an SRT subtitle track."""

    def test_add_subtitle_track(self, get_base_path: Path, get_path_test_file: Path, get_path_test_srt: Path) -> None:
        output = get_base_path / "integ_subtitle.mkv"
        mkv = MKVFile(get_path_test_file)
        sub = MKVTrack(str(get_path_test_srt))
        sub.language = "eng"
        mkv.add_track(sub)

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        types = [t.track_type for t in result.tracks]
        assert "subtitles" in types

        sub_track = next(t for t in result.tracks if t.track_type == "subtitles")
        assert sub_track.language == "eng"


class TestAttachment:
    """Verify adding a new attachment to an MKV."""

    def test_add_attachment(self, get_base_path: Path, get_path_test_file: Path, temp_file: str) -> None:
        output = get_base_path / "integ_attachment.mkv"
        mkv = MKVFile(get_path_test_file)

        att = MKVAttachment(temp_file)
        att.name = "test_attachment.txt"
        att.description = "Integration test attachment"
        mkv.add_attachment(att)

        mkv.mux(output, silent=True)

        info = _mkvmerge_json(output)
        attachments = info.get("attachments", [])
        assert len(attachments) >= 1
        names = [a.get("file_name") or a.get("properties", {}).get("name") for a in attachments]
        assert "test_attachment.txt" in names


class TestMuxProgressHandler:
    """Verify that progress_handler receives callbacks during mux."""

    def test_progress_handler_called(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_progress.mkv"
        mkv = MKVFile(get_path_test_file)

        progress_values: list[int] = []
        mkv.mux(output, progress_handler=progress_values.append)

        assert output.is_file()
        assert len(progress_values) > 0
        assert progress_values[-1] == 100  # noqa: PLR2004


class TestMuxReturnCode:
    """Verify mux returns 0 on success."""

    def test_mux_returns_zero(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_rc.mkv"
        mkv = MKVFile(get_path_test_file)
        rc = mkv.mux(output, silent=True)
        assert rc == 0
        assert output.is_file()


class TestContextManagerMux:
    """Verify context manager cleans up temp chapters after mux."""

    def test_context_manager_cleanup_after_mux(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_ctx.mkv"

        with MKVFile(get_path_test_file) as mkv:
            mkv.add_chapter(ChapterAtom(time_start="00:00:00.000", displays=[ChapterDisplay(string="Ch1")]))
            mkv.mux(output, silent=True)
            temp_file = mkv._temp_chapters_file  # noqa: SLF001

        assert output.is_file()
        if temp_file is not None:
            assert not Path(temp_file).exists()


class TestMultipleProperties:
    """Verify multiple properties applied at once persist correctly."""

    def test_combined_properties(self, get_base_path: Path, get_path_test_file: Path) -> None:
        output = get_base_path / "integ_combined.mkv"
        mkv = MKVFile(get_path_test_file)
        mkv.title = "Integration Combined Test"

        video = cast("MKVTrack", mkv.get_track(0))
        video.track_name = "Main Video"
        video.default_track = True
        video.language = "jpn"

        audio = cast("MKVTrack", mkv.get_track(1))
        audio.track_name = "Main Audio"
        audio.default_track = False
        audio.forced_track = False
        audio.flag_commentary = True
        audio.language = "eng"

        mkv.mux(output, silent=True)

        result = MKVFile(output)
        assert result.title == "Integration Combined Test"

        v = cast("MKVTrack", result.get_track(0))
        assert v.track_name == "Main Video"
        assert v.default_track is True
        assert v.language == "jpn"

        a = cast("MKVTrack", result.get_track(1))
        assert a.track_name == "Main Audio"
        assert a.default_track is False
        assert a.flag_commentary is True
        assert a.language == "eng"


class TestDisableTrackStatisticsTags:
    """Verify --disable-track-statistics-tags affects tag output."""

    def test_disable_track_statistics_tags(self, get_base_path: Path, get_path_test_file: Path) -> None:
        # Mux without the flag (default: statistics are recalculated)
        output_with = get_base_path / "integ_with_stats.mkv"
        mkv_with = MKVFile(get_path_test_file)
        mkv_with.mux(output_with, silent=True)

        # Mux with the flag (statistics not recalculated)
        output_without = get_base_path / "integ_no_stats.mkv"
        mkv_without = MKVFile(get_path_test_file)
        mkv_without.no_track_statistics_tags = True
        mkv_without.mux(output_without, silent=True)

        info_with = _mkvmerge_json(output_with)
        info_without = _mkvmerge_json(output_without)

        tags_with = sum(t.get("num_entries", 0) for t in info_with.get("track_tags", []))
        tags_without = sum(t.get("num_entries", 0) for t in info_without.get("track_tags", []))

        # The tag counts should differ when statistics are disabled vs enabled
        assert tags_with != tags_without


class TestCommandGeneration:
    """Verify command() output contains expected flags (without muxing)."""

    def test_command_contains_default_track_flag(self, get_path_test_file: Path) -> None:
        mkv = MKVFile(get_path_test_file)
        video = cast("MKVTrack", mkv.get_track(0))
        video.default_track = True

        cmd = mkv.command("output.mkv", subprocess=True)
        assert isinstance(cmd, list)
        assert "--default-track-flag" in cmd

    def test_command_contains_forced_display_flag(self, get_path_test_file: Path) -> None:
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.forced_track = True

        cmd = mkv.command("output.mkv", subprocess=True)
        assert isinstance(cmd, list)
        assert "--forced-display-flag" in cmd

    def test_command_contains_disable_track_statistics_tags(self, get_path_test_file: Path) -> None:
        mkv = MKVFile(get_path_test_file)
        mkv.no_track_statistics_tags = True

        cmd = mkv.command("output.mkv", subprocess=True)
        assert isinstance(cmd, list)
        assert "--disable-track-statistics-tags" in cmd

    def test_command_contains_hearing_impaired_flag(self, get_path_test_file: Path) -> None:
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.flag_hearing_impaired = True

        cmd = mkv.command("output.mkv", subprocess=True)
        assert isinstance(cmd, list)
        assert "--hearing-impaired-flag" in cmd

    def test_command_contains_original_flag(self, get_path_test_file: Path) -> None:
        mkv = MKVFile(get_path_test_file)
        audio = cast("MKVTrack", mkv.get_track(1))
        audio.flag_original = True

        cmd = mkv.command("output.mkv", subprocess=True)
        assert isinstance(cmd, list)
        assert "--original-flag" in cmd
