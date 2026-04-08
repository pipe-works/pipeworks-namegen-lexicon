# pipeworks-namegen-lexicon

`pipeworks-namegen-lexicon` is the home of the human-facing PipeWorks web apps.

It owns the corpus-to-lexicon side of the system: extraction, normalization,
annotation, exploratory syllable walking, candidate generation, selection, and
package building for downstream runtime import. It also now owns the first
consumer-facing `names` app implementation for people who want to play with
prepared package data without entering the creator workflow.

This repository is not just a preprocessing bucket. It is the place where
phonetic space becomes playable. The central idea is not "generate more names
like this corpus" but "explore the conditions that make new names emerge."

## Repository Role

PipeWorks currently has three main name-generation repositories:

- `pipeworks-namegen-core`
  - pure deterministic library code
  - owns rendering helpers and generation primitives
  - owns no HTTP, SQLite, UI, or deployment contract
- `pipeworks-namegen-api`
  - canonical runtime contract and runtime service boundary
  - imports package artifacts into its own service-owned SQLite store
  - serves runtime generation over HTTP at `namegen-api.luminal.local`
- `pipeworks-namegen-lexicon`
  - creator/research environment and package-authoring surface
  - owns the browser-based creator workbench
  - owns the consumer-facing names app
  - exports package artifacts for API import

The important boundary is that `lexicon` does not own runtime package serving.
It prepares, explores, and exports the material that the runtime API later
imports and serves.

## What Is Novel Here

This repository centers on phonetic feature walks rather than simple frequency
reuse or Markov-style imitation. Source names are split into syllables,
annotated with explicit phonetic features, and then explored as a navigable
space.

That creates a different creative workflow:

- not "sample the most common outputs"
- but "shape the conditions that produce interesting outputs"
- not "retrain and hope"
- but "walk, compare, combine, and listen for what emerges"

The web surface is therefore a workbench, not a toy demo. It is an instrument
for exploring corpora, comparing patches, generating candidate pools, and
building reusable package artifacts.

## Main Capabilities

This repo currently owns:

- corpus extraction from raw source text
- normalization and feature annotation
- corpus SQLite build steps for fast loading and repeatable runs
- phonetic-space walking and profile-based exploration
- candidate generation and name-class selection
- package export for downstream API import
- browser-based creator workflow via `build_tools.syllable_walk_web`
- browser-based consumer workflow via `build_tools.names_web`

The maintained web surfaces now intentionally split into two distinct apps:

- creator workflows for building and refining lexicon material
- consumer workflows for generating names from prepared package data and
  managing favorites

They live in one repo because they share Pipe-Works identity, package context,
and author-to-consumer product continuity, but they are no longer being framed
as one muddled UI surface.

## Creator Workbench

The main interactive surface is the creator workbench implementation at
`build_tools.syllable_walk_web`.

It combines:

- a `Pipeline` view for extraction, normalization, annotation, and database runs
- a `Walker` view for dual-patch corpus loading, feature walks, combining,
  selection, analysis, rendering, and packaging

The current implementation includes:

- run discovery from manifest-backed output directories
- patch A / patch B side-by-side comparison
- named walk profiles and custom walk parameters
- candidate generation in flat or walk-based modes
- selection policies such as `first_name`, `last_name`, and `place_name`
- package export as ZIP plus companion metadata persisted under
  `<output_base>/packages/`

The maintained workbench is web-first. The old TUI-heavy workflow from the
monolith era was intentionally retired from the supported product shape here.

## Names App

The first consumer-facing names app now exists as:

- `build_tools.names_web`

This is the deliberately simpler Pipe-Works surface for people working with
prepared package data. It is not the place for corpus ingestion, syllable
annotation, or package import administration.

The first implementation keeps the scope narrow:

- package-backed generation by class, package, and syllable mode
- live preview of generated names
- first + last combination preview
- favorites save/list/delete flows
- concise user-facing help

Important boundary:

