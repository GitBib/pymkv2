from pathlib import Path

import pytest


@pytest.fixture()
def get_base_path() -> Path:
    return Path.cwd() / "tests"


@pytest.fixture()
def get_path_test_file(get_base_path: Path) -> Path:
    return get_base_path / "file.mkv"


@pytest.fixture()
def get_path_test_file_two(get_base_path: Path) -> Path:
    return get_base_path / "file_2.mkv"


@pytest.fixture(autouse=True)
def cleanup_mkv_files(get_base_path: Path, get_path_test_file: Path, get_path_test_file_two: Path) -> None:  # noqa: PT004
    yield
    for file_path in get_base_path.glob("*.mkv"):
        if file_path not in (get_path_test_file, get_path_test_file_two):
            file_path.unlink()
