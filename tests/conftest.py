import random
import shutil
import subprocess as sp
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from pyinstrument import Profiler

from pymkv.models import ContainerInfo, MkvMergeOutput, TrackInfo

requires_mkvtoolnix = pytest.mark.skipif(
    shutil.which("mkvmerge") is None or shutil.which("mkvextract") is None,
    reason="mkvmerge/mkvextract not installed; this test requires the real binaries",
)

TESTS_ROOT = Path.cwd()


@pytest.fixture
def get_base_path() -> Path:
    return Path.cwd() / "tests"


@pytest.fixture
def get_path_test_file(get_base_path: Path) -> Path:
    return get_base_path / "file.mkv"


@pytest.fixture
def get_path_test_file_two(get_base_path: Path) -> Path:
    return get_base_path / "file_2.mkv"


@pytest.fixture(autouse=True)
def _cleanup_mkv_files(
    get_base_path: Path,
    get_path_test_file: Path,
    get_path_test_file_two: Path,
) -> Generator[None, None, None]:
    yield
    for ext in ["*.mkv", "*.mp4", "*.ogg", "*.txt", "*.srt", "*.xml"]:
        for file_path in get_base_path.glob(ext):
            if file_path not in (get_path_test_file, get_path_test_file_two):
                file_path.unlink()


@pytest.fixture
def temp_file(tmp_path: Path) -> str:
    file = tmp_path / "test_attachment.txt"
    file.write_text("Test content")
    return str(file)


def generate_random_text() -> str:
    """Generates random text for subtitles."""
    words = ["hello", "world", "test", "subtitle", "example", "random", "generate", "python"]
    return " ".join(random.choices(words, k=random.randint(3, 8)))  # noqa: S311


def create_srt_file_with_random_text(path: Path, subtitles_count: int = 5) -> None:
    """Creates an SRT file with randomly generated text."""
    with Path.open(path, "w", encoding="utf-8") as file:
        for i in range(1, subtitles_count + 1):
            start = f"00:00:{i:02},000"  # Generate start time
            end = f"00:00:{i + 1:02},000"  # Generate end time
            text = generate_random_text()  # Generate random subtitle text
            file.write(f"{i}\n{start} --> {end}\n{text}\n\n")


@pytest.fixture
def get_path_test_srt(get_base_path: Path) -> Path:
    """
    Fixture to create a path for a temporary SRT file.

    Uses the `get_base_path` fixture to determine the directory and
    generates a random SRT file.
    """
    srt_path = get_base_path / "test_file.srt"
    create_srt_file_with_random_text(srt_path)
    return srt_path


@pytest.fixture
def get_path_test_chapters_xml(get_base_path: Path) -> Path:
    """
    Fixture to create a path for a temporary chapter XML file.
    """
    chapter_path = get_base_path / "chapters.xml"
    chapter_path.touch()
    return chapter_path


@pytest.fixture
def get_path_test_chapters_txt(get_base_path: Path) -> Path:
    """
    Fixture to create a path for a temporary simple chapter TXT file.
    """
    chapter_path = get_base_path / "simple_chapters.txt"
    chapter_path.touch()
    return chapter_path


# Source chapters XML used to build the real chaptered fixture file below. Deliberately includes
# fields that pymkv.chapters.Chapters does not model (ChapterPhysicalEquiv, ChapLanguageIETF) so
# tests can assert those are preserved on remux instead of being silently dropped.
_CHAPTERS_SOURCE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Chapters>
  <EditionEntry>
    <EditionUID>1111</EditionUID>
    <ChapterAtom>
      <ChapterUID>2001</ChapterUID>
      <ChapterTimeStart>00:00:00.000000000</ChapterTimeStart>
      <ChapterPhysicalEquiv>10</ChapterPhysicalEquiv>
      <ChapterDisplay>
        <ChapterString>Intro</ChapterString>
        <ChapterLanguage>chi</ChapterLanguage>
        <ChapLanguageIETF>zh-Hans</ChapLanguageIETF>
      </ChapterDisplay>
    </ChapterAtom>
  </EditionEntry>