- the names app owns the consumer UX
- `pipeworks-namegen-api` still owns the runtime API contract and favorites
  persistence
- the names app talks to the API rather than re-owning those runtime concerns

The current in-repo implementation uses a small local proxy layer so the
consumer app can be served from its own hostname later without browser CORS
workarounds while still respecting the API boundary.

## Package Boundary

The exported package artifacts from this repo are intended for
`pipeworks-namegen-api`.

At a high level the flow is:

1. Raw corpus material is processed in `pipeworks-namegen-lexicon`.
2. A creator explores patches, profiles, and candidate pools in the web
   workbench.
3. Selected output is packaged as a ZIP plus metadata.
4. `pipeworks-namegen-api` imports that package into its service-owned SQLite
   store.
5. Runtime generation happens from the imported package data through the API.

`pipeworks-namegen-lexicon` therefore owns package creation, but not runtime
package serving.

## Scope

In scope:

- creator-facing lexicon pipeline code under `src/build_tools`
- the browser-based creator workbench
- artifact/package production for downstream runtime import
- analysis modules that support exploration of corpus and feature space

Out of scope:

- runtime HTTP serving of generation packages
- runtime favorites or user-profile state
- the pure deterministic generator boundary owned by `pipeworks-namegen-core`
- retired Textual/TUI surfaces from the monolith era

Transitional note:

- the old consumer-facing UI still temporarily exists in
  `pipeworks-namegen-api`
- that legacy API-embedded UI should eventually be removed once the names app
  is good enough to replace the retained consumer workflows

## PipeWorks on Luminal

The current live PipeWorks workspace on `luminal.local` is:

- root:
  - `/srv/work/pipeworks`
- repos:
  - `/srv/work/pipeworks/repos`
- venvs:
  - `/srv/work/pipeworks/venvs`
- host config:
  - `/srv/work/pipeworks/config`
  - `/etc/pipeworks`
- runtime state:
  - `/srv/work/pipeworks/runtime`

Current name-generation repo/runtime picture:

- `pipeworks-namegen-core`
  - library surface
  - dedicated development venv exists
  - not a hosted service
- `pipeworks-namegen-api`
  - live local development service
  - `systemd` unit: `pipeworks-namegen-api.service`
  - HTTPS hostname: `namegen-api.luminal.local`
- `pipeworks-namegen-lexicon`
  - creator workbench
  - dedicated development and service venv: `pw-namegen-lexicon`
  - HTTPS hostname: `creator.pipeworks.luminal.local`
  - consumer-facing names app also lives here
  - HTTPS hostname: `names.pipeworks.luminal.local`

This repo should now be read as part of a real host-managed multi-repo layout,
not just as a local tool folder.

## App Entry Points

This repository now has two browser-facing app entrypoints:

- creator app:
  - `pipeworks-namegen-lexicon-web`
  - module: `python -m build_tools.syllable_walk_web`
- names app:
  - `pipeworks-namegen-names-web`
  - module: `python -m build_tools.names_web`

Both apps are now hosted on Luminal as separate services backed by the same
repo and service venv.

## Live Creator Workbench Host Model

The creator workbench is now deployed locally on Luminal with nginx as the
canonical front door.

Current live host shape:

- repo:
  - `/srv/work/pipeworks/repos/pipeworks-namegen-lexicon`
- venv:
  - `/srv/work/pipeworks/venvs/pw-namegen-lexicon`
- live config:
  - `/etc/pipeworks/namegen-lexicon/server.ini`
- config staging/source area:
  - `/srv/work/pipeworks/config/namegen-lexicon`
- runtime data:
  - `/srv/work/pipeworks/runtime/namegen-lexicon/output`
  - `/srv/work/pipeworks/runtime/namegen-lexicon/sessions`
- localhost backend:
  - `127.0.0.1:8370`
- `systemd` unit:
  - `pipeworks-namegen-lexicon.service`
- HTTPS hostname:
  - `creator.pipeworks.luminal.local`

