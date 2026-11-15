Languages
---------

The ``pymkv.Languages`` module provides a normalized API for comparing and
translating language codes across ISO 639-1, /B, /T, 639-3, BCP 47, and
English language names. It backs the lenient :class:`~pymkv.MKVTrack`
``language`` setter and the :meth:`~pymkv.MKVTrack.matches_language`
convenience helper.

The authoritative source for "what mkvmerge accepts" is
``mkvmerge --list-languages`` (loaded once per process via
``_load_mkvmerge_table``). ``python-iso639`` provides the offline fallback
and resolves /T-variant codes that mkvmerge does not emit.

.. autofunction:: pymkv.get_iso639_2

.. autofunction:: pymkv.normalize_language

.. autofunction:: pymkv.is_known_language

.. autofunction:: pymkv.language_equivalents

.. autofunction:: pymkv.languages_match
