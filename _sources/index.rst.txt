pymkv2
=====

Welcome to the pymkv2 documentation! Here you will find links to the core modules and examples of how to use each.

Modules
-------

The three primary modules of pymkv2 are :class:`~pymkv.MKVFile`, :class:`~pymkv.MKVTrack`, and
:class:`~pymkv.MKVAttachment`. The :class:`~pymkv.MKVFile` class is used to import existing or create new MKV files.
The :class:`~pymkv.MKVTrack` class is used to add individual tracks to an :class:`~pymkv.MKVFile`. The
:class:`~pymkv.MKVAttachment` class is used to add attachments to an :class:`~pymkv.MKVFile`.

Each module supports or mimics many of the same operations as mkvmerge but are not necessarily complete. If there is
functionality that is missing or an error in the docs, please open a new issue `here <https://github
.com/gitbib/pymkv2/issues>`_.

.. toctree::
    :maxdepth: 1

    pymkv/MKVFile
    pymkv/MKVTrack
    pymkv/MKVAttachment
    pymkv/Timestamp
    pymkv/Verifications

Install
-------

To install pymkv2 from PyPI, use the following command:

    $ pip install pymkv2

You can also clone the repo and run the following command in the project root to install the source code as editable:

    $ pip install -e .

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
