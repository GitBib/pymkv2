from typing import cast

import pytest

from pymkv.Timestamp import Timestamp


def test_init() -> None:
    ts1 = Timestamp("01:23:45.678")
    assert str(ts1) == "01:23:45.678"

    ts2 = Timestamp(3661)  # 1 hour, 1 minute, 1 second
    assert str(ts2) == "01:01:01"

    ts3 = Timestamp(hh=2, mm=30, ss=15, nn=500000000)
    assert str(ts3) == "02:30:15.5"


def test_comparison() -> None:
    ts1 = Timestamp("01:00:00")
    ts2 = Timestamp("02:00:00")
    ts3 = Timestamp("01:00:00")

    assert ts1 < ts2
    assert ts2 > ts1
    assert ts1 <= ts3
    assert ts1 >= ts3
    assert ts1 == ts3
    assert ts1 != ts2


def test_properties() -> None:
    ts = Timestamp("12:34:56.789")
    assert ts.hh == 12  # noqa: PLR2004
    assert ts.mm == 34  # noqa: PLR2004
    assert ts.ss == 56  # noqa: PLR2004
    assert ts.nn == 789000000  # noqa: PLR2004


def test_setters() -> None:
    ts = Timestamp()
    ts.hh = 10
    ts.mm = 20
    ts.ss = 30
    ts.nn = 400000000
    assert str(ts) == "10:20:30.4"

    # Test overflow handling
    ts.mm = 70
    assert ts.mm == 0


def test_verify() -> None:
    assert Timestamp.verify("01:23:45")
    assert Timestamp.verify("01:23:45.678")
    assert not Timestamp.verify("25.00:00")


def test_extract() -> None:
    ts = Timestamp()
    ts.extract(3661)  # 1 hour, 1 minute, 1 second

    assert ts.hh == 1
    assert ts.mm == 1
    assert ts.ss == 1
    assert ts.nn == 0


def test_getitem() -> None:
    ts = Timestamp("01:23:45.678")
    assert ts[0] == 1  # hours
    assert ts[1] == 23  # minutes  # noqa: PLR2004
    assert ts[2] == 45  # seconds  # noqa: PLR2004
    assert ts[3] == 45  # seconds (again, as per the implementation)  # noqa: PLR2004


def test_invalid_input() -> None:
    with pytest.raises(TypeError):
        Timestamp(cast(str, []))  # Invalid type

    with pytest.raises(ValueError):  # noqa: PT011
        Timestamp("invalid_timestamp")


def test_ts_property() -> None:
    ts = Timestamp("01:23:45.678")
    assert ts.ts == "01:23:45.678"

    ts.ts = "02:30:00"
    assert ts.ts == "02:30:00"

    with pytest.raises(TypeError):
        ts.ts = cast(str, [])
