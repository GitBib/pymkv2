import subprocess as sp
import sys
from unittest.mock import MagicMock, patch

from pymkv import MKVFile

# pymkv.MKVFile is a class, effectively hiding the module of the same name.
# We need the module to patch 'verify_mkvmerge' which is a global in that module.
MKVFileModule = sys.modules["pymkv.MKVFile"]


def test_mux_progress_handler() -> None:
    # Setup mock Popen instance
    process_mock = MagicMock()
    # Support context manager
    process_mock.__enter__.return_value = process_mock
    process_mock.__exit__.return_value = None

    # Configure stdout to be an iterator yielding progress lines
    process_mock.stdout = iter(
        [
            "mkvmerge v1.0.0",
            "Progress: 10%",
            "Something else",
            "Progress: 50%",
            "Progress: 100%",
        ]
    )
    process_mock.communicate.return_value = (None, None)
    process_mock.returncode = 0

    # Setup callback
    progress_values = []

    def callback(percent: int) -> None:
        progress_values.append(percent)

    # Patch 'verify_mkvmerge' locally to avoid initialization running a subprocess
    with (
        patch.object(MKVFileModule, "verify_mkvmerge", return_value=True),
        patch("subprocess.Popen", return_value=process_mock) as mock_popen,
    ):
        mkv = MKVFile()
        # Mock command generation
        with patch.object(MKVFile, "command", return_value=["mkvmerge", "-o", "out.mkv"]):
            mkv.mux("out.mkv", progress_handler=callback)

        # Verify
        assert progress_values == [10, 50, 100]

        # Verify Popen was called with text=True and stdout=PIPE
        _, kwargs = mock_popen.call_args
        assert kwargs["text"] is True
        assert kwargs["stdout"] == sp.PIPE


def test_mux_progress_handler_no_progress() -> None:
    # Test with no progress lines
    process_mock = MagicMock()
    # Support context manager
    process_mock.__enter__.return_value = process_mock
    process_mock.__exit__.return_value = None

    process_mock.stdout = iter(["No progress here", "Just logs"])
    process_mock.communicate.return_value = (None, None)
    process_mock.returncode = 0

    progress_values = []

    def callback(percent: int) -> None:
        progress_values.append(percent)

    with (
        patch.object(MKVFileModule, "verify_mkvmerge", return_value=True),
        patch("subprocess.Popen", return_value=process_mock),
    ):
        mkv = MKVFile()
        with patch.object(MKVFile, "command", return_value=["mkvmerge", "-o", "out.mkv"]):
            mkv.mux("out.mkv", progress_handler=callback)

    assert progress_values == []
