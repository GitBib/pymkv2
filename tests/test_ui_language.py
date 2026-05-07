"""Unit tests for the ``ui_language`` plumbing on :class:`pymkv.MKVFile`.

These tests inspect the argument list returned by :meth:`MKVFile.command`
without invoking ``mkvmerge``. Real-binary coverage lives in
``tests/test_mux_progress.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pymkv import MKVFile


def test_command_default_ui_language(get_path_test_file: Path) -> None:
    """The default flag value comes from ``MKVFile.DEFAULT_UI_LANGUAGE``."""
    mkv = MKVFile(get_path_test_file)
    cmd = mkv.command("output.mkv", subprocess=True)

    assert isinstance(cmd, list)
    prefix_len = len(mkv.mkvmerge_path)
    assert cmd[prefix_len : prefix_len + 2] == ["--ui-language", MKVFile.DEFAULT_UI_LANGUAGE]


@pytest.mark.skipif(sys.platform == "win32", reason="Unix mkvmerge expects POSIX-style locale codes")
def test_default_ui_language_is_en_us_on_unix() -> None:
    """Unix builds of mkvmerge accept ``en_US`` (POSIX); ``en`` is rejected.

    The catalog is hardcoded in mkvmerge's ``translation.cpp``: each row has separate
    ``unix_locale`` and ``windows_locale`` columns, and ``get_locale()`` returns one or
    the other depending on the build target. Verified via ``mkvmerge --ui-language list``.
    """
    assert MKVFile.DEFAULT_UI_LANGUAGE == "en_US"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows mkvmerge expects short locale codes")
def test_default_ui_language_is_en_on_windows() -> None:
    """Windows builds of mkvmerge accept ``en`` (short); ``en_US`` is rejected.

    The Windows column of mkvmerge's translation table stores ``en`` for English. Passing
    ``en_US`` produces ``Error: There is no translation available for 'en_US'.`` and aborts
    the mux. Verified via ``mkvmerge --ui-language list`` on the Windows runner.
    """
    assert MKVFile.DEFAULT_UI_LANGUAGE == "en"


def test_command_explicit_ui_language_override(get_path_test_file: Path) -> None:
    """An explicit ``ui_language`` kwarg replaces the default in the argv."""
    mkv = MKVFile(get_path_test_file)
    cmd = mkv.command("output.mkv", subprocess=True, ui_language="ja_JP")

    assert isinstance(cmd, list)
    prefix_len = len(mkv.mkvmerge_path)
    assert cmd[prefix_len : prefix_len + 2] == ["--ui-language", "ja_JP"]
    assert MKVFile.DEFAULT_UI_LANGUAGE not in cmd[prefix_len + 2 :]


def test_command_subclass_default_ui_language(get_path_test_file: Path) -> None:
    """Subclasses can override ``DEFAULT_UI_LANGUAGE`` and the new value is honoured."""

    class FrenchMKVFile(MKVFile):
        DEFAULT_UI_LANGUAGE = "fr_FR"

    mkv = FrenchMKVFile(get_path_test_file)
    cmd = mkv.command("output.mkv", subprocess=True)

    assert isinstance(cmd, list)
    prefix_len = len(mkv.mkvmerge_path)
    assert cmd[prefix_len : prefix_len + 2] == ["--ui-language", "fr_FR"]


def test_command_explicit_overrides_subclass_default(get_path_test_file: Path) -> None:
    """An explicit kwarg beats the subclass-level default."""

    class FrenchMKVFile(MKVFile):
        DEFAULT_UI_LANGUAGE = "fr_FR"

    mkv = FrenchMKVFile(get_path_test_file)
    cmd = mkv.command("output.mkv", subprocess=True, ui_language="ja_JP")

    assert isinstance(cmd, list)
    prefix_len = len(mkv.mkvmerge_path)
    assert cmd[prefix_len : prefix_len + 2] == ["--ui-language", "ja_JP"]


def test_command_empty_ui_language_falls_back_to_default(get_path_test_file: Path) -> None:
    """Empty string is treated as "use default" rather than forwarded as ``--ui-language ''``."""
    mkv = MKVFile(get_path_test_file)
    cmd = mkv.command("output.mkv", subprocess=True, ui_language="")

    assert isinstance(cmd, list)
    prefix_len = len(mkv.mkvmerge_path)
    assert cmd[prefix_len : prefix_len + 2] == ["--ui-language", MKVFile.DEFAULT_UI_LANGUAGE]


def test_command_explicit_none_uses_default(get_path_test_file: Path) -> None:
    """Explicitly passing ``ui_language=None`` resolves to ``DEFAULT_UI_LANGUAGE``."""
    mkv = MKVFile(get_path_test_file)
    cmd = mkv.command("output.mkv", subprocess=True, ui_language=None)

    assert isinstance(cmd, list)
    prefix_len = len(mkv.mkvmerge_path)
    assert cmd[prefix_len : prefix_len + 2] == ["--ui-language", MKVFile.DEFAULT_UI_LANGUAGE]


def test_command_string_form_includes_ui_language(get_path_test_file: Path) -> None:
    """The non-subprocess (joined-string) return path must also carry the flag."""
    mkv = MKVFile(get_path_test_file)
    cmd_str = mkv.command("output.mkv")

    assert isinstance(cmd_str, str)
    assert f"--ui-language {MKVFile.DEFAULT_UI_LANGUAGE}" in cmd_str
