Luminal Deployment
==================

`pipeworks-namegen-lexicon` is now a real hosted development surface on
``luminal.local``, not just a clone-only repo.

This page records the live creator-workbench and names-app shapes on Luminal so
future changes to nginx, ``systemd``, config paths, or local TLS can be made
from verified context instead of memory.

Current Host Shape
------------------

Current live lexicon-hosted deployment:

- repo:
  - ``/srv/work/pipeworks/repos/pipeworks-namegen-lexicon``
- venv:
  - ``/srv/work/pipeworks/venvs/pw-namegen-lexicon``
- live config:
  - ``/etc/pipeworks/namegen-lexicon/server.ini``
- config staging/source area:
  - ``/srv/work/pipeworks/config/namegen-lexicon``
- runtime data:
  - ``/srv/work/pipeworks/runtime/namegen-lexicon/output``
  - ``/srv/work/pipeworks/runtime/namegen-lexicon/sessions``
- localhost backend:
  - ``127.0.0.1:8370``
- ``systemd`` unit:
  - ``pipeworks-namegen-lexicon.service``
- HTTPS hostname:
  - ``creator.pipeworks.luminal.local``

This hostname was chosen deliberately so the creator workbench does not consume
the most generic future-facing PipeWorks user hostname.

Current live names-app deployment:

- repo:
  - ``/srv/work/pipeworks/repos/pipeworks-namegen-lexicon``
- venv:
  - ``/srv/work/pipeworks/venvs/pw-namegen-lexicon``
- live config:
  - ``/etc/pipeworks/namegen-lexicon/names.ini``
- config staging/source area:
  - ``/srv/work/pipeworks/config/namegen-lexicon``
- localhost backend:
  - ``127.0.0.1:8380``
- ``systemd`` unit:
  - ``pipeworks-namegen-names.service``
- HTTPS hostname:
  - ``names.pipeworks.luminal.local``

The names app is a consumer-facing generation and favorites UI backed by the
runtime API. It remains separate from the creator workbench even though both
apps live in the same repo and service venv.

Local Config
------------

The workbench now prefers the ``[creator_workbench]`` section name.

Current live config shape:

.. code-block:: ini

   [creator_workbench]
   bind_host = 127.0.0.1
   port = 8370
   verbose = false
   output_base = /srv/work/pipeworks/runtime/namegen-lexicon/output
   sessions_dir = /srv/work/pipeworks/runtime/namegen-lexicon/sessions

Two practical consequences matter:

- ``bind_host`` should stay ``127.0.0.1`` for the host-managed deployment
  model, with nginx as the public entrypoint.
- mutable output and session state should live in host-owned runtime
  directories, not inside the repo checkout.

Current live names-app config shape:

.. code-block:: ini

   [names_app]
   bind_host = 127.0.0.1
   port = 8380
   verbose = false
   api_base_url = http://127.0.0.1:8360

systemd Service
---------------

Current service unit:

- ``/etc/systemd/system/pipeworks-namegen-lexicon.service``

Current shape:

.. code-block:: ini

   [Unit]
   Description=Pipeworks Namegen Lexicon Creator Workbench
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=pipeworks
   Group=pipeworks
   WorkingDirectory=/srv/work/pipeworks/repos/pipeworks-namegen-lexicon
   Environment=PYTHONUNBUFFERED=1
   ExecStart=/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/pipeworks-namegen-lexicon-web --config /etc/pipeworks/namegen-lexicon/server.ini
   Restart=on-failure
   RestartSec=3
   NoNewPrivileges=true
   PrivateTmp=true
   ProtectSystem=full
   ProtectHome=true
   ReadWritePaths=/srv/work/pipeworks/runtime/namegen-lexicon

   [Install]
   WantedBy=multi-user.target

This mirrors the current API deployment pattern closely while pointing at the
creator-workbench entrypoint rather than an API module.

Current names-app service unit:

- ``/etc/systemd/system/pipeworks-namegen-names.service``

Current shape:

.. code-block:: ini

   [Unit]
   Description=Pipeworks Names App
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=pipeworks
   Group=pipeworks
   WorkingDirectory=/srv/work/pipeworks/repos/pipeworks-namegen-lexicon
   Environment=PYTHONUNBUFFERED=1
   ExecStart=/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/pipeworks-namegen-names-web --config /etc/pipeworks/namegen-lexicon/names.ini
   Restart=on-failure
   RestartSec=3
   NoNewPrivileges=true
   PrivateTmp=true
   ProtectSystem=full
   ProtectHome=true

   [Install]
   WantedBy=multi-user.target

nginx
-----

The creator workbench is not API-only. nginx must proxy the full application
surface:

- ``/``
- ``/static/``
- ``/api/``

Current nginx template source:

- ``/srv/work/pipeworks/config/namegen-lexicon/creator.pipeworks.luminal.local.nginx.conf``

Current live vhost paths:

- ``/etc/nginx/sites-available/creator.pipeworks.luminal.local``
- ``/etc/nginx/sites-enabled/creator.pipeworks.luminal.local``

Current shape:

