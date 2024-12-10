import warnings
from functools import cache

from iana_bcp47.validator import validate_bcp47


@cache
def is_bcp47(language_ietf: str) -> bool:
    """
    Check if a given language tag is a valid BCP 47 language tag.

    Parameters
    ----------
    language_ietf : str
        The language tag to check.

    Returns
    -------
    bool
        True if the language tag is a valid BCP 47 language tag, False otherwise.
    """

    if language_ietf != "und":
        valid, msg = validate_bcp47(language_ietf)
        if not valid:
            warnings.warn(f"{language_ietf} is not a valid BCP 47 language tag; {msg}.")
            return False
        else:
            return True
    else:  # noqa: RET505
        return True
