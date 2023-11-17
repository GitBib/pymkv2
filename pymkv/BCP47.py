# sheldon woodward
# 10/21/20

"""BCP47 language region code"""

import bcp47


def is_bcp47(language_ietf):
    """The `is_bcp47` function checks if a given language tag is a valid BCP47 language tag.

    Args:
        language_ietf: The language tag to be checked.

    Returns:
        bool: True if the language tag is a valid BCP47 language tag, False otherwise.

    Raises:
        None
    """
    if language_ietf == "und":
        return True
    else:
        return language_ietf in bcp47.languages.values()
