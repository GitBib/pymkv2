# pymkv2
[![PyPI Version](https://img.shields.io/pypi/v/pymkv2.svg)](https://pypi.python.org/pypi/pymkv2)
[![License](https://img.shields.io/github/license/gitbib/pymkv.svg)](https://github.com/GitBib/pymkv2/blob/master/LICENSE.txt)
[![codecov](https://codecov.io/github/GitBib/pymkv2/branch/master/graph/badge.svg?token=2JDX5HHGUO)](https://codecov.io/github/GitBib/pymkv2)
[![versions](https://img.shields.io/pypi/pyversions/pymkv2.svg)](https://github.com/GitBib/pymkv2)

pymkv2 is a Python wrapper for mkvmerge and other tools in the MKVToolNix suite. It provides support for muxing,
splitting, linking, chapters, tags, and attachments through the use of mkvmerge.

## About pymkv2
it's a fork of the [pymkv](https://github.com/sheldonkwoodward/pymkv) project. pymkv2 is a Python 3 library for manipulating MKV files
with mkvmerge. Constructing mkvmerge commands manually can quickly become confusing and complex. To remedy this, I decided to write
this library to make mkvmerge more scriptable and easier to use. Please open new issues for any bugs you find,
support is greatly appreciated!

## Installation
mkvmerge must be installed on your computer, it is needed to process files when creating MKV objects. It is also
recommended to add it to your $PATH variable but a different path can be manually specified. mkvmerge can be found
and downloaded from [here](https://mkvtoolnix.download/downloads.html) or from most package managers.

To install pymkv from PyPI, use the following command:

    $ pip install pymkv2

You can also clone the repo and run the following command in the project root to install the source code as editable:

    $ pip install -e .

## Language code utilities

pymkv exposes a normalized API for comparing and translating language codes
across ISO 639-1, /B, /T, 639-3, BCP 47, and English language names. Use these
helpers instead of comparing language strings directly — `language_ietf="zh-Hans"`
and `language="chi"` should match, and they do via `languages_match`.

```python
from pymkv import (
    MKVFile,
    get_iso639_2,
    languages_match,
    language_equivalents,
    normalize_language,
)

get_iso639_2("English")        # "eng"
get_iso639_2("fra")            # "fre"  (canonical /B)
normalize_language("zh-Hans")  # "chi"  (BCP 47 subtag stripped)
languages_match("zho", "zh")   # True
language_equivalents("eng")    # frozenset({"eng", "en"})

# MKVTrack setter is now lenient — any recognized form is accepted and
# canonicalized to /B on store.
mkv = MKVFile("path/to/file.mkv")
track = mkv.tracks[1]
track.language = "Chinese"        # stored as "chi"
track.matches_language("zh")       # True (works against language_ietf too)
track.effective_language           # "chi" — normalized /B
```

## Documentation
The documentation for pymkv can be found [here](https://gitbib.github.io/pymkv2/) or in the project's docstrings.
