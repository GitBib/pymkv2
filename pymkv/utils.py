from __future__ import annotations

import os
import shlex
from collections.abc import Iterable, Sequence
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

T = TypeVar("T")
SelfType = TypeVar("SelfType")


def prepare_mkvtoolnix_path(
    path: str | os.PathLike | Iterable[str],
) -> tuple[str, ...]:
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
        # Check if the path exists and is accessible
        return (path,) if Path(path).exists() else tuple(shlex.split(path))
    elif isinstance(path, tuple):
        return path
    elif isinstance(path, Sequence):
        return tuple(path)
    else:
        msg = "Invalid path type. Expected str, List[str], Tuple[str] or os.PathLike."
        raise ValueError(msg)  # noqa: TRY004


def ensure_info(
    info_attr: str,
    fetch_func: Callable[..., T],
    fetch_args: list[str],
    **fetch_kwargs: Any,  # noqa: ANN401
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    A decorator that ensures the specified attribute (info_attr) is available before executing the method.

    If the attribute doesn't exist or is None, it fetches the information using the provided fetch function.

    Parameters:
    -----------
    info_attr : str
        The name of the attribute to check and potentially fetch.
    fetch_func : Callable
        The function to call to fetch the information if it's not available.
    fetch_args : list[str]
        A list of argument names to pass to fetch_func. These can be attributes of the decorated object or
         literal strings.
    **fetch_kwargs : Any
        Additional keyword arguments to pass to fetch_func.

    Returns:
    --------
    Callable
        A decorator function that wraps the original method.

    Example:
    --------
    @ensure_info('_info', get_info, ['file_path', 'mkvmerge_path'])
    def some_method(self):
        # Use self._info here
        pass
    """

    def decorator(method: Callable[..., T]) -> Callable[..., T]:
        @wraps(method)
        def wrapper(
            self: SelfType,
            *args: list[Any],
            **kwargs: dict[str, Any],
        ) -> T:
            if not hasattr(self, info_attr) or getattr(self, info_attr) is None:
                func_params = []
                for arg in fetch_args:
                    if hasattr(self, arg):
                        func_params.append(getattr(self, arg))
                    else:
                        func_params.append(arg)
                setattr(self, info_attr, fetch_func(*func_params, **fetch_kwargs))
            return method(self, *args, **kwargs)

        return cast(Callable[..., T], wrapper)

    return decorator
