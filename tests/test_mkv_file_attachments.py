from pathlib import Path

import msgspec
import pytest

from pymkv import MKVAttachment, MKVFile
from pymkv.Verifications import get_file_info

ATTACHMENT_COUNT_1 = 1
ATTACHMENT_COUNT_2 = 2
ATTACHMENT_COUNT_3 = 3


def test_get_attachment(temp_file: str) -> None:
    mkv = MKVFile()
    attachment1 = MKVAttachment(temp_file, name="Test1")
    attachment2 = MKVAttachment(temp_file, name="Test2")
    mkv.add_attachment(attachment1)
    mkv.add_attachment(attachment2)

    attachments = mkv.get_attachment()
    assert isinstance(attachments, list)
    assert len(attachments) == ATTACHMENT_COUNT_2

    attachment = mkv.get_attachment(0)
    assert isinstance(attachment, MKVAttachment)
    assert attachment.name == "Test1"

    attachment = mkv.get_attachment(1)
    assert isinstance(attachment, MKVAttachment)
    assert attachment.name == "Test2"

    with pytest.raises(IndexError):
        mkv.get_attachment(2)


def test_remove_attachment(temp_file: str) -> None:
    mkv = MKVFile()
    attachment1 = MKVAttachment(temp_file, name="Test1")
    attachment2 = MKVAttachment(temp_file, name="Test2")
    mkv.add_attachment(attachment1)
    mkv.add_attachment(attachment2)

    assert len(mkv.attachments) == ATTACHMENT_COUNT_2

    mkv.remove_attachment(0)
    assert len(mkv.attachments) == ATTACHMENT_COUNT_1
    assert mkv.attachments[0].name == "Test2"

    mkv.remove_attachment(0)
    assert len(mkv.attachments) == 0

    with pytest.raises(IndexError):
        mkv.remove_attachment(0)


def test_remove_all_attachments(temp_file: str) -> None:
    mkv = MKVFile()
    mkv.add_attachment(MKVAttachment(temp_file, name="Test1"))
    mkv.add_attachment(MKVAttachment(temp_file, name="Test2"))
    mkv.add_attachment(MKVAttachment(temp_file, name="Test3"))

    assert len(mkv.attachments) == ATTACHMENT_COUNT_3

    mkv.remove_all_attachments()
    assert len(mkv.attachments) == 0


def test_init_with_attachments(get_path_test_file: Path) -> None:
    info = msgspec.to_builtins(get_file_info(get_path_test_file, "mkvmerge"))
    has_attachments = "attachments" in info and len(info["attachments"]) > 0

    mkv = MKVFile(str(get_path_test_file))

    if has_attachments:
        assert len(mkv.attachments) > 0

        for attachment in mkv.attachments:
            assert attachment.source_id is not None
            assert attachment.source_file is not None
            assert attachment.source_file == str(get_path_test_file)
    else:
        assert hasattr(mkv, "attachments")
        pytest.skip("Test file doesn't contain attachments")


def test_add_and_remove_attachments_workflow(get_path_test_file: Path, temp_file: str, tmp_path: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))

    initial_count = len(mkv.attachments)

    attachment1 = MKVAttachment(temp_file, name="NewAttachment1")
    attachment2 = MKVAttachment(temp_file, name="NewAttachment2")
    mkv.add_attachment(attachment1)
    mkv.add_attachment(attachment2)

    assert len(mkv.attachments) == initial_count + ATTACHMENT_COUNT_2

    mkv.remove_attachment(initial_count)

    assert len(mkv.attachments) == initial_count + ATTACHMENT_COUNT_1

    output_path = str(tmp_path / "output_with_attachments.mkv")

    command = mkv.command(output_path, subprocess=True)

    if initial_count > 0:
        attachment_cmd_elements = [arg for arg in command if isinstance(arg, str) and "--attachment" in arg]
        assert attachment_cmd_elements

    attachment_name_found = any(
        isinstance(arg, str)
        and "--attachment-name" in arg
        and i + 1 < len(command)
        and "NewAttachment2" in command[i + 1]
        for i, arg in enumerate(command)
    )
    assert attachment_name_found, "New attachment name not found in command"


def test_attachment_preservation(get_path_test_file: Path, tmp_path: Path, temp_file: str) -> None:
    mkv = MKVFile(str(get_path_test_file))

    initial_count = len(mkv.attachments)
    attachment = MKVAttachment(temp_file, name="NewAttachment")
    mkv.add_attachment(attachment)

    assert len(mkv.attachments) == initial_count + 1

    output_path = str(tmp_path / "output_attachment.mkv")
    mkv.mux(output_path)

    mkv = MKVFile(output_path)
    mkv.remove_attachment(0)
    command = mkv.command(output_path, subprocess=True)

    assert "--no-attachments" in command or "--attachments" in command, f"{command}"
    output_path = str(tmp_path / "output_with_excluded_attachment.mkv")
    mkv.mux(output_path)
    mkv = MKVFile(output_path)
    assert len(mkv.attachments) == 0, f"Attachments should be removed, {mkv.attachments}"


def test_attachments_preserved_after_mux(temp_file: str, tmp_path: Path, get_path_test_file: Path) -> None:
    mkv = MKVFile(str(get_path_test_file))

    initial_count = len(mkv.attachments)
    attachment1 = MKVAttachment(temp_file, name="TestAttachment1")
    attachment2 = MKVAttachment(temp_file, name="TestAttachment2")

    mkv.add_attachment(attachment1)
    mkv.add_attachment(attachment2)

    assert len(mkv.attachments) == initial_count + ATTACHMENT_COUNT_2

    output_path = str(tmp_path / "output_with_attachments.mkv")

    mkv.mux(output_path)

    assert Path(output_path).exists(), "Output file was not created"

    output_info = msgspec.to_builtins(get_file_info(output_path, "mkvmerge"))

    assert "attachments" in output_info, "No attachments found in output file"
    assert len(output_info["attachments"]) >= ATTACHMENT_COUNT_2, "Not all attachments were preserved"

    attachment_names = [attachment.get("file_name", "") for attachment in output_info["attachments"]]

    assert "TestAttachment1" in attachment_names, "TestAttachment1 not found in output file"
    assert "TestAttachment2" in attachment_names, "TestAttachment2 not found in output file"

    output_mkv = MKVFile(output_path)

    assert len(output_mkv.attachments) >= ATTACHMENT_COUNT_2, (
        f"Expected at least 2 attachments, found {output_mkv.attachments}"
    )
