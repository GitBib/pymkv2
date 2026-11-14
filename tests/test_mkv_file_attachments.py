import subprocess
from pathlib import Path

import msgspec
import pytest

from pymkv import MKVAttachment, MKVFile
from pymkv.Verifications import get_file_info

ATTACHMENT_COUNT_1 = 1
ATTACHMENT_COUNT_2 = 2
ATTACHMENT_COUNT_3 = 3
SMALL_ATTACHMENT_SIZE = 24
LARGE_ATTACHMENT_SIZE = 4096
REPLACEMENT_SIZE = 1234


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


def _mkv_with_two_attachments(source: Path, tmp_path: Path) -> tuple[str, int, int]:
    """Mux two attachments of deliberately different sizes and return the path plus both sizes."""
    small = tmp_path / "small.txt"
    small.write_bytes(b"x" * SMALL_ATTACHMENT_SIZE)
    large = tmp_path / "large.txt"
    large.write_bytes(b"y" * LARGE_ATTACHMENT_SIZE)

    mkv = MKVFile(str(source))
    mkv.add_attachment(MKVAttachment(str(small)))
    mkv.add_attachment(MKVAttachment(str(large)))
    output = str(tmp_path / "with_attachments.mkv")
    mkv.mux(output, silent=True)
    return output, SMALL_ATTACHMENT_SIZE, LARGE_ATTACHMENT_SIZE


def test_attachment_size_read_from_source(get_path_test_file: Path, tmp_path: Path) -> None:
    """Each attachment reports its own payload size, not the size of the MKV holding it."""
    output, small_size, large_size = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    container_size = Path(output).stat().st_size

    attachments = MKVFile(output).attachments

    assert [a.size for a in attachments] == [small_size, large_size]
    # file_path points at the container, so a size taken from it would be this instead.
    assert container_size not in [a.size for a in attachments]


def test_attachment_size_is_none_before_muxing(temp_file: str) -> None:
    """An attachment built from a local path is not in an MKV yet, so it has no reported size."""
    assert MKVAttachment(temp_file).size is None


def test_attachment_size_survives_mux(get_path_test_file: Path, tmp_path: Path) -> None:
    output, small_size, large_size = _mkv_with_two_attachments(get_path_test_file, tmp_path)

    mkv = MKVFile(output)
    remuxed = str(tmp_path / "remuxed.mkv")
    mkv.mux(remuxed, silent=True)

    assert [a.size for a in MKVFile(remuxed).attachments] == [small_size, large_size]


def test_attachment_read_from_file_rejects_a_new_path(get_path_test_file: Path, tmp_path: Path) -> None:
    """Repointing an embedded attachment used to mux the old payload silently, so it is refused."""
    output, _, _ = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    attachment = MKVFile(output).attachments[0]
    other = tmp_path / "other.txt"
    other.write_bytes(b"z" * LARGE_ATTACHMENT_SIZE)

    with pytest.raises(ValueError, match="cannot be changed"):
        attachment.file_path = str(other)

    assert attachment.size == SMALL_ATTACHMENT_SIZE


def test_replacing_an_attachment_by_removing_and_adding(get_path_test_file: Path, tmp_path: Path) -> None:
    """The supported way to swap an attachment: remove it, add a new one, and the bytes follow."""
    output, _, _ = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    replacement = tmp_path / "replacement.bin"
    replacement.write_bytes(b"r" * REPLACEMENT_SIZE)

    mkv = MKVFile(output)
    mkv.remove_attachment(0)
    mkv.add_attachment(MKVAttachment(str(replacement)))
    repointed = str(tmp_path / "replaced.mkv")
    mkv.mux(repointed, silent=True)

    result = MKVFile(repointed)
    by_name = {a.name: a.size for a in result.attachments}
    assert by_name.get("replacement.bin") == REPLACEMENT_SIZE
    assert "small.txt" not in by_name

    extracted = tmp_path / "extracted.bin"
    attachment_id = next(a.source_id for a in result.attachments if a.name == "replacement.bin")
    subprocess.run(  # noqa: S603
        ["mkvextract", repointed, "attachments", f"{attachment_id}:{extracted}"],  # noqa: S607
        check=True,
        capture_output=True,
    )
    assert extracted.read_bytes() == replacement.read_bytes()


def test_local_attachment_path_can_still_change(temp_file: str, tmp_path: Path) -> None:
    """An attachment that is not tied to an MKV is still free to point somewhere else."""
    attachment = MKVAttachment(temp_file)
    other = tmp_path / "other.bin"
    other.write_bytes(b"o" * REPLACEMENT_SIZE)

    attachment.file_path = str(other)

    assert attachment.file_path == str(other)
    assert attachment.size is None


