"""Base class defines the interface for command generation.

All command generators for mkvmerge options must inherit from the `CommandGeneratorBase` class.

Examples
--------
>>> from pymkv.command_generators.base import CommandGeneratorBase  # doctest: +SKIP
>>> class MyGenerator(CommandGeneratorBase):  # doctest: +SKIP
...     def generate(self, mkv_file):
...         yield "-v"
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pymkv.MKVFile import MKVFile


class CommandGeneratorBase(ABC):
    """Abstract base class for a part of the mkvmerge command generation pipeline."""

    @abstractmethod
    def generate(self, mkv_file: MKVFile) -> Iterator[str]:
        """
        Generates the command arguments for this specific part of the mkvmerge command.

        Parameters
        ----------
        mkv_file : MKVFile
            The :class:`~pymkv.MKVFile` object containing the data to be processed.

        Yields
        ------
        str
            The next command line argument token.

        Examples
        --------
        >>> class MyGenerator(CommandGeneratorBase):
        ...     def generate(self, mkv_file):
        ...         yield "-v"
        >>>
        >>> gen = MyGenerator()
        >>> list(gen.generate(None))
        ['-v']
        """
        ...
