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
   RUFF_CACHE_DIR=/tmp/pw-namegen-lexicon-ruff-cache /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m ruff check src tests
   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.syllable_walk_web --help
   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.names_web --help
   cd docs && make clean html

CLI Entry Point
---------------

The maintained creator app is exposed through the project script:

.. code-block:: bash

   pipeworks-namegen-lexicon-web --help

Or directly as a module:

.. code-block:: bash

   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.syllable_walk_web --help

The module looks for ``[creator_workbench]`` in ``server.ini`` first and
falls back to ``[build_tools]`` for older local configs.

For host-managed Luminal deployment, the live config currently lives at:

- ``/etc/pipeworks/namegen-lexicon/server.ini``

and uses a localhost bind:

.. code-block:: ini

   [creator_workbench]
   bind_host = 127.0.0.1
   port = 8370
   verbose = false
   output_base = /srv/work/pipeworks/runtime/namegen-lexicon/output
   sessions_dir = /srv/work/pipeworks/runtime/namegen-lexicon/sessions

This keeps nginx as the canonical entrypoint and keeps mutable state outside
the repo checkout.

The names app has its own entrypoint:

.. code-block:: bash

   pipeworks-namegen-names-web --help
   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.names_web --help

The names app is now also host-promoted on Luminal. Its live hostname is
``names.pipeworks.luminal.local`` and its live config currently lives at:

- ``/etc/pipeworks/namegen-lexicon/names.ini``

Current live config shape:

.. code-block:: ini

   [names_app]
   bind_host = 127.0.0.1
   port = 8380
   verbose = false
   api_base_url = http://127.0.0.1:8360

Like the creator workbench, the names app binds only to localhost and relies
on nginx plus mkcert-backed TLS for LAN/browser access.

Documentation Scope
-------------------

This documentation set intentionally documents the maintained repository shape:

- the creator-facing workbench
- the repository boundary
- package flow into the runtime API

It does not attempt to recreate the full documentation tree of the archived
monolith, especially for retired TUI surfaces.
