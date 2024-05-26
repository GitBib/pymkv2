# sheldon woodward
# august 5, 2019

from pkg_resources import DistributionNotFound, get_distribution

# package imports
from .MKVAttachment import MKVAttachment
from .MKVFile import MKVFile
from .MKVTrack import MKVTrack
from .Timestamp import Timestamp
from .Verifications import checking_file_path, verify_matroska, verify_mkvmerge, verify_recognized, verify_supported

# set the version number within the package using setuptools-scm
try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = None

__all__ = (
    "MKVAttachment",
    "MKVFile",
    "MKVTrack",
    "Timestamp",
    "verify_matroska",
    "verify_mkvmerge",
    "verify_recognized",
    "verify_supported",
    "checking_file_path",
)
