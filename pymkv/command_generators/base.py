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
        """
        ...
