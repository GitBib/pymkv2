from __future__ import annotations

import re
from typing import Final, cast

_TIMESTAMP_PATTERN: Final[re.Pattern] = re.compile(
    r"^[0-9]{1,2}(:[0-9]{1,2}){1,2}(\.[0-9]{1,9})?$",
)


class Timestamp:
    __slots__ = ["_hh", "_mm", "_ss", "_nn", "_form"]

    def __init__(  # noqa: PLR0913
        self,
        timestamp: str | int | Timestamp | None = None,
        hh: int | None = None,
        mm: int | None = None,
        ss: int | None = None,
        nn: int | None = None,
        form: str = "MM:SS",
    ) -> None:
        """
        A class that represents a timestamp used in MKVFiles.

        The Timestamp class represents a timestamp used in mkvmerge. These are commonly used for splitting MKVFiles.
        Specific time values can overridden in the timestamp using 'hh', 'mm', 'ss', and 'nn'. Any override value
        that is greater than its maximum (ex. 61 minutes) will be set to 0.

        timestamp (str, int, Timestamp):
            A str of a timestamp acceptable to mkvmerge or an int representing seconds. This value will be
            the basis of the timestamp.
        hh (int):
            Hours in the timestamp. This will override the hours in the given timestamp.
        mm (int):
            Minutes in the timestamp. This will override the minutes in the given timestamp.
        ss (int):
            Seconds in the timestamp. This will override the seconds in the given timestamp.
        nn (int):
            Nanoseconds in the timestamp. This will override the nanoseconds in the given timestamp.
        form (str):
            A str for the form of the returned timestamp. 'MM' and 'SS' must be included where 'HH' and 'NN' are
            optional but will be included if 'hh' and 'nn' are not zero.
        """
        self._hh = hh
        self._mm = mm
        self._ss = ss
        self._nn = nn
        self._form = form
        if isinstance(timestamp, Timestamp):
            self._hh = timestamp.hh
            self._mm = timestamp.mm
            self._ss = timestamp.ss
            self._nn = timestamp.nn
        elif timestamp is not None:
            self.extract(timestamp)
        else:
            self._hh = 0 if hh is None else hh
            self._mm = 0 if mm is None else mm
            self._ss = 0 if ss is None else ss
            self._nn = 0 if nn is None else nn

    def __eq__(self, other: object) -> bool:
        """
        Compares the Timestamp object with another Timestamp object for equality.

        Args:
            other: The Timestamp object to compare with.

        Returns:
            bool: True if the Timestamp objects are equal, False otherwise.
        """
        if not isinstance(other, Timestamp):
            return NotImplemented

        return self.hh == other.hh and self.mm == other.mm and self.ss == other.ss and self.nn == other.nn

    def __ne__(self, other: object) -> bool:
        """
        Compares the Timestamp object with another Timestamp object for inequality.

        Args:
            other: The Timestamp object to compare with.

        Returns:
            bool: True if the Timestamp objects are not equal, False otherwise.
        """
        if not isinstance(other, Timestamp):
            return NotImplemented
        return self.hh != other.hh or self.mm != other.mm or self.ss != other.ss or self.nn != other.nn

    def __lt__(self, other: object) -> bool:
        """
        Compares the Timestamp object with another Timestamp object to determine if it is less than.

        Args:
            other: The Timestamp object to compare with.

        Returns:
            bool: True if the Timestamp object is less than the other Timestamp object, False otherwise.
        """
        if not isinstance(other, Timestamp):
            return NotImplemented
        if self.hh != other.hh:
            return self.hh < other.hh
        elif self.mm != other.mm:  # noqa: RET505
            return self.mm < other.mm
        elif self.ss != other.ss:
            return self.ss < other.ss
        elif self.nn != other.nn:
            return self.nn < other.nn
        return False

    def __le__(self, other: object) -> bool:
        """
        Compares the Timestamp object with another Timestamp object to determine if it is less than or equal to.

        Args:
            other: The Timestamp object to compare with.

        Returns:
            bool: True if the Timestamp object is less than or equal to the other Timestamp object, False otherwise.
        """
        if not isinstance(other, Timestamp):
            return NotImplemented
        if self.hh != other.hh:
            return self.hh <= other.hh
        elif self.mm != other.mm:  # noqa: RET505
            return self.mm <= other.mm
        elif self.ss != other.ss:
            return self.ss <= other.ss
        elif self.nn != other.nn:
            return self.nn <= other.nn
        return True

    def __gt__(self, other: object) -> bool:
        """
        Compares the Timestamp object with another Timestamp object to determine if it is greater than.

        Args:
            other: The Timestamp object to compare with.

        Returns:
            bool: True if the Timestamp object is greater than the other Timestamp object, False otherwise.
        """
        if not isinstance(other, Timestamp):
            return NotImplemented
        if self.hh != other.hh:
            return self.hh > other.hh
        elif self.mm != other.mm:  # noqa: RET505
            return self.mm > other.mm
        elif self.ss != other.ss:
            return self.ss > other.ss
        elif self.nn != other.nn:
            return self.nn > other.nn
        return False

    def __ge__(self, other: object) -> bool:
        """
        Compares the Timestamp object with another Timestamp object to determine if it is greater than or equal to.

        Args:
            other: The Timestamp object to compare with.

        Returns:
            bool: True if the Timestamp object is greater than or equal to the other Timestamp object, False otherwise.
        """
        if not isinstance(other, Timestamp):
            return NotImplemented
        if self.hh != other.hh:
            return self.hh >= other.hh
        elif self.mm != other.mm:  # noqa: RET505
            return self.mm >= other.mm
        elif self.ss != other.ss:
            return self.ss >= other.ss
        elif self.nn != other.nn:
            return self.nn >= other.nn
        return True

    def __str__(self) -> str:
        return self.ts

    def __getitem__(self, index: int) -> int:
        """
        Retrieves the element at the specified index from the Timestamp object.

        Args:
            index: The index of the element to retrieve.

        Returns:
            int: The element at the specified index.
        """
        return (self.hh, self.mm, self.ss, self.ss)[index]

    @property
    def ts(self) -> str:
        """
        Generates and returns the timestamp string specified by the object.

        Returns:
            str: A formatted timestamp string based on the object's properties and format.

        The timestamp format is determined by the 'form' attribute and includes hours (HH),
        minutes (MM), seconds (SS), and nanoseconds (NN) as applicable. The method constructs
        the timestamp string according to the specified format, including or omitting parts
        based on the format and the presence of non-zero values.
        """
        format_match = re.match(
            r"^(([Hh]{1,2}):)?([Mm]{1,2}):([Ss]{1,2})(\.([Nn]{1,9}))?$",
            self.form,
        )
        assert format_match is not None
        format_groups = format_match.groups()
        timestamp_format = [format_groups[i] is not None for i in (1, 2, 3, 5)]

        timestamp_string = ""
        if timestamp_format[0] or self._hh:
            timestamp_string += f"{self.hh:0=2d}:"
        if timestamp_format[1] or self._mm:
            timestamp_string += f"{self.mm:0=2d}:"
        if timestamp_format[2] or self._ss:
            timestamp_string += f"{self.ss:0=2d}"
        if timestamp_format[3] or self._nn:
            timestamp_string += f"{self.nn / 1000000000:.9f}".rstrip("0")[1:] if self.nn else ".0"
        return timestamp_string

    @ts.setter
    def ts(self, timestamp: Timestamp) -> None:
        """
        Set a new timestamp.

        timestamp (str, int):
            A str of a timestamp acceptable to mkvmerge or an int representing seconds. This value will be
            the basis of the timestamp.
        """
        if not isinstance(timestamp, (int, str)):
            msg = f'"{type(timestamp)}" is not str or int type'
            raise TypeError(msg)
        self._hh = None
        self._mm = None
        self._ss = None
        self._nn = None
        self.extract(timestamp)

    @property
    def hh(self) -> int:
        """
        Get the hours component of the timestamp.

        Returns:
            int: The hours value.
        """
        return cast(int, self._hh)

    @hh.setter
    def hh(self, value: int) -> None:
        """
        Set the hours component of the timestamp.

        Args:
            value (int): The new hours value.
        """
        self._hh = value

    @property
    def mm(self) -> int:
        """
        Get the minutes component of the timestamp.

        Returns:
            int: The minutes value.
        """
        return cast(int, self._mm)

    @mm.setter
    def mm(self, value: int) -> None:
        """
        Set the minutes component of the timestamp.

        Args:
            value (int): The new minutes value. If greater than or equal to 60, it will be set to 0.
        """
        self._mm = value if value < 60 else 0  # noqa: PLR2004

    @property
    def ss(self) -> int:
        """
        Get the seconds component of the timestamp.

        Returns:
            int: The seconds value.
        """
        return cast(int, self._ss)

    @ss.setter
    def ss(self, value: int) -> None:
        """
        Set the seconds component of the timestamp.

        Args:
            value (int): The new seconds value. If greater than or equal to 60, it will be set to 0.
        """
        self._ss = value if value < 60 else 0  # noqa: PLR2004

    @property
    def nn(self) -> int:
        """
        Get the nanoseconds component of the timestamp.

        Returns:
            int: The nanoseconds value.
        """
        return cast(int, self._nn)

    @nn.setter
    def nn(self, value: int) -> None:
        """
        Set the nanoseconds component of the timestamp.

        Args:
            value (int): The new nanoseconds value. If greater than or equal to 1,000,000,000, it will be set to 0.
        """
        self._nn = value if value < 1000000000 else 0  # noqa: PLR2004

    @property
    def form(self) -> str:
        """
        Get the format string for the timestamp.

        Returns:
            str: The format string.
        """
        return self._form

    @form.setter
    def form(self, form: str) -> None:
        """
        Set the format string for the timestamp.

        Args:
            form (str): The new format string.
        """
        self._form = form

    @staticmethod
    def verify(timestamp: str) -> bool:
        """
        Verify a timestamp has the proper form to be used in mkvmerge.

        timestamp (str):
            The timestamp to be verified.
        """
        if not isinstance(timestamp, str):
            msg = f'"{type(timestamp)}" is not str type'
            raise TypeError(msg)
        return bool(_TIMESTAMP_PATTERN.match(timestamp))

    def extract(self, timestamp: str | int) -> None:
        """
        Extracts time info from a timestamp.

        timestamp (str, int):
            A str of a timestamp acceptable to mkvmerge or an int representing seconds. The timing info will be
            extracted from this parameter.
        """
        if not isinstance(timestamp, (str, int)):
            msg = f'"{type(timestamp)}" is not str or int type'
            raise TypeError(msg)
        if isinstance(timestamp, str) and not Timestamp.verify(
            timestamp,
        ):
            msg = f'"{timestamp}" is not a valid timestamp'
            raise ValueError(msg)
        if isinstance(timestamp, str):
            self.splitting_timestamp(timestamp)
        elif isinstance(timestamp, int):
            self._hh = int(timestamp / 3600)
            self._mm = int(timestamp % 3600 / 60)
            self._ss = int(timestamp % 3600 % 60)
            self._nn = 0

    def splitting_timestamp(self, timestamp: str) -> None:
        """
        This method splits the given timestamp string into hours, minutes, seconds, and nanoseconds. The timestamp
        string should be in the format "HH:MM:SS.NNNNNNNNN", where HH represents hours,
        MM represents minutes, SS represents seconds, and NNNNNNNNN represents nanoseconds.

        Parameters
        ----------
        timestamp : str
            The timestamp string to be split.

        Returns
        -------
        None

        Example
        -------
        >>> obj = Timestamp("12:34:56.789012345")
        >>> print(obj)
        12:34:56.789012345
        >>> assert obj.hh == 12
        >>> assert obj.mm == 34
        >>> assert obj.ss == 56
        >>> assert obj.nn == 789012345

        # Assuming self._hh, self._mm, self._ss, and self._nn are all None initially
        The hours (self.hh) will be set to 12.
        The minutes (self.mm) will be set to 34.
        The seconds (self.ss) will be set to 56.
        The nanoseconds (self.nn) will be set to 789012345.
        """
        timestamp_match = re.match(
            r"^(([0-9]{1,2}):)?([0-9]{1,2}):([0-9]{1,2})(\.([0-9]{1,9}))?$",
            timestamp,
        )
        assert timestamp_match is not None
        timestamp_groups = timestamp_match.groups()

        timestamp_lst = [cast(str, timestamp_groups[i]) for i in (1, 2, 3, 4)]
        timestamp_clean = []
        for ts in timestamp_lst:
            if ts is None:
                timestamp_clean.append(0)
            else:
                timestamp_clean.append(float(ts))
        self.hh = int(timestamp_clean[0]) if self._hh is None else self._hh
        self.mm = int(timestamp_clean[1]) if self._mm is None else self._mm
        self.ss = int(timestamp_clean[2]) if self._ss is None else self._ss
        self.nn = int(timestamp_clean[3] * 1000000000) if self._nn is None else self._nn


if __name__ == "__main__":
    pass
