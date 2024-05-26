# pymkv2
[![PyPI Version](https://img.shields.io/pypi/v/pymkv2.svg)](https://pypi.python.org/pypi/pymkv2)
[![License](https://img.shields.io/github/license/gitbib/pymkv.svg)](https://github.com/gitbib/pymkv/LICENSE.txt)

pymkv2 is a Python wrapper for mkvmerge and other tools in the MKVToolNix suite. It provides support for muxing,
splitting, linking, chapters, tags, and attachments through the use of mkvmerge.

## About pymkv2
it's a fork of the [project](https://github.com/sheldonkwoodward/pymkv). Pymkv2 is a Python 3 library for manipulating MKV files with mkvmerge. Constructing mkvmerge commands manually can
quickly become confusing and complex. To remedy this, I decided to write this library to make mkvmerge more
scriptable and easier to use. Please open new issues for any bugs you find, support is greatly appreciated!

## Installation
mkvmerge must be installed on your computer, it is needed to process files when creating MKV objects. It is also
recommended to add it to your $PATH variable but a different path can be manually specified. mkvmerge can be found
and downloaded from [here](https://mkvtoolnix.download/downloads.html) or from most package managers.

To install pymkv from PyPI, use the following command:

    $ pip install pymkv2

You can also clone the repo and run the following command in the project root to install the source code as editable:

    $ pip install -e .

## Documentation
The documentation for pymkv can be found [here](https://gitbib.github.io/pymkv2/) or in the project's docstrings.

### Tests
~~After completing documentation for the existing features, unit tests need to be written to "lock in" the existing
functionality. Generating mkvmerge commands can be complex and it is easy to subtly modify an existing feature when
adding a new one. Unit tests will ensure that features remain the same and help prevent bugs in the future.~~

### Cleanup
~~The existing code base could use some tidying, better commenting, debugging, and a general styling overhaul. Setting up
[pre-commit](https://pre-commit.com/) and the [Black code formatter](https://github.com/psf/black) will help keep the
code base more readable and maintainable.~~

### Features
~~Once these first three steps are complete, pymkv will be ready to start adding new features. The goal is for pymkv to
implement the functionality of mkvmerge and other MKVToolNix tools as closely as possible. New features and bugs will
be added to the [GitHub issues page](https://github.com/gitbib/pymkv/issues). As pymkv progresses through
the previous steps, this roadmap will be expanded to outline new features.~~
