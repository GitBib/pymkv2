from __future__ import annotations

import os
import shlex


def prepare_mkvmerge_path(mkvmerge_path: str | list[str] | os.PathLike) -> list[str]:
    """
    Parameters
    ----------
    mkvmerge_path : str | list[str] | os.PathLike
        The path(s) to the mkvmerge executable or script.

    Returns
    -------
    list[str]
        A list containing the prepared mkvmerge path(s).

    Raises
    ------
    ValueError
        If the `mkvmerge_path` parameter is not of type str, list[str], or os.PathLike.
    """
    if isinstance(mkvmerge_path, os.PathLike):
        return [os.fspath(mkvmerge_path)]
    elif isinstance(mkvmerge_path, str):  # noqa: RET505
        if mkvmerge_path == "mkvmerge":
            return ["mkvmerge"]
        else:  # noqa: RET505
            return shlex.split(mkvmerge_path)
    elif isinstance(mkvmerge_path, list):
        return mkvmerge_path
    else:
        msg = "Invalid mkvmerge_path type. Expected str, List[str], or os.PathLike."
        raise ValueError(msg)  # noqa: TRY004
