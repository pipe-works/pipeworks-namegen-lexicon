Development
===========

Environment
-----------

Use the dedicated lexicon virtual environment:

.. code-block:: bash

   python3 -m venv /srv/work/pipeworks/venvs/pw-namegen-lexicon
   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m pip install -U pip
   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m pip install -e ".[dev,docs]"

Common Commands
---------------

.. code-block:: bash

   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m pytest -q
   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.syllable_walk_web --help
   cd docs && make clean html

CLI Entry Point
---------------

The maintained web surface is exposed through the project script:

.. code-block:: bash

   pipeworks-namegen-lexicon-web --help

Or directly as a module:

.. code-block:: bash

   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.syllable_walk_web --help

Documentation Scope
-------------------

This documentation set intentionally documents the maintained repository shape:

- the creator-facing workbench
- the repository boundary
- package flow into the runtime API

It does not attempt to recreate the full documentation tree of the archived
monolith, especially for retired TUI surfaces.
