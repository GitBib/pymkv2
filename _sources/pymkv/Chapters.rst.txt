Chapters
--------

The `pymkv.chapters` module provides a programmatic way to create and manage Matroska chapters. It uses a structured approach with `msgspec` to ensure that the chapter hierarchy (EditionEntry -> ChapterAtom -> ChapterDisplay) is correctly maintained and can be easily exported to the XML format required by `mkvmerge`.

Overview
~~~~~~~~

Matroska chapters are organized into **Editions**, which contain one or more **Chapter Atoms**. Each Chapter Atom can have multiple **Displays** (for different languages) and can also contain nested sub-chapters.

Using Chapters
~~~~~~~~~~~~~~

There are two primary ways to work with chapters in `pymkv`.

Simple Chapters
^^^^^^^^^^^^^^^

For basic use cases, you can use the `add_simple_chapter` helper method. This is the easiest way to add a sequence of chapters to a file.

.. code-block:: python

    from pymkv.chapters import Chapters, ChapterAtom

    # Create and export
    chapters = Chapters()
    chapters.add_simple_chapter("00:00:00.000", "Intro")
    xml = export_to_xml(chapters)

You can also add chapters directly to an `MKVFile` object:

.. code-block:: python

    from pymkv import MKVFile
    from pymkv.chapters import ChapterAtom, ChapterDisplay

    mkv = MKVFile()

    # Add simple chapter directly
    atom = ChapterAtom(
        time_start="00:00:00.000",
        displays=[ChapterDisplay(string="Intro")]
    )
    mkv.add_chapter(atom)

Complex Nested Chapters
^^^^^^^^^^^^^^^^^^^^^^^

For more advanced scenarios, such as nested chapters, you can build the structure manually.

.. code-block:: python

    from pymkv.chapters import Chapters, ChapterAtom, ChapterDisplay, EditionEntry

    # Create the container
    chapters = Chapters()

    # Create complex nested chapters
    display = ChapterDisplay(string="Nested Chapter", language="eng")
    atom = ChapterAtom(time_start="00:05:00.000", displays=[display])

    parent = ChapterAtom(time_start="00:01:00.000", atoms=[atom])

    # Add to manually created edition
    edition = EditionEntry(atoms=[parent])
    chapters.editions.append(edition)

API Reference
~~~~~~~~~~~~~

.. automodule:: pymkv.chapters
    :noindex:

.. autoclass:: pymkv.chapters.Chapters
    :members:
    :undoc-members:

.. autoclass:: pymkv.chapters.ChapterAtom
    :members:
    :undoc-members:

.. autoclass:: pymkv.chapters.ChapterDisplay
    :members:
    :undoc-members:

.. autoclass:: pymkv.chapters.EditionEntry
    :members:
    :undoc-members:

Module Functions
~~~~~~~~~~~~~~~~

.. autofunction:: pymkv.chapters.export_to_xml
