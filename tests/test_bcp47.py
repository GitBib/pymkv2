from pymkv import BCP47


def test_is_bcp47_en_US() -> None:  # noqa: N802
    assert BCP47.is_bcp47("en-US") is True


def test_is_bcp47_fr_FR() -> None:  # noqa: N802
    assert BCP47.is_bcp47("fr-FR") is True


def test_is_bcp47_english() -> None:
    assert BCP47.is_bcp47("english") is False


def test_is_bcp47_und() -> None:
    assert BCP47.is_bcp47("und") is True


def test_is_bcp47_empty() -> None:
    assert BCP47.is_bcp47("") is False
