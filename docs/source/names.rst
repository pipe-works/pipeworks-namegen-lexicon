Names App
=========

The second human-facing web surface in this repository is the consumer-facing
names app at ``build_tools.names_web``.

This app exists so the Pipe-Works consumer experience can leave the API repo
without dragging runtime ownership, import tooling, or database-admin baggage
along with it.

Role
----

The names app is intentionally narrower than the creator workbench.

It is for:

- generating names from prepared package data
- selecting class, package, and syllable mode
- previewing generated names
- building simple first + last combinations
- managing favorites through the existing runtime API

It is not for:

- corpus ingestion
- exploratory syllable walking
- package authoring
- import/browser administration
- direct runtime database maintenance

Boundary
--------

The names app does not replace the runtime API. It depends on it.

The working split is:

- ``pipeworks-namegen-lexicon``
  - owns the consumer UI
- ``pipeworks-namegen-api``
  - owns generation endpoints, favorites persistence, and the runtime service boundary

The current implementation keeps that split explicit by serving a local
consumer app and proxying only the consumer-safe API routes needed for the
first pass.

First-pass scope
----------------

The first implementation intentionally keeps the app small:

- ``Generate``
  - queue one or more prepared selections
  - generate preview names
  - derive first + last combinations
- ``Favorites``
  - list saved names
  - delete saved names
- ``Help``
  - concise guidance for the consumer flow

This is enough to establish a clean product home outside the API repo without
trying to migrate every legacy UI surface at once.

Implementation
--------------

The current names app includes:

- ``build_tools.names_web.cli``
  - names-app configuration and CLI entrypoint
- ``build_tools.names_web.server``
  - stdlib HTTP server and narrow API proxy layer
- ``build_tools.names_web.static``
  - packaged frontend assets for the consumer app

The shared Pipe-Works design language is reused intentionally:

- the names app serves shared base and font assets from the creator-workbench
  bundle
- the consumer app therefore keeps one visual identity with the creator app
  while remaining a separate product surface

Entry points
------------

Project script:

.. code-block:: bash

   pipeworks-namegen-names-web --help

Module entrypoint:

.. code-block:: bash

   /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.names_web --help

Live host shape
---------------

The names app is now live on Luminal at:

- ``names.pipeworks.luminal.local``

This keeps the three active surfaces clear:

- ``creator.pipeworks.luminal.local``
  - creator workbench
- ``names.pipeworks.luminal.local``
  - consumer names app
- ``namegen-api.luminal.local``
  - runtime API

Current host-managed deployment shape:

- repo:
  - ``/srv/work/pipeworks/repos/pipeworks-namegen-lexicon``
- venv:
  - ``/srv/work/pipeworks/venvs/pw-namegen-lexicon``
- live config:
  - ``/etc/pipeworks/namegen-lexicon/names.ini``
- localhost backend:
  - ``127.0.0.1:8380``
- ``systemd`` unit:
  - ``pipeworks-namegen-names.service``
- nginx vhost:
  - ``/etc/nginx/sites-enabled/names.pipeworks.luminal.local``
- nginx template source:
  - ``/srv/work/pipeworks/config/namegen-lexicon/names.pipeworks.luminal.local.nginx.conf``
- cert:
  - ``/etc/nginx/certs/names.pipeworks.luminal.local.pem``
  - ``/etc/nginx/certs/names.pipeworks.luminal.local-key.pem``

Current live config shape:

.. code-block:: ini

   [names_app]
   bind_host = 127.0.0.1
   port = 8380
   verbose = false
   api_base_url = http://127.0.0.1:8360

The names app stays intentionally thin at the service layer. It serves the
consumer UI locally and proxies only the consumer-safe runtime routes needed
for generation preview and favorites flows.

Luminal uses ``mkcert`` for the local TLS leaf certificate on this hostname.
The working pattern is to mint the leaf with ``sudo mkcert
names.pipeworks.luminal.local``, install the generated PEM/key pair under
``/etc/nginx/certs``, then test and reload nginx.
