import subprocess as sp
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "Windows mkvmerge ignores LANG/LC_ALL — it picks the UI locale via Windows API, "
        "so the gettext-driven regression this test guards against cannot occur there. "
        "Cross-platform coverage of the default flag is provided by "
        "test_real_mkvmerge_default_ui_language_is_accepted_on_host."
    ),
)
def test_real_mkvmerge_progress_handler_default_ui_language_under_non_english_locale(
    monkeypatch: pytest.MonkeyPatch,
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    """Regression test for issue #115 (Unix-only).

    Force the subprocess to inherit a non-English locale; if ``--ui-language`` were
    not injected by default, ``mkvmerge`` on a system with German translations
    installed would emit ``Fortschritt: 1%`` and the ``Progress:\\s*(\\d+)%`` parser
    would silently never fire. Asserting that progress callbacks still arrive proves
    the default flag is normalising output. On translation-less installs this still
    exercises the real binary end-to-end.
    """
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    monkeypatch.setenv("LANGUAGE", "de_DE")

    output = get_base_path / "ui_language_progress_default.mkv"

    mkv = MKVFile(get_path_test_file)
    progress_values: list[int] = []
    rc = mkv.mux(output, progress_handler=progress_values.append)

    assert rc == 0
    assert output.is_file()
    assert progress_values, "progress_handler was never invoked — --ui-language not applied?"
    assert progress_values[-1] == 100  # noqa: PLR2004


def test_real_mkvmerge_explicit_ui_language_reaches_mkvmerge(
    capfd: pytest.CaptureFixture[str],
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    """Verify the explicit ``ui_language`` argument is actually forwarded to mkvmerge.

    Pass an unsupported locale: mkvmerge rejects it (``Error: There is no translation
    available for 'xyz_ZZ'``) on stdout and exits non-zero, which ``mux`` turns into
    a ``ValueError``. To prove the override actually reached the binary (and was not
    silently dropped, falling back to the platform default), assert ``xyz_ZZ`` shows
    up in the subprocess stdout captured at the file-descriptor level — which is the
    only place mkvmerge writes that string. Without this check, any unrelated
    non-zero exit would also satisfy the test.
    """
    output = get_base_path / "ui_language_invalid_override.mkv"

    mkv = MKVFile(get_path_test_file)
    with pytest.raises(ValueError, match=r"non-zero exit status \d+"):
        mkv.mux(output, ui_language="xyz_ZZ")

    captured = capfd.readouterr()
    assert "xyz_ZZ" in captured.out, (
        "mkvmerge stdout did not mention 'xyz_ZZ' — override likely never reached the binary"
    )
    assert not output.exists()


def test_real_mkvmerge_default_ui_language_is_accepted_on_host(
    get_base_path: Path,
    get_path_test_file: Path,
) -> None:
    """Smoke test: the platform-aware default must be a token mkvmerge accepts.

    If ``DEFAULT_UI_LANGUAGE`` is ever set to a value the host's mkvmerge build does
    not have in its translation catalog (e.g. ``en_US`` on Windows, ``en`` on Unix —
    both of which produce ``Error: There is no translation available for ...``),
    ``mux`` raises ``ValueError``. This test calls ``mux`` with no override and
    asserts the binary actually accepts the default and produces a file.
    """
    output = get_base_path / "ui_language_default_smoke.mkv"

    mkv = MKVFile(get_path_test_file)
    rc = mkv.mux(output, silent=True)

    assert rc == 0
    assert output.is_file()