def test_attachment_size_invalidated_when_source_id_changes(get_path_test_file: Path, tmp_path: Path) -> None:
    """source_id selects which embedded attachment is used, so the old size must not survive it."""
    output, _, _ = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    attachment = MKVFile(output).attachments[0]
    assert attachment.size == SMALL_ATTACHMENT_SIZE

    attachment.source_id = 2

    assert attachment.size is None


def test_attachment_metadata_kept_when_file_path_reassigned_to_itself(
    get_path_test_file: Path,
    tmp_path: Path,
) -> None:
    """Assigning the same path is not a mutation and must not discard what was read from the source."""
    output, _, _ = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    attachment = MKVFile(output).attachments[0]

    attachment.file_path = attachment.file_path

    assert attachment.size == SMALL_ATTACHMENT_SIZE
    assert attachment.source_id is not None
    assert attachment.name == "small.txt"


def test_attachment_sizes_with_duplicate_names_and_removal(get_path_test_file: Path, tmp_path: Path) -> None:
    """Sizes must follow the attachment, not its name or list index, and survive mkvmerge reindexing."""
    first = tmp_path / "dup" / "шрифт.ttf"
    first.parent.mkdir()
    first.write_bytes(b"a" * SMALL_ATTACHMENT_SIZE)
    second = tmp_path / "шрифт.ttf"
    second.write_bytes(b"b" * LARGE_ATTACHMENT_SIZE)

    mkv = MKVFile(str(get_path_test_file))
    mkv.add_attachment(MKVAttachment(str(first)))
    mkv.add_attachment(MKVAttachment(str(second)))
    output = str(tmp_path / "dupes.mkv")
    mkv.mux(output, silent=True)

    loaded = MKVFile(output)
    assert [a.name for a in loaded.attachments] == ["шрифт.ttf", "шрифт.ttf"]
    assert [a.size for a in loaded.attachments] == [SMALL_ATTACHMENT_SIZE, LARGE_ATTACHMENT_SIZE]

    loaded.remove_attachment(0)
    remuxed = str(tmp_path / "dupes_trimmed.mkv")
    loaded.mux(remuxed, silent=True)

    remaining = MKVFile(remuxed).attachments
    assert [a.size for a in remaining] == [LARGE_ATTACHMENT_SIZE]


def test_attachment_size_after_dropping_source_attachments(get_path_test_file: Path, tmp_path: Path) -> None:
    """Dropping the inherited attachments and adding a new one leaves only the new size."""
    output, _, _ = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    fresh = tmp_path / "fresh.bin"
    fresh.write_bytes(b"f" * 777)

    mkv = MKVFile(output)
    mkv.remove_all_attachments()
    mkv.no_attachments()
    mkv.add_attachment(MKVAttachment(str(fresh)))
    trimmed = str(tmp_path / "only_fresh.mkv")
    mkv.mux(trimmed, silent=True)

    attachments = MKVFile(trimmed).attachments
    assert [(a.name, a.size) for a in attachments] == [("fresh.bin", 777)]


def test_attachment_path_may_be_reassigned_in_another_spelling(get_path_test_file: Path, tmp_path: Path) -> None:
    """A different spelling of the same file is not a change, so it must not be refused."""
    output, _, _ = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    attachment = MKVFile(output).attachments[0]
    # Path keeps ".." segments verbatim, so this is a different string naming the same file.
    detour = tmp_path / "detour"
    detour.mkdir()
    spelled_differently = str(detour / ".." / Path(output).name)
    assert spelled_differently != output

    attachment.file_path = spelled_differently

    assert attachment.size == SMALL_ATTACHMENT_SIZE
    assert attachment.name == "small.txt"
    assert attachment.source_id is not None


def test_attachment_path_reassignment_survives_a_deleted_source(get_path_test_file: Path, tmp_path: Path) -> None:
    """An identical path is a no-op even when the container is gone, rather than FileNotFoundError."""
    output, _, _ = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    attachment = MKVFile(output).attachments[0]
    Path(output).unlink()

    attachment.file_path = attachment.file_path

    assert attachment.size == SMALL_ATTACHMENT_SIZE


def test_attachment_repoint_error_identifies_the_attachment(get_path_test_file: Path, tmp_path: Path) -> None:
    """Iterating attachments and catching the error must show which one refused."""
    output, _, _ = _mkv_with_two_attachments(get_path_test_file, tmp_path)
    other = tmp_path / "other.bin"
    other.write_bytes(b"o" * REPLACEMENT_SIZE)

    messages = []
    for attachment in MKVFile(output).attachments:
        with pytest.raises(ValueError, match="cannot be changed") as excinfo:
            attachment.file_path = str(other)
        messages.append(str(excinfo.value))

    assert "small.txt" in messages[0]
    assert "large.txt" in messages[1]
    assert messages[0] != messages[1]
