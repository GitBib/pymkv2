from collections.abc import Generator
from pathlib import Path

import pytest


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
    for ext in ["*.mkv", "*.mp4", "*.ogg", "*.txt"]:
        for file_path in get_base_path.glob(ext):
            if file_path not in (get_path_test_file, get_path_test_file_two):
                file_path.unlink()


@pytest.fixture
def temp_file(tmp_path: Path) -> str:
    file = tmp_path / "test_attachment.txt"
    file.write_text("Test content")
    return str(file)
