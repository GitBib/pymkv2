import pytest

from pymkv import MKVTrack


def test_language_name_to_code(get_path_test_file: str) -> None:
    track = MKVTrack(get_path_test_file)
    track.language = "English"
    assert track.language == "eng"

    track.language = "fra"
    assert track.language == "fre"

    track.language = "deu"
    assert track.language == "ger"

    # language case insensitive
    track.language = "english"  # lowercase
    assert track.language == "eng"

    track.language = "ARAbIC"
    assert track.language == "ara"

    with pytest.raises(
        ValueError,
        match="cannot be mapped to a valid ISO 639-2 language code",
    ):
        track.language = "invalid-lang"

    # unset language
    track.language = None
    assert track.language is None
