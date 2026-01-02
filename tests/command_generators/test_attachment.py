from typing import Any
from unittest.mock import MagicMock

from pymkv import MKVAttachment
from pymkv.command_generators import AttachmentOptions


def gen_to_list(generator: Any, *args: Any) -> list[str]:  # noqa: ANN401
    return list(generator.generate(*args))


def test_attachment_options(mock_mkv: MagicMock) -> None:
    cover_attachment = MagicMock(spec=MKVAttachment)
    cover_attachment.file_path = "cover.jpg"
    cover_attachment.name = "cover"
    cover_attachment.mime_type = "image/jpeg"
    cover_attachment.description = "Cover Art"
    cover_attachment.attach_once = False
    cover_attachment.uid = None
    cover_attachment.source_id = None

    mock_mkv.attachments = [cover_attachment]

    opts = AttachmentOptions()
    args = gen_to_list(opts, mock_mkv)

    expected = [
        "--attachment-name",
        "cover",
        "--attachment-description",
        "Cover Art",
        "--attachment-mime-type",
        "image/jpeg",
        "--attach-file",
        "cover.jpg",
    ]
    assert args == expected
