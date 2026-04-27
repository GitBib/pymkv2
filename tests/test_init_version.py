import importlib
import importlib.metadata

import pytest

import pymkv


def test_version_is_set() -> None:
    assert pymkv.__version__ is not None


def test_version_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", _raise)
    importlib.reload(pymkv)
    assert pymkv.__version__ is None

    # Restore original state
    monkeypatch.undo()
    importlib.reload(pymkv)
