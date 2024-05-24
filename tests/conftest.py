from pathlib import Path

import pytest


@pytest.fixture()
def get_base_path() -> Path:
    return Path.cwd() / "tests"


@pytest.fixture()
def get_path_test_file(get_base_path: Path) -> Path:
    return get_base_path / "file.mkv"


@pytest.fixture(autouse=True)
def cleanup_mkv_files(get_base_path: Path, get_path_test_file: Path) -> None:  # noqa: PT004
    yield
    for file_path in get_base_path.glob("*.mkv"):
        if file_path != get_path_test_file:
            file_path.unlink()
