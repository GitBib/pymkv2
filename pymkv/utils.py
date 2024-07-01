from __future__ import annotations

import os
import shlex
from functools import wraps
from typing import Any, Callable


def prepare_mkvtoolnix_path(path: str | list[str] | os.PathLike | tuple[str, ...]) -> tuple[str, ...]:
    """
    Parameters
    ----------
    path : str | list[str] | os.PathLike | tuple
        The path to prepare for use with MKVToolNix.

    Returns
    -------
    tuple[str, ...]
        The prepared path as a list of strings.

    Raises
    ------
    ValueError
        If the path type is invalid. Expected str, list of str, or os.PathLike.
    """
    if isinstance(path, os.PathLike):
        return (os.fspath(path),)
    elif isinstance(path, str):  # noqa: RET505
        return tuple(shlex.split(path))
    elif isinstance(path, list):
        return tuple(path)
    elif isinstance(path, tuple):
        return path
    else:
        msg = "Invalid path type. Expected str, List[str], Tuple[str] or os.PathLike."
        raise ValueError(msg)  # noqa: TRY004


def ensure_info(info_attr: str, fetch_func: Callable, fetch_args: list[str], **fetch_kwargs: Any) -> Callable:  # noqa: ANN401
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if not hasattr(self, info_attr) or getattr(self, info_attr) is None:
                func_params = []
                for arg in fetch_args:
                    if hasattr(self, arg):
                        func_params.append(getattr(self, arg))
                    else:
                        func_params.append(arg)
                setattr(self, info_attr, fetch_func(*func_params, **fetch_kwargs))
            return method(self, *args, **kwargs)

        return wrapper

    return decorator