.. code-block:: nginx

   server {
       listen 80;
       server_name creator.pipeworks.luminal.local;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl;
       server_name creator.pipeworks.luminal.local;

       ssl_certificate     /etc/nginx/certs/creator.pipeworks.luminal.local.pem;
       ssl_certificate_key /etc/nginx/certs/creator.pipeworks.luminal.local-key.pem;

       access_log /var/log/nginx/creator.pipeworks.luminal.local.access.log;
       error_log  /var/log/nginx/creator.pipeworks.luminal.local.error.log;

       include /etc/nginx/snippets/security-headers.conf;
       include /etc/nginx/snippets/proxy-common.conf;
       include /etc/nginx/snippets/proxy-timeouts.conf;

       location / {
           proxy_pass http://127.0.0.1:8370;
       }
   }

Unlike ``namegen-api.luminal.local``, this vhost intentionally proxies the
whole app because the creator workbench is a browser application with an
embedded JSON API.

Current names-app nginx template source:

- ``/srv/work/pipeworks/config/namegen-lexicon/names.pipeworks.luminal.local.nginx.conf``

Current live names-app vhost paths:

- ``/etc/nginx/sites-available/names.pipeworks.luminal.local``
- ``/etc/nginx/sites-enabled/names.pipeworks.luminal.local``

Current shape:

.. code-block:: nginx

   server {
       listen 80;
       server_name names.pipeworks.luminal.local;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl;
       server_name names.pipeworks.luminal.local;

       ssl_certificate     /etc/nginx/certs/names.pipeworks.luminal.local.pem;
       ssl_certificate_key /etc/nginx/certs/names.pipeworks.luminal.local-key.pem;

       access_log /var/log/nginx/names.pipeworks.luminal.local.access.log;
       error_log  /var/log/nginx/names.pipeworks.luminal.local.error.log;

       include /etc/nginx/snippets/security-headers.conf;
       include /etc/nginx/snippets/proxy-common.conf;
       include /etc/nginx/snippets/proxy-timeouts.conf;

       location / {
           proxy_pass http://127.0.0.1:8380;
       }
   }

The names app is also a browser application, so nginx proxies the whole app
surface rather than only ``/api/``.

mkcert and Local TLS
--------------------

Luminal uses ``mkcert`` for local development TLS.

The working pattern for both lexicon-hosted apps is:

1. mint the leaf certificate for the hostname
2. install the cert and key under ``/etc/nginx/certs``
3. reload nginx
4. make sure the issuing local root CA is trusted by the machine that is
   performing verification

Useful issuance pattern:

.. code-block:: bash

   cd /tmp
   sudo mkcert creator.pipeworks.luminal.local
   sudo mkcert names.pipeworks.luminal.local

Operational lesson from the rollout:

- the first ``creator`` certificate was minted from a different mkcert CA than
  the one already trusted on Luminal
- browser access and curl trust can diverge if the wrong local CA is used
- the correct fix was to recreate the leaf certificate with the same trusted
  root-owned mkcert CA already used by the existing PipeWorks local certs

Current live names-app certificate paths:

- ``/etc/nginx/certs/names.pipeworks.luminal.local.pem``
- ``/etc/nginx/certs/names.pipeworks.luminal.local-key.pem``

Useful verification commands:

.. code-block:: bash

   openssl x509 -in /etc/nginx/certs/creator.pipeworks.luminal.local.pem -noout -issuer -subject -dates
   openssl x509 -in /etc/nginx/certs/names.pipeworks.luminal.local.pem -noout -issuer -subject -dates
   curl -I https://creator.pipeworks.luminal.local/
   curl -I https://names.pipeworks.luminal.local/
   curl -I https://namegen-api.luminal.local/

If ``curl`` fails with a local issuer error while other local sites work,
compare the issuer on the creator leaf against the issuer used by the already
trusted PipeWorks certificates.

HTTP Behavior
-------------

The workbench originally returned ``501 Unsupported method ('HEAD')`` when
checked with ``curl -I`` because the stdlib server handled ``GET`` and
``POST`` but had no ``HEAD`` implementation.

The server now implements ``HEAD`` by reusing the same route handling as
``GET`` while suppressing the response body. That means:

- browser behavior was always fine
- but ``curl -I`` and similar probe-style checks now work correctly as well

Ownership Model
---------------

The working ownership split on Luminal is:

- repo workspace:
  - ``/srv/work/pipeworks/repos``
  - ``aapark:pipeworks``
  - setgid
- service/runtime/config staging:
  - ``/srv/work/pipeworks/config``
  - ``/srv/work/pipeworks/runtime``
  - ``pipeworks:pipeworks``
- service venvs:
  - ``pipeworks:pipeworks``
- live ``/etc/pipeworks/...`` config:
  - root-owned

That split matters. Repo source is developer-managed; service config and
runtime state are host-managed.

Verification
------------

Useful checks for the live workbench:

.. code-block:: bash

   systemctl status pipeworks-namegen-lexicon.service
   systemctl status pipeworks-namegen-names.service
   curl http://127.0.0.1:8370/api/settings
   curl -I http://127.0.0.1:8370/
   curl -I https://creator.pipeworks.luminal.local/
   curl http://127.0.0.1:8380/api/app-config
   curl -I http://127.0.0.1:8380/
   curl -I https://names.pipeworks.luminal.local/

If localhost succeeds but HTTPS fails, the likely problem is nginx or local
certificate handling rather than the Python backend itself.
