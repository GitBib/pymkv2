Verifications
============

The Verifications module provides utilities for validating files, paths and MKVToolNix executables.

Core Functions
-------------

File Path Verification
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pymkv.checking_file_path

MKVToolNix Verification
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pymkv.verify_mkvmerge

File Format Verification
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pymkv.verify_matroska

.. autofunction:: pymkv.verify_recognized

.. autofunction:: pymkv.verify_supported

Utility Functions
~~~~~~~~~~~~~~~

.. autofunction:: pymkv.get_file_info

Examples
--------

Basic Usage
~~~~~~~~~~

Here's a simple example of verifying an MKV file::

    from pymkv import verify_matroska, verify_mkvmerge
    
    # First verify mkvmerge is available
    if verify_mkvmerge("mkvmerge"):
        # Then check if file is valid Matroska
        if verify_matroska("path/to/file.mkv", "mkvmerge"):
            print("Valid MKV file!")

Advanced Usage
~~~~~~~~~~~~

Example showing multiple verifications::

    from pymkv import verify_recognized, verify_supported
    
    # Check if file format is recognized
    if verify_recognized("path/to/file.mkv"):
        # Check if format is fully supported
        if verify_supported("path/to/file.mkv"):
            print("File is fully supported!")
