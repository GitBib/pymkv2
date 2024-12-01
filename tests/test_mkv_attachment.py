from pathlib import Path

import pytest

from pymkv.MKVAttachment import MKVAttachment


def test_init(temp_file: str) -> None:
    attachment = MKVAttachment(temp_file)
    assert attachment.file_path == temp_file
    assert attachment.mime_type == "text/plain"
    assert attachment.name is None
    assert attachment.description is None
    assert attachment.attach_once is False


def test_init_with_options(temp_file: str) -> None:
    attachment = MKVAttachment(
        temp_file,
        name="Test",
        description="Test Description",
        attach_once=True,
    )
    assert attachment.file_path == temp_file
    assert attachment.name == "Test"
    assert attachment.description == "Test Description"
    assert attachment.attach_once is True


def test_file_path_setter_valid(temp_file: str) -> None:
    attachment = MKVAttachment(temp_file)
    new_file = Path(temp_file).parent / "new_file.txt"
    new_file.write_text("New content")
    attachment.file_path = str(new_file)
    assert attachment.file_path == str(new_file)
    assert attachment.mime_type == "text/plain"
    assert attachment.name is None


def test_file_path_setter_invalid() -> None:
    with pytest.raises(FileNotFoundError):
        MKVAttachment("non_existent_file.txt")


def test_repr(temp_file: str) -> None:
    attachment = MKVAttachment(temp_file, name="Test", description="Test Description")
    repr_str = repr(attachment)
    assert "file_path" in repr_str
    assert "name" in repr_str
    assert "description" in repr_str
    assert "mime_type" in repr_str


def test_mime_type_guess(tmp_path: Path) -> None:
    # Test different file types
    file_types = {
        "test.txt": "text/plain",
        "test.jpg": "image/jpeg",
        "test.png": "image/png",
        "test.mp3": "audio/mpeg",
    }

    for file_name, expected_mime in file_types.items():
        file_path = tmp_path / file_name
        file_path.write_text("Test content")
        attachment = MKVAttachment(str(file_path))
        assert attachment.mime_type == expected_mime


def test_file_path_expansion(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))

    test_file = fake_home / "test_file.txt"
    test_file.write_text("Test content")

    attachment = MKVAttachment("~/test_file.txt")
    assert attachment.file_path == str(test_file)
