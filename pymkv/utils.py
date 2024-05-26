from __future__ import annotations

import os
import shlex


def prepare_mkvtoolnix_path(path: str | list[str] | os.PathLike) -> list[str]:
    """
    Parameters
    ----------
    path : str | list[str] | os.PathLike
        The path to prepare for use with MKVToolNix.

    Returns
    -------
    list[str]
        The prepared path as a list of strings.

    Raises
    ------
    ValueError
        If the path type is invalid. Expected str, list of str, or os.PathLike.
    """
    if isinstance(path, os.PathLike):
        return [os.fspath(path)]
    elif isinstance(path, str):  # noqa: RET505
        return shlex.split(path)
    elif isinstance(path, list):
        return path
    else:
        msg = "Invalid path type. Expected str, List[str], or os.PathLike."
        raise ValueError(msg)  # noqa: TRY004