</Chapters>
"""


@pytest.fixture
def get_path_test_file_with_chapters(
    get_path_test_file_two: Path,
    tmp_path: Path,
) -> Path:
    """
    Build a real MKV file with chapters (via ``mkvmerge --chapters``)
    """
    chapters_xml = tmp_path / "source_chapters.xml"
    chapters_xml.write_text(_CHAPTERS_SOURCE_XML, encoding="utf-8")

    output_path = tmp_path / "chaptered.mkv"

    mkvmerge = shutil.which("mkvmerge")
    assert mkvmerge is not None
    sp.run(  # noqa: S603
        [
            mkvmerge,
            "-o",
            str(output_path),
            "--chapters",
            str(chapters_xml),
            str(get_path_test_file_two),
        ],
        check=True,
        capture_output=True,
    )
    return output_path


@pytest.fixture
def real_mkvextract_chapters_xml(get_path_test_file_with_chapters: Path) -> str:
    """
    The actual XML that ``mkvextract chapters`` produces for the fixture above, including
    whatever BOM/derived fields (e.g. ``ChapterCountry``) mkvextract adds on its own.
    """

    mkvextract = shutil.which("mkvextract")
    assert mkvextract is not None
    result = sp.run(  # noqa: S603
        [mkvextract, "chapters", str(get_path_test_file_with_chapters)],
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8")


@pytest.fixture(autouse=True)
def auto_profile(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    profile_root = TESTS_ROOT / ".profiles"
    profiler = Profiler()
    profiler.start()

    yield

    profiler.stop()
    profile_root.mkdir(exist_ok=True)
    test_name = request.node.name
    results_file = profile_root / f"{test_name}.html"
    profiler.write_html(results_file)


@pytest.fixture
def mock_mkv(request: Any) -> MagicMock:  # noqa: ANN401
    """Provides a mocked MKVFile with common attributes pre-set."""
    mkv = MagicMock()
    mkv.output_path = "output.mkv"
    mkv.title = None
    mkv.mkvmerge_path = ("mkvmerge",)
    mkv._global_tags_file = None  # noqa: SLF001
    mkv.no_track_statistics_tags = False
    mkv.tracks = []
    mkv.attachments = []
    mkv._chapters_file = None  # noqa: SLF001
    mkv._chapter_language = None  # noqa: SLF001
    mkv._link_to_previous_file = None  # noqa: SLF001
    mkv._link_to_next_file = None  # noqa: SLF001
    mkv._split_options = []  # noqa: SLF001
    return mkv


@pytest.fixture
def mock_track_cleaner() -> Callable[[Any], None]:
    """Returns a helper function to ensure a mock track has all None/False attributes."""

    def clean_mock(m: Any) -> None:  # noqa: ANN401
        m.mkvmerge_path = ("mkvmerge",)
        m.track_name = None
        m.language = None
        m.language_ietf = None
        m.effective_language = None
        m.tags = {}
        m.default_track = False
        m.forced_track = False
        m.flag_hearing_impaired = False
        m.flag_visual_impaired = False
        m.flag_original = False
        m.flag_commentary = False
        m.stereo_mode = None
        m.crop = None
        m.aac_is_sbr = None
        m.reduce_to_core = None
        m.remove_dialog_normalization = None
        m.timestamps = None
        m.default_duration = None
        m.fix_bitstream_frame_rate = None
        m.nalu_size_length = None
        m.compression = None
        m.sync = None
        m.aspect_ratio = None
        m.fourcc = None
        m.pixel_dimensions = None
        m.projection_pose_yaw = None
        m.projection_pose_pitch = None
        m.projection_pose_roll = None
        m.projection_type = None
        m.projection_private = None
        m.color_matrix_coefficients = None
        m.color_bits_per_channel = None
        m.color_chroma_subsampling_horz = None
        m.color_chroma_subsampling_vert = None
        m.color_cb_subsampling_horz = None
        m.color_cb_subsampling_vert = None
        m.color_chroma_siting_horz = None
        m.color_chroma_siting_vert = None
        m.color_range = None
        m.color_transfer_characteristics = None
        m.color_primaries = None
        m.color_max_content_light = None
        m.color_max_frame_light = None

    return clean_mock


@pytest.fixture
def dummy_mkv(tmp_path: Path) -> Path:
    f = tmp_path / "dummy.mkv"
    f.touch()
    return f


@pytest.fixture
def single_video_info() -> MkvMergeOutput:
    """MkvMergeOutput with a single h264 video track."""
    return MkvMergeOutput(container=ContainerInfo(), tracks=[TrackInfo(id=0, type="video", codec="h264")])
