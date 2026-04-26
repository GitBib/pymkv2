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
    assert ts[3] == 678000000  # nanoseconds  # noqa: PLR2004


def test_invalid_input() -> None:
    with pytest.raises(TypeError):
        Timestamp(cast("str", []))  # Invalid type

    with pytest.raises(ValueError):  # noqa: PT011
        Timestamp("invalid_timestamp")


def test_ts_property() -> None:
    ts = Timestamp("01:23:45.678")
    assert ts.ts == "01:23:45.678"

    ts.ts = "02:30:00"
    assert ts.ts == "02:30:00"

    ts.ts = ts.time
    assert ts.ts == "02:30:00"

    with pytest.raises(TypeError):
        ts.ts = cast("str", [])


def test_ts_equals() -> None:
    ts1 = Timestamp("01:23:45.678")
    ts2 = Timestamp("01:23:45.678")
    ts3 = Timestamp("02:30:00")

    assert ts1 == ts2
    assert ts1 != ts3
    assert hash(ts1) == hash(ts2)
    assert hash(ts1) != hash(ts3)


def test_nn_overflow() -> None:
    ts = Timestamp()
    ts.nn = 1_000_000_000
    assert ts.nn == 0


def test_nn_boundary() -> None:
    ts = Timestamp()
    ts.nn = 999_999_999
    assert ts.nn == 999_999_999  # noqa: PLR2004


def test_ss_overflow() -> None:
    ts = Timestamp()
    ts.ss = 60
    assert ts.ss == 0


def test_eq_with_non_timestamp() -> None:
    ts = Timestamp("01:00:00")
    result = ts.__eq__("01:00:00")
    assert result is NotImplemented


def test_ne_with_non_timestamp() -> None:
    ts = Timestamp("01:00:00")
    result = ts.__ne__(42)
    assert result is NotImplemented


def test_ts_setter_rejects_timestamp_object() -> None:
    ts = Timestamp("01:00:00")
    with pytest.raises(TypeError):
        ts.ts = Timestamp("02:00:00")  # type: ignore[assignment]


def test_init_from_timestamp_object() -> None:
    original = Timestamp("01:30:45.500000000")
    copy = Timestamp(original)
    assert copy.hh == original.hh
    assert copy.mm == original.mm
    assert copy.ss == original.ss
    assert copy.nn == original.nn


def test_comparison_by_minutes() -> None:
    ts1 = Timestamp("01:10:00")
    ts2 = Timestamp("01:20:00")
    assert ts1 < ts2
    assert ts2 > ts1
    assert ts1 <= ts2
    assert ts2 >= ts1


def test_comparison_by_seconds() -> None:
    ts1 = Timestamp("01:30:10")
    ts2 = Timestamp("01:30:50")
    assert ts1 < ts2
    assert ts2 > ts1
    assert ts1 <= ts2
    assert ts2 >= ts1


def test_comparison_by_nanoseconds() -> None:
    ts1 = Timestamp("01:30:10.100000000")
    ts2 = Timestamp("01:30:10.900000000")
    assert ts1 < ts2
    assert ts2 > ts1
    assert ts1 <= ts2
    assert ts2 >= ts1


def test_lt_equal_timestamps_returns_false() -> None:
    ts1 = Timestamp("01:30:10.500000000")
    ts2 = Timestamp("01:30:10.500000000")
    assert not (ts1 < ts2)
    assert not (ts1 > ts2)
    assert ts1 <= ts2
    assert ts1 >= ts2


def test_form_setter() -> None:
    ts = Timestamp("01:30:10")
    ts.form = "HH:MM:SS"
    assert ts.form == "HH:MM:SS"


def test_ts_property_invalid_form() -> None:
    ts = Timestamp("01:30:10")
    ts._form = "INVALID"  # noqa: SLF001
    with pytest.raises(ValueError, match="not a valid timestamp format"):
        _ = ts.ts


def test_verify_non_string() -> None:
    with pytest.raises(TypeError, match="not str type"):
        Timestamp.verify(123)  # type: ignore[arg-type]


def test_lt_with_non_timestamp() -> None:
    ts = Timestamp("01:00:00")
    assert ts.__lt__("01:00:00") is NotImplemented


def test_le_with_non_timestamp() -> None:
    ts = Timestamp("01:00:00")
    assert ts.__le__(42) is NotImplemented


def test_gt_with_non_timestamp() -> None:
    ts = Timestamp("01:00:00")
    assert ts.__gt__("01:00:00") is NotImplemented


def test_ge_with_non_timestamp() -> None:
    ts = Timestamp("01:00:00")
    assert ts.__ge__(42) is NotImplemented


def test_total_seconds_property() -> None:
    ts = Timestamp("01:01:01")
    assert ts.time == 3661  # noqa: PLR2004


def test_hash_value() -> None:
    ts = Timestamp("01:01:01")
    assert hash(ts) == 3661  # noqa: PLR2004


def test_comparison_by_hours() -> None:
    ts1 = Timestamp("01:00:00")
    ts2 = Timestamp("02:00:00")
    assert ts1 < ts2
    assert ts2 > ts1
    assert ts1 <= ts2
    assert ts2 >= ts1


def test_splitting_timestamp_invalid_string_raises() -> None:
    ts = Timestamp("01:00:00")
    with pytest.raises(ValueError, match="not a valid timestamp"):
        ts.splitting_timestamp("garbage-not-a-timestamp")
