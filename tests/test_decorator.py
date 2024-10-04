from __future__ import annotations

from typing import Any

import pytest

from pymkv.utils import ensure_info


class MockMKVTrack:
    def __init__(self) -> None:
        self.file_path = "/path/to/file.mkv"
        self.mkvmerge_path = "/path/to/mkvmerge"
        self._info_json: dict[str, Any] | None = None
        self._track_id: int | None = None

    @property
    def track_id(self) -> int | None:
        return self._track_id

    @track_id.setter
    @ensure_info(
        "_info_json",
        lambda *args, **kwargs: {"tracks": [{"id": 0}, {"id": 1}]},
        ["file_path", "mkvmerge_path"],
        check_path=False,
    )
    def track_id(self, track_id: int) -> None:
        assert self._info_json is not None
        if not 0 <= track_id < len(self._info_json["tracks"]):
            msg = "Track index out of range"
            raise IndexError(msg)
        self._track_id = track_id


def mock_fetch_info(*args, **kwargs):  # noqa: ANN201, ANN002, ANN003
    return {"tracks": [{"id": 0}, {"id": 1}]}


def test_ensure_info_fetches_info_when_not_present() -> None:
    track = MockMKVTrack()
    assert track._info_json is None  # noqa: SLF001
    track.track_id = 0
    assert track._info_json == {"tracks": [{"id": 0}, {"id": 1}]}  # noqa: SLF001


def test_ensure_info_does_not_fetch_when_info_present() -> None:
    track = MockMKVTrack()
    track._info_json = {"tracks": [{"id": 0}]}  # noqa: SLF001
    track.track_id = 0
    assert track._info_json == {"tracks": [{"id": 0}]}  # noqa: SLF001


def test_ensure_info_raises_index_error() -> None:
    track = MockMKVTrack()
    with pytest.raises(IndexError):
        track.track_id = 2


def test_ensure_info_with_custom_fetch_function() -> None:
    class CustomMockTrack:
        def __init__(self) -> None:
            self.custom_path = "/custom/path"
            self._info_json = None

        @ensure_info("_info_json", mock_fetch_info, ["custom_path"])
        def get_info(self):  # noqa: ANN202
            return self._info_json

    track = CustomMockTrack()
    assert track.get_info() == {"tracks": [{"id": 0}, {"id": 1}]}


def test_ensure_info_with_kwargs() -> None:
    def fetch_with_kwargs(*args, **kwargs):  # noqa: ANN202, ANN002, ANN003
        return {"tracks": [{"id": 0}], "check_path": kwargs["check_path"]}

    class KwargsMockTrack:
        def __init__(self) -> None:
            self.path = "/path"
            self._info_json = None

        @ensure_info("_info_json", fetch_with_kwargs, ["path"], check_path=False)
        def get_info(self):  # noqa: ANN202
            return self._info_json

    track = KwargsMockTrack()
    assert track.get_info() == {"tracks": [{"id": 0}], "check_path": False}


def test_ensure_info_multiple_calls() -> None:
    fetch_count = 0

    def counting_fetch(*args, **kwargs):  # noqa: ANN202, ANN002, ANN003
        nonlocal fetch_count
        fetch_count += 1
        return {"tracks": [{"id": 0}]}

    class CountingMockTrack:
        def __init__(self) -> None:
            self.path = "/path"
            self._info_json = None

        @ensure_info("_info_json", counting_fetch, ["path"])
        def get_info(self):  # noqa: ANN202
            return self._info_json

    track = CountingMockTrack()
    track.get_info()
    track.get_info()
    track.get_info()
    assert fetch_count == 1
