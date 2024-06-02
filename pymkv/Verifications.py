from __future__ import annotations

import json
import os
import subprocess as sp
from pathlib import Path
from re import match

from pymkv.utils import prepare_mkvtoolnix_path


def checking_file_path(file_path: str) -> str:
    """
    Parameters
    ----------
    file_path : str
        The path to the file that needs to be checked.

    Returns
    -------
    str
        The resolved and expanded file path if it exists.

    Raises
    ------
    TypeError
        If the provided file path is not of type str.
    FileNotFoundError
        If the file path does not exist.
    """
    if not isinstance(file_path, (str, os.PathLike)):
        msg = f'"{file_path}" is not of type str'
        raise TypeError(msg)
    file_path = Path(file_path).expanduser()
    if not file_path.is_file():
        msg = f'"{file_path}" does not exist'
        raise FileNotFoundError(msg)
    return str(file_path)


def verify_mkvmerge(mkvmerge_path: str | list | os.PathLike | None = "mkvmerge") -> bool:
    """
    Parameters
    ----------
    mkvmerge_path : str | None, optional
        The path to the `mkvmerge` executable. If not provided, the default value is "mkvmerge".

    Returns
    -------
    bool
        True, if `mkvmerge_path` is valid and the `mkvmerge` executable is found. False otherwise.
    """
    try:
        mkvmerge_command = [*prepare_mkvtoolnix_path(mkvmerge_path), "-V"]
        output = sp.check_output(mkvmerge_command).decode()  # noqa: S603
    except (sp.CalledProcessError, FileNotFoundError):
        return False
    return bool(match("mkvmerge.*", output))


def verify_matroska(file_path: str | os.PathLike, mkvmerge_path: str | list | os.PathLike | None = "mkvmerge") -> bool:
    """
    Parameters
    ----------
    file_path : str or os.PathLike
        The path to the Matroska file to be verified.

    mkvmerge_path : str, optional
        The path to the `mkvmerge` executable. Default is "mkvmerge".

    Returns
    -------
    bool
        True if the Matroska file is valid and is of type "Matroska", False otherwise.

    Raises
    ------
    FileNotFoundError
        If `mkvmerge` executable is not found at the specified path.
    TypeError
        If `file_path` is not a string or an instance of `os.PathLike`.
    FileNotFoundError
        If the specified `file_path` does not exist.
    ValueError
        If the `file_path` could not be opened using `mkvmerge`.

    Notes
    -----
    This method verifies the validity of a Matroska file by checking if it is of type "Matroska"
    using the `mkvmerge` command-line tool.
    """
    if not verify_mkvmerge(mkvmerge_path=mkvmerge_path):
        msg = "mkvmerge is not at the specified path, add it there or change the mkvmerge_path property"
        raise FileNotFoundError(msg)
    try:
        info_json: dict = json.loads(
            sp.check_output(
                [*prepare_mkvtoolnix_path(mkvmerge_path), "-J", checking_file_path(file_path)],  # noqa: S603
            ).decode(),
        )

    except sp.CalledProcessError as e:
        msg = f'"{file_path}" could not be opened'
        raise ValueError(msg) from e
    return info_json["container"]["type"] == "Matroska"


def verify_file_path_and_mkvmerge(file_path: str, mkvmerge_path: str | list | os.PathLike | None = "mkvmerge") -> str:
    """
    Parameters
    ----------
    file_path : str
        The path to the file that needs to be verified.

    mkvmerge_path : str, optional
        The path to the mkvmerge executable. By default, it is set to "mkvmerge".

    Returns
    -------
    str
        The verified file path.

    Raises
    ------
    FileNotFoundError
        If mkvmerge is not found at the specified path or if the file_path does not exist.

    TypeError
        If the file_path is not of type str.

    """
    if not verify_mkvmerge(mkvmerge_path=mkvmerge_path):
        msg = "mkvmerge is not at the specified path, add it there or change the mkvmerge_path property"
        raise FileNotFoundError(msg)
    return checking_file_path(file_path)


def verify_recognized(file_path: str, mkvmerge_path: str | None = "mkvmerge"):  # noqa: ANN201
    """
    Parameters
    ----------
    file_path : str
        The path to the file that will be verified.

    mkvmerge_path : str, optional
        The path to the `mkvmerge` executable. Default is "mkvmerge".

    Returns
    -------
    bool
        True if the container format of the file is recognized, False otherwise.
    """
    file_path = verify_file_path_and_mkvmerge(file_path, mkvmerge_path)
    try:
        info_json = json.loads(
            sp.check_output(
                [*prepare_mkvtoolnix_path(mkvmerge_path), "-J", file_path],  # noqa: S603
            ).decode(),
        )
    except sp.CalledProcessError as e:
        msg = f'"{file_path}" could not be opened'
        raise ValueError(msg) from e
    return info_json["container"]["recognized"]


def verify_supported(file_path: str, mkvmerge_path: str | list | os.PathLike | None = "mkvmerge"):  # noqa: ANN201
    """
    Parameters
    ----------
    file_path : str
        The path of the file to be verified.

    mkvmerge_path : str, optional
        The path to the `mkvmerge` executable. Defaults to "mkvmerge".

    Returns
    -------
    bool
        Whether the container format of the file is supported by `mkvmerge`.

    Raises
    ------
    ValueError
        If the file cannot be opened or an error occurs during the verification process.
    """
    mkvmerge_path = prepare_mkvtoolnix_path(mkvmerge_path)
    file_path = verify_file_path_and_mkvmerge(file_path, mkvmerge_path)
    try:
        info_json = json.loads(sp.check_output([*mkvmerge_path, "-J", file_path]).decode())  # noqa: S603
    except sp.CalledProcessError as e:
        msg = '"{}" could not be opened'
        raise ValueError(msg) from e
    return info_json["container"]["supported"]
