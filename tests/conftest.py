import random
from collections.abc import Generator
from pathlib import Path

import pytest
from pyinstrument import Profiler

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
    for ext in ["*.mkv", "*.mp4", "*.ogg", "*.txt", "*.srt"]:
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
