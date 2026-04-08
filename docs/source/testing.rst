Testing
=======

The lexicon repository has a large automated test surface because it covers both
pipeline behavior and the maintained web workbench.

What is covered
---------------

The test suite exercises:

- extraction and normalization behavior
- corpus and SQLite build paths
- syllable walking and reach calculations
- candidate combination and policy-based selection
- web API handlers and workbench services
- run discovery, session handling, and package generation

Run the suite
-------------

Use the dedicated lexicon virtual environment:

.. code-block:: bash

   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m pytest -q

Repository note
---------------

Some tests create `_working/output` style fixtures under the repository. In a
normal local environment that is expected. In restricted sandboxed sessions,
those tests may fail for filesystem reasons even when the code is correct.

At the time of the current docs pass, the full suite completed successfully in a
normal writable environment.
