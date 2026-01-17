"""
:mod:`pymkv.Verifications` module provides functions for validating files, paths and MKVToolNix executables.

This module contains utilities for:

- Validating file paths and existence
- Verifying MKVToolNix installation and availability
- Checking Matroska file format compatibility
- Getting detailed media file information

Examples
--------

Basic path verification::

    >>> from pymkv.Verifications import checking_file_path
    >>> file_path = checking_file_path("path/to/file.mkv")  # doctest: +SKIP
    >>> print(f"Valid file path: {file_path}")  # doctest: +SKIP

Checking MKVToolNix availability::

    >>> from pymkv.Verifications import verify_mkvmerge # doctest: +SKIP
    >>> if verify_mkvmerge("mkvmerge"): # doctest: +SKIP
    ...     print("MKVToolNix is ready to use") # doctest: +SKIP

Full file verification::

    >>> from pymkv.Verifications import verify_matroska, verify_supported # doctest: +SKIP
    >>> file_path = "path/to/file.mkv" # doctest: +SKIP
    >>> if verify_matroska(file_path, "mkvmerge"): # doctest: +SKIP
    ...     if verify_supported(file_path): # doctest: +SKIP
    ...         print("File is a valid and supported Matroska file") # doctest: +SKIP

See Also
--------
:class:`pymkv.MKVFile`
    The main class for working with MKV files
:class:`pymkv.MKVTrack`
    Class for handling individual MKV tracks
"""

from __future__ import annotations

import os
import subprocess as sp
from collections.abc import Iterable, Sequence
from functools import cache
from pathlib import Path
from re import match
from typing import Any, cast

import msgspec

from pymkv.models import MkvMergeOutput
from pymkv.utils import prepare_mkvtoolnix_path