The workbench now supports explicit `bind_host` and defaults to `127.0.0.1`,
which matches the intended host model: Python app on localhost, nginx exposed
to the LAN.

## Live Names App Host Model

The names app is now deployed locally on Luminal with nginx as the canonical
front door.

Current live host shape:

- repo:
  - `/srv/work/pipeworks/repos/pipeworks-namegen-lexicon`
- venv:
  - `/srv/work/pipeworks/venvs/pw-namegen-lexicon`
- live config:
  - `/etc/pipeworks/namegen-lexicon/names.ini`
- config staging/source area:
  - `/srv/work/pipeworks/config/namegen-lexicon`
- localhost backend:
  - `127.0.0.1:8380`
- `systemd` unit:
  - `pipeworks-namegen-names.service`
- HTTPS hostname:
  - `names.pipeworks.luminal.local`

The names app is intentionally stateless at the service layer. It serves the
consumer UI locally and proxies only a narrow set of consumer-safe runtime API
calls through to `http://127.0.0.1:8360`.

Current live config shape:

```ini
[names_app]
bind_host = 127.0.0.1
port = 8380
verbose = false
api_base_url = http://127.0.0.1:8360
```

## Live Config Shape

The workbench configuration now prefers a `[creator_workbench]` section in
`server.ini`. Existing `[build_tools]` sections are still understood, but new
or cleaned-up host configuration should use the workbench name directly.

Current live config shape:

```ini
[creator_workbench]
bind_host = 127.0.0.1
port = 8370
verbose = false
output_base = /srv/work/pipeworks/runtime/namegen-lexicon/output
sessions_dir = /srv/work/pipeworks/runtime/namegen-lexicon/sessions
```

Important design point:

- mutable workbench runtime state should live under host-owned runtime
  directories
- not inside the repo checkout

That is the same architectural split already used by the API:

- code in repo
- config in `/etc/pipeworks/...`
- runtime state outside git

## systemd Services

Current service unit:

- `/etc/systemd/system/pipeworks-namegen-lexicon.service`

Current shape:

```ini
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
```

This closely mirrors the API unit style, but points at the creator-workbench
entrypoint instead of an API module.

Current names-app service unit:

- `/etc/systemd/system/pipeworks-namegen-names.service`

Current shape:

```ini
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
```

## nginx Entry Points

The creator workbench is not API-only. nginx must proxy the full app surface:

- `/`
- `/static/`
- `/api/`

Current nginx template source:

- `/srv/work/pipeworks/config/namegen-lexicon/creator.pipeworks.luminal.local.nginx.conf`

Current live vhost path:

- `/etc/nginx/sites-available/creator.pipeworks.luminal.local`
- `/etc/nginx/sites-enabled/creator.pipeworks.luminal.local`

Current shape:

```nginx
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
```

Unlike the API vhost, this one is intentionally full-surface proxying because
the creator workbench is a browser application with an embedded JSON API.

The names app follows the same localhost-plus-nginx pattern with its own vhost.

Current names-app nginx template source:

- `/srv/work/pipeworks/config/namegen-lexicon/names.pipeworks.luminal.local.nginx.conf`

Current live names-app vhost path:

- `/etc/nginx/sites-available/names.pipeworks.luminal.local`
- `/etc/nginx/sites-enabled/names.pipeworks.luminal.local`

Current shape:

```nginx
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
```

The names app is also a browser app, so nginx proxies the whole surface rather
than only `/api/`.

## mkcert and Local TLS

Luminal uses `mkcert` for local development TLS.

For the creator workbench and names app, the working pattern is:

1. mint the leaf cert for the hostname
2. install the cert and key into `/etc/nginx/certs`
3. reload nginx
4. ensure the issuing root CA is trusted by the local machine/client

Important operational lesson from the rollout:

- `creator.pipeworks.luminal.local` initially failed `curl` trust checks even
  though the browser app loaded
- the cause was not nginx itself, but that the first `creator` leaf certificate
  was minted from a different mkcert CA than the one already trusted on
  `luminal`
