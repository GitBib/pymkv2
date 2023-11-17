# sheldon woodward
# 3/18/18

"""ISO639-2 Three Character Language Codes"""

from iso639 import languages


def is_iso639_2(language):
    """The `is_iso639_2` function checks if a given language code is a valid ISO 639-2 language code.

    Args:
        language: The language code to be checked.

    Returns:
        bool: True if the language code is a valid ISO 639-2 language code, False otherwise.

    Raises:
        None
    """
    try:
        languages.get(part2b=language)
        return True
    except KeyError:
        return False