def checking_file_path(file_path: str | os.PathLike[Any] | None) -> str:
    """Check if a file path exists and is valid.

    Parameters
    ----------
    file_path : str | os.PathLike[Any] | None
        The path to the file that needs to be checked.

    Returns
    -------
    str
        The resolved and expanded file path if it exists.

    Raises
    ------
    TypeError
        If the provided file path is not of type str or PathLike.
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
    file_path: str | os.PathLike[Any],
    mkvmerge_path: str | os.PathLike | Iterable[str],
    check_path: bool = True,
) -> MkvMergeOutput:
    """Get information about a media file using mkvmerge.

    Parameters
    ----------
    file_path : str | os.PathLike[Any]
        The path to the media file to analyze.
    mkvmerge_path : str | os.PathLike | Iterable[str]
        The path to the mkvmerge executable or a list of command parts.
    check_path : bool, optional
        Whether to check and validate the file path. Defaults to True.

    Returns
    -------
    MkvMergeOutput
        A struct containing the parsed JSON output from mkvmerge,
        which includes detailed information about the media file.

    Raises
    ------
    subprocess.CalledProcessError
        If mkvmerge fails to execute or returns a non-zero exit status.
    msgspec.ValidationError, msgspec.DecodeError
        If the output from mkvmerge cannot be parsed as JSON.
    FileNotFoundError
        If check_path is True and the file does not exist.
    TypeError
        If check_path is True and file_path is not a string or PathLike object.

    Examples
    --------
    >>> info = get_file_info('path/to/file.mkv')  # doctest: +SKIP
    >>> print(info.container.title)  # doctest: +SKIP
    """
    return msgspec.json.decode(
        get_file_info_raw(file_path, mkvmerge_path, check_path=check_path),
        type=MkvMergeOutput,
        strict=False,
    )


def get_file_info_raw(
    file_path: str | os.PathLike[Any],
    mkvmerge_path: str | os.PathLike | Iterable[str],
    check_path: bool = True,
) -> bytes:
    """Get raw information about a media file using mkvmerge.

    Parameters
    ----------
    file_path : str | os.PathLike[Any]
        The path to the media file to analyze.
    mkvmerge_path : str | os.PathLike | Iterable[str]
        The path to the mkvmerge executable or a list of command parts.
    check_path : bool, optional
        Whether to check and validate the file path. Defaults to True.

    Returns
    -------
    bytes
        The raw stdout bytes from mkvmerge -J.
    """
    if check_path:
        file_path = checking_file_path(file_path)

    cmds = [*prepare_mkvtoolnix_path(mkvmerge_path), "-J", file_path]
    return sp.check_output(cmds)  # noqa: S603


@cache
def _verify_mkvmerge_cached(mkvmerge_path_tuple: tuple[str, ...]) -> bool:
    """Internal cached function to verify mkvmerge availability."""
    try:
        mkvmerge_command = list(mkvmerge_path_tuple)
        mkvmerge_command.append("-V")
        output = sp.check_output(mkvmerge_command).decode()  # noqa: S603
    except (sp.CalledProcessError, FileNotFoundError):
        return False
    return bool(match("mkvmerge.*", output))


def verify_mkvmerge(
    mkvmerge_path: str | os.PathLike | Iterable[str] = "mkvmerge",
) -> bool:
    """Verify if mkvmerge is available at the specified path.

    Parameters
    ----------
    mkvmerge_path : str | os.PathLike | Iterable[str], optional
        The path to the mkvmerge executable. Defaults to "mkvmerge".

    Returns
    -------
    bool
        True if mkvmerge is available at the specified path, False otherwise.
    """
    mkvmerge_command = prepare_mkvtoolnix_path(mkvmerge_path)
    if isinstance(mkvmerge_command, list):
        mkvmerge_command = tuple(mkvmerge_command)
    return _verify_mkvmerge_cached(mkvmerge_command)


def verify_matroska(
    file_path: str | os.PathLike[Any],
    mkvmerge_path: str | os.PathLike | Iterable[str] = "mkvmerge",
) -> bool:
    """Verify if a file is a valid Matroska file.

    Parameters
    ----------
    file_path : str | os.PathLike[Any]
        The path to the Matroska file to be verified.
    mkvmerge_path : str | os.PathLike | Iterable[str], optional
        The path to the mkvmerge executable. Defaults to "mkvmerge".

    Returns
    -------
    bool
        True if the file is a valid Matroska file, False otherwise.

    Raises
    ------
    FileNotFoundError
        If mkvmerge executable is not found at the specified path.
    TypeError
        If file_path is not a string or PathLike object.
    FileNotFoundError
        If the specified file_path does not exist.
    ValueError
        If the file_path could not be opened using mkvmerge.

    Notes
    -----
    This function verifies the validity of a Matroska file by checking if it is of type "Matroska"
    using the mkvmerge command-line tool.
    """
    if not verify_mkvmerge(mkvmerge_path=mkvmerge_path):
        msg = "mkvmerge is not at the specified path, add it there or change the mkvmerge_path property"
        raise FileNotFoundError(msg)
    try:
        if isinstance(mkvmerge_path, Sequence) and not isinstance(mkvmerge_path, str):
            mkvmerge_path = cast("Iterable[str]", tuple(mkvmerge_path))
        info = get_file_info(file_path, mkvmerge_path)

    except sp.CalledProcessError as e:
        msg = f'"{file_path}" could not be opened'
        raise ValueError(msg) from e
    return info.container.type == "Matroska"


def verify_file_path_and_mkvmerge(
    file_path: str | os.PathLike[Any],
    mkvmerge_path: str | os.PathLike | Iterable[str] = "mkvmerge",
) -> str:
    """Verify both the file path and mkvmerge availability.

    Parameters
    ----------
    file_path : str | os.PathLike[Any]
        The path to the file that needs to be verified.
    mkvmerge_path : str | os.PathLike | Iterable[str], optional
        The path to the mkvmerge executable. Defaults to "mkvmerge".

    Returns
    -------
    str
        The verified file path.

    Raises
    ------
    FileNotFoundError
        If mkvmerge is not found at the specified path or if the file_path does not exist.
    TypeError
        If the file_path is not of type str or PathLike.

    Notes
    -----
    This function combines the verification of both the file path and mkvmerge availability
    in a single call, which is useful when both checks are needed.
    """
    if not verify_mkvmerge(mkvmerge_path=mkvmerge_path):
        msg = "mkvmerge is not at the specified path, add it there or change the mkvmerge_path property"
        raise FileNotFoundError(msg)
    return checking_file_path(file_path)


def verify_recognized(
    file_path: str | os.PathLike[Any],
    mkvmerge_path: str | os.PathLike | Iterable[str] = "mkvmerge",
) -> bool:
    """Verify if the file format is recognized by mkvmerge.

    Parameters
    ----------
    file_path : str | os.PathLike[Any]
        The path to the file that will be verified.
    mkvmerge_path : str | os.PathLike | Iterable[str], optional
        The path to the mkvmerge executable. Defaults to "mkvmerge".

    Returns
    -------
    bool
        True if the container format of the file is recognized by mkvmerge, False otherwise.

    Raises
    ------
    ValueError
        If the file cannot be opened or an error occurs during verification.
    FileNotFoundError
        If mkvmerge is not found at the specified path.
    TypeError
        If file_path is not of type str or PathLike.

    Notes
    -----
    This function checks if mkvmerge can recognize the container format of the specified file,
    which is a prerequisite for any further operations with the file.

    Examples
    --------
    >>> if verify_recognized('path/to/file.mkv'):  # doctest: +SKIP
    ...     print("File is recognized")
    """
    file_path = verify_file_path_and_mkvmerge(file_path, mkvmerge_path)
    try:
        if isinstance(mkvmerge_path, list):
            mkvmerge_path = cast("Iterable[str]", tuple(mkvmerge_path))
        info = get_file_info(file_path, mkvmerge_path, check_path=False)
    except sp.CalledProcessError as e:
        msg = f'"{file_path}" could not be opened'
        raise ValueError(msg) from e
    return info.container.recognized


def verify_supported(
    file_path: str | os.PathLike[Any],
    mkvmerge_path: str | os.PathLike | Iterable[str] = "mkvmerge",
) -> bool:
    """Verify if the file format is supported by mkvmerge.

    Parameters
    ----------
    file_path : str | os.PathLike[Any]
        The path to the file that will be verified.
    mkvmerge_path : str | os.PathLike | Iterable[str], optional
        The path to the mkvmerge executable. Defaults to "mkvmerge".

    Returns
    -------
    bool
        True if the container format of the file is supported by mkvmerge, False otherwise.

    Raises
    ------
    ValueError
        If the file cannot be opened or an error occurs during verification.
    FileNotFoundError
        If mkvmerge is not found at the specified path.
    TypeError
        If file_path is not of type str or PathLike.

    Notes
    -----
    This function checks if mkvmerge can fully support the container format of the specified file.
    A file might be recognized but not fully supported for all operations.
    """
    mkvmerge_path = prepare_mkvtoolnix_path(mkvmerge_path)
    fp = verify_file_path_and_mkvmerge(file_path, mkvmerge_path)
    try:
        if isinstance(mkvmerge_path, list):
            mkvmerge_path = tuple(mkvmerge_path)
        info = get_file_info(fp, mkvmerge_path, check_path=False)
    except sp.CalledProcessError as e:
        msg = f'"{file_path}" could not be opened'
        raise ValueError(msg) from e
    return info.container.supported
