import subprocess
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest

from pymkv import MKVTrack
from pymkv.command_generators import TrackOptions
from pymkv.Languages import _load_mkvmerge_table


def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_track_options_grouping(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    video_track = MagicMock(spec=MKVTrack)
    video_track.file_path = "fileA.mkv"
    video_track.file_id = 0
    video_track.track_id = 0
    video_track.track_type = "video"
    video_track._track_id = 0  # noqa: SLF001
    video_track.tags = {}

    audio_track = MagicMock(spec=MKVTrack)
    audio_track.file_path = "fileA.mkv"
    audio_track.file_id = 0
    audio_track.track_id = 1
    audio_track.track_type = "audio"
    audio_track._track_id = 1  # noqa: SLF001
    audio_track.language = "eng"
    audio_track.tags = {}
    audio_track.configure_mock(**dict.fromkeys(["track_name", "default_track", "forced_track"], None))

    subtitle_track = MagicMock(spec=MKVTrack)
    subtitle_track.file_path = "fileB.mkv"
    subtitle_track.file_id = 1
    subtitle_track.track_id = 0
    subtitle_track.track_type = "subtitles"
    subtitle_track._track_id = 0  # noqa: SLF001
    subtitle_track.tags = {}
    subtitle_track.configure_mock(**dict.fromkeys(["track_name", "language", "default_track"], None))

    mock_mkv.tracks = [video_track, audio_track, subtitle_track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()

    mock_track_cleaner(video_track)
    mock_track_cleaner(audio_track)
    mock_track_cleaner(subtitle_track)

    audio_track.language = "eng"

    args = gen_to_list(opts, mock_mkv)

    assert "fileA.mkv" in args
    assert "fileB.mkv" in args
    assert args.count("fileA.mkv") == 1

    idx_a = args.index("fileA.mkv")
    opts_a = args[:idx_a]

    assert "--language" in opts_a
    assert "1:eng" in opts_a
    assert "--audio-tracks" in opts_a
    assert "1" in opts_a
    assert "--video-tracks" in opts_a
    assert "0" in opts_a

    assert "--no-video" in args[idx_a:]
    assert "--no-audio" in args[idx_a:]
    assert "--subtitle-tracks" in args[idx_a:]
    assert "0" in args[idx_a:]


def test_track_options_empty_language(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    track = MagicMock(spec=MKVTrack)
    track.file_path = "videos.mkv"
    track.track_id = 0
    track.track_type = "video"
    track.language = ""
    track.language_ietf = ""
    track.compression = None

    mock_track_cleaner(track)
    track.language = ""
    track.language_ietf = ""

    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()
    args = gen_to_list(opts, mock_mkv)

    assert args.count("--language") == 1
    assert "0:" in args


def test_track_options_exclusion_no_chapters(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "video"
    track.tags = {}
    mock_track_cleaner(track)
    track.no_chapters = True
    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()
    args = gen_to_list(opts, mock_mkv)
    assert "--no-chapters" in args


def test_track_options_exclusion_no_global_tags(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "audio"
    track.tags = {}
    mock_track_cleaner(track)
    track.no_global_tags = True
    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()
    args = gen_to_list(opts, mock_mkv)
    assert "--no-global-tags" in args


def test_track_options_exclusion_no_track_tags(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "video"
    track.tags = {}
    mock_track_cleaner(track)
    track.no_track_tags = True
    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()
    args = gen_to_list(opts, mock_mkv)
    assert "--no-track-tags" in args


def test_track_options_exclusion_no_attachments(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "video"
    track.tags = {}
    mock_track_cleaner(track)
    track.no_attachments = True
    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()
    args = gen_to_list(opts, mock_mkv)
    assert "--no-attachments" in args


def test_track_options_compression_zlib(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "video"
    track.tags = {}
    mock_track_cleaner(track)
    track.compression = True
    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()
    args = gen_to_list(opts, mock_mkv)
    assert "--compression" in args
    idx = args.index("--compression")
    assert args[idx + 1] == "0:zlib"


def test_track_options_compression_none(mock_mkv: MagicMock, mock_track_cleaner: Any) -> None:  # noqa: ANN401
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "video"
    track.tags = {}
    mock_track_cleaner(track)
    track.compression = False
    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    opts = TrackOptions()
    args = gen_to_list(opts, mock_mkv)
    assert "--compression" in args
    idx = args.index("--compression")
    assert args[idx + 1] == "0:none"


_TABLE_WITH_TOK = (
    "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
    "----------------------+----------------+----------------+---------------\n"
    "Toki Pona             | tok            |                |\n"
    "Klingon               | tlh            | tlh            |\n"
    "English               | eng            | eng            | en\n"
    "Undetermined          | und            | und            |\n"
)


@pytest.fixture
def _patched_mkvmerge_table(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Swap ``mkvmerge --list-languages`` for a synthetic, deterministic table.

    Clears the cache on both setup and teardown so the synthetic table doesn't
    leak into unrelated tests run later in the same session.
    """
    _load_mkvmerge_table.cache_clear()
    monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_k: _TABLE_WITH_TOK)
    yield
    _load_mkvmerge_table.cache_clear()


@pytest.mark.usefixtures("_patched_mkvmerge_table")
def test_track_options_emits_iso639_3_only_ietf_tag(
    mock_mkv: MagicMock,
    mock_track_cleaner: Any,  # noqa: ANN401
) -> None:
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "audio"
    track.mkvmerge_path = ("mkvmerge",)
    mock_track_cleaner(track)
    track.language_ietf = "tok"

    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    args = gen_to_list(TrackOptions(), mock_mkv)

    assert "--language" in args
    assert "0:tok" in args


@pytest.mark.usefixtures("_patched_mkvmerge_table")
def test_track_options_skips_unknown_ietf_tag(
    mock_mkv: MagicMock,
    mock_track_cleaner: Any,  # noqa: ANN401
) -> None:
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "audio"
    track.mkvmerge_path = ("mkvmerge",)
    mock_track_cleaner(track)
    track.language = "eng"
    track.language_ietf = "xyz"

    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    args = gen_to_list(TrackOptions(), mock_mkv)

    assert args.count("--language") == 1
    assert "0:eng" in args
    assert "0:xyz" not in args


@pytest.mark.usefixtures("_patched_mkvmerge_table")
@pytest.mark.parametrize("bad_ietf", ["English", "english", "English-US", "Russian"])
def test_track_options_skips_language_name_ietf(
    mock_mkv: MagicMock,
    mock_track_cleaner: Any,  # noqa: ANN401
    bad_ietf: str,
) -> None:
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "audio"
    track.mkvmerge_path = ("mkvmerge",)
    mock_track_cleaner(track)
    track.language = "eng"
    track.language_ietf = bad_ietf

    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    args = gen_to_list(TrackOptions(), mock_mkv)

    assert args.count("--language") == 1
    assert "0:eng" in args
    assert f"0:{bad_ietf}" not in args


@pytest.mark.usefixtures("_patched_mkvmerge_table")
def test_track_options_und_only_emitted_when_language_unset(
    mock_mkv: MagicMock,
    mock_track_cleaner: Any,  # noqa: ANN401
) -> None:
    track_with_lang = MagicMock(spec=MKVTrack)
    track_with_lang.file_path = "fileA.mkv"
    track_with_lang.track_id = 0
    track_with_lang.track_type = "audio"
    track_with_lang.mkvmerge_path = ("mkvmerge",)
    mock_track_cleaner(track_with_lang)
    track_with_lang.language = "eng"
    track_with_lang.language_ietf = "und"

    mock_mkv.tracks = [track_with_lang]
    mock_mkv._info_json = None  # noqa: SLF001

    args = gen_to_list(TrackOptions(), mock_mkv)
    assert "0:eng" in args
    assert "0:und" not in args

    track_no_lang = MagicMock(spec=MKVTrack)
    track_no_lang.file_path = "fileB.mkv"
    track_no_lang.track_id = 0
    track_no_lang.track_type = "audio"
    track_no_lang.mkvmerge_path = ("mkvmerge",)
    mock_track_cleaner(track_no_lang)
    track_no_lang.language = None
    track_no_lang.language_ietf = "und"

    mock_mkv.tracks = [track_no_lang]
    args = gen_to_list(TrackOptions(), mock_mkv)
    assert "0:und" in args


def test_track_options_uses_file_mkvmerge_path(
    mock_mkv: MagicMock,
    mock_track_cleaner: Any,  # noqa: ANN401
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custom_table = (
        "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
        "----------------------+----------------+----------------+---------------\n"
        "Afro-Asiatic languages| afa            | afa            |\n"
    )
    empty_table = (
        "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
        "----------------------+----------------+----------------+---------------\n"
    )

    captured: list[list[str]] = []

    def fake_check_output(cmd: list[str], **_kwargs: object) -> str:
        captured.append(cmd)
        if cmd[0].startswith("/opt/"):
            return custom_table
        return empty_table

    _load_mkvmerge_table.cache_clear()
    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "audio"
    mock_track_cleaner(track)
    track.mkvmerge_path = ("mkvmerge",)
    track.language_ietf = "afa"

    mock_mkv.tracks = [track]
    mock_mkv.mkvmerge_path = ("/opt/mkvtoolnix/bin/mkvmerge",)
    mock_mkv._info_json = None  # noqa: SLF001

    args = gen_to_list(TrackOptions(), mock_mkv)

    assert any(cmd[0] == "/opt/mkvtoolnix/bin/mkvmerge" for cmd in captured)
    assert "0:afa" in args


@pytest.mark.filterwarnings("ignore:'mkvmerge --list-languages' returned no parseable rows")
def test_track_options_ignores_per_track_mkvmerge_path_for_gate(
    mock_mkv: MagicMock,
    mock_track_cleaner: Any,  # noqa: ANN401
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custom_table = (
        "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
        "----------------------+----------------+----------------+---------------\n"
        "Afro-Asiatic languages| afa            | afa            |\n"
    )
    empty_table = (
        "English language name | ISO 639-3 code | ISO 639-2 code | ISO 639-1 code\n"
        "----------------------+----------------+----------------+---------------\n"
    )

    def fake_check_output(cmd: list[str], **_kwargs: object) -> str:
        if cmd[0].startswith("/opt/"):
            return custom_table
        return empty_table

    _load_mkvmerge_table.cache_clear()
    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "audio"
    mock_track_cleaner(track)
    track.mkvmerge_path = ("/opt/mkvtoolnix/bin/mkvmerge",)
    track.language_ietf = "afa"

    mock_mkv.tracks = [track]
    mock_mkv.mkvmerge_path = ("mkvmerge",)
    mock_mkv._info_json = None  # noqa: SLF001

    args = gen_to_list(TrackOptions(), mock_mkv)

    assert "0:afa" not in args


@pytest.mark.usefixtures("_patched_mkvmerge_table")
@pytest.mark.parametrize(
    "malformed_ietf",
    [
        " en-US ",
        " en",
        "en ",
        "en--US",
        "-en",
        "en-",
        "en-US-",
        pytest.param("en\tUS", id="en-tab-US"),
        "en US",
    ],
)
def test_track_options_skips_malformed_ietf(
    mock_mkv: MagicMock,
    mock_track_cleaner: Any,  # noqa: ANN401
    malformed_ietf: str,
) -> None:
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "audio"
    track.mkvmerge_path = ("mkvmerge",)
    mock_track_cleaner(track)
    track.language = "eng"
    track.language_ietf = malformed_ietf

    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    args = gen_to_list(TrackOptions(), mock_mkv)

    assert args.count("--language") == 1
    assert "0:eng" in args
    assert f"0:{malformed_ietf}" not in args


@pytest.mark.usefixtures("_patched_mkvmerge_table")
@pytest.mark.parametrize("malformed_und", [" und ", "und ", " und", "und-"])
def test_track_options_skips_malformed_und(
    mock_mkv: MagicMock,
    mock_track_cleaner: Any,  # noqa: ANN401
    malformed_und: str,
) -> None:
    track = MagicMock(spec=MKVTrack)
    track.file_path = "file.mkv"
    track.track_id = 0
    track.track_type = "audio"
    track.mkvmerge_path = ("mkvmerge",)
    mock_track_cleaner(track)
    track.language = None
    track.language_ietf = malformed_und

    mock_mkv.tracks = [track]
    mock_mkv._info_json = None  # noqa: SLF001

    args = gen_to_list(TrackOptions(), mock_mkv)

    assert "--language" not in args
    assert f"0:{malformed_und}" not in args
