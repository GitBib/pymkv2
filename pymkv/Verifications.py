from __future__ import annotations

import json
import os
import subprocess as sp
from pathlib import Path
from re import match
from typing import Any

from pymkv.utils import prepare_mkvtoolnix_path


def checking_file_path(file_path: str | os.PathLike[Any]) -> str:
    """
    Parameters
    ----------
    file_path : str, os.PathLike
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


def get_file_info(
    file_path: str | os.PathLike,
    mkvmerge_path: str | tuple | os.PathLike,
    check_path: bool = True,
) -> dict:
    """
    Get information about a media file using mkvmerge.

    Parameters:
    -----------
    file_path : Union[str, os.PathLike]
        The path to the media file to analyze.
    mkvmerge_path : Union[str, tuple, os.PathLike]
        The path to the mkvmerge executable or a list of command parts.
    check_path : bool, optional
        Whether to check and validate the file path. Defaults to True.

    Returns:
    --------
    Dict
        A dictionary containing the parsed JSON output from mkvmerge,
        which includes detailed information about the media file.

    Raises:
    -------
    subprocess.CalledProcessError
        If mkvmerge fails to execute or returns a non-zero exit status.
    json.JSONDecodeError
        If the output from mkvmerge cannot be parsed as JSON.
    FileNotFoundError
        If check_path is True and the file does not exist.
    TypeError
        If check_path is True and file_path is not a string or PathLike object.
    """
    if check_path:
        file_path = checking_file_path(file_path)

    return json.loads(
        sp.check_output(
            [*prepare_mkvtoolnix_path(mkvmerge_path), "-J", file_path],  # noqa: S603
        ).decode(),
    )


def verify_mkvmerge(mkvmerge_path: str | list | os.PathLike | tuple[str, ...] | None = "mkvmerge") -> bool:
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
        if isinstance(mkvmerge_path, list):
            mkvmerge_path = tuple(mkvmerge_path)
        info_json: dict = get_file_info(file_path, mkvmerge_path)

    except sp.CalledProcessError as e:
        msg = f'"{file_path}" could not be opened'
        raise ValueError(msg) from e
    return info_json["container"]["type"] == "Matroska"


def verify_file_path_and_mkvmerge(
    file_path: str,
    mkvmerge_path: str | list | tuple[str, ...] | os.PathLike | None = "mkvmerge",
) -> str:
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
        if isinstance(mkvmerge_path, list):
            mkvmerge_path = tuple(mkvmerge_path)
        info_json = get_file_info(file_path, mkvmerge_path, check_path=False)
    except sp.CalledProcessError as e:
        msg = f'"{file_path}" could not be opened'
        raise ValueError(msg) from e
    return info_json["container"]["recognized"]


def verify_supported(  # noqa: ANN201
    file_path: str,
    mkvmerge_path: str | list | tuple[str, ...] | os.PathLike | None = "mkvmerge",
):
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
        if isinstance(mkvmerge_path, list):
            mkvmerge_path = tuple(mkvmerge_path)
        info_json = get_file_info(file_path, mkvmerge_path, check_path=False)
    except sp.CalledProcessError as e:
        msg = '"{}" could not be opened'
        raise ValueError(msg) from e
    return info_json["container"]["supported"]