- the correct fix was to recreate the `creator` leaf with the same root-owned
  mkcert CA used by the existing PipeWorks local certs

Current live names-app certificate paths are:

- `/etc/nginx/certs/names.pipeworks.luminal.local.pem`
- `/etc/nginx/certs/names.pipeworks.luminal.local-key.pem`

Useful issuance pattern:

```bash
cd /tmp
sudo mkcert creator.pipeworks.luminal.local
sudo mkcert names.pipeworks.luminal.local
```

Then copy the generated cert/key pairs into `/etc/nginx/certs`, keep the cert
world-readable, keep the key root-readable only, test with `nginx -t`, and
reload nginx.

Useful verification commands:

```bash
openssl x509 -in /etc/nginx/certs/creator.pipeworks.luminal.local.pem -noout -issuer -subject -dates
openssl x509 -in /etc/nginx/certs/names.pipeworks.luminal.local.pem -noout -issuer -subject -dates
curl -I https://creator.pipeworks.luminal.local/
curl -I https://names.pipeworks.luminal.local/
curl -I https://namegen-api.luminal.local/
```

If `curl` fails with local issuer problems on Luminal, compare the issuer on
the `creator` leaf against the issuer used by the already-working local
PipeWorks certs.

## HTTP Notes

The creator workbench originally returned `501 Unsupported method ('HEAD')`
when checked with `curl -I`.

That was because the stdlib HTTP server handled `GET` and `POST` but had no
`HEAD` implementation. The server has now been updated so `HEAD` reuses the
same routing as `GET` while suppressing the body.

That means:

- browser behavior was always fine
- but health-style checks using `curl -I` now behave correctly as well

## Development

Create a dedicated environment:

```bash
python3 -m venv /srv/work/pipeworks/venvs/pw-namegen-lexicon
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m pip install -U pip
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m pip install -e ".[dev,docs]"
```

Common commands:

```bash
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m pytest -q
RUFF_CACHE_DIR=/tmp/pw-namegen-lexicon-ruff-cache /srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m ruff check src tests
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.syllable_walk_web --help
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m build_tools.names_web --help
cd docs && make clean html
```

## Service-Oriented Local Checks

Useful local checks now that the creator workbench is host-managed on Luminal:

```bash
systemctl status pipeworks-namegen-lexicon.service
systemctl status pipeworks-namegen-names.service
curl http://127.0.0.1:8370/api/settings
curl -I http://127.0.0.1:8370/
curl -I https://creator.pipeworks.luminal.local/
curl http://127.0.0.1:8380/api/app-config
curl -I http://127.0.0.1:8380/
curl -I https://names.pipeworks.luminal.local/
```

If HTTPS fails but localhost succeeds, the likely problem is:

- nginx config
- missing cert files
- mkcert trust mismatch

not the Python backend itself.

## Ownership Model on Luminal

The working ownership split is:

- repo workspace:
  - `/srv/work/pipeworks/repos`
  - `aapark:pipeworks`
  - setgid
- service/runtime/config staging:
  - `/srv/work/pipeworks/config`
  - `/srv/work/pipeworks/runtime`
  - `pipeworks:pipeworks`
- service venvs:
  - `pipeworks:pipeworks`
- live `/etc/pipeworks/...` config:
  - root-owned

That split matters. Repo source is developer-managed; service config and
runtime state are host-managed.

## Working Principles

This repository is healthiest when it stays explicit about its role:

- it is the place to explore and shape phonetic possibility space
- it is the place to build reusable lexicon artifacts
- it is the creator-facing PipeWorks browser workbench
- it is also the home of the consumer-facing names app
- it is not the canonical runtime contract
- it does not own runtime API behavior even when it owns consumer UI

If a change is primarily about runtime serving, HTTP contract semantics, or
service-owned generation state, it probably belongs in `pipeworks-namegen-api`
instead.

If a change is primarily about deterministic generator primitives, it probably
belongs in `pipeworks-namegen-core`.
