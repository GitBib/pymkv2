import pytest

from pymkv import MKVTrack


def test_language_name_to_code(get_path_test_file: str):
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

    with pytest.raises(ValueError) as exc:
        track.language = "invalid-lang"
    assert "cannot be mapped to a valid ISO 639-2 language code" in str(exc.value)

    # unset language
    track.language = None
    assert track.language is None
