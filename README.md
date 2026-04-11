[![CI](https://github.com/pipe-works/pipeworks-namegen-lexicon/actions/workflows/ci.yml/badge.svg)](https://github.com/pipe-works/pipeworks-namegen-lexicon/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/pipe-works/pipeworks-namegen-lexicon/branch/main/graph/badge.svg)](https://codecov.io/gh/pipe-works/pipeworks-namegen-lexicon)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# pipeworks-namegen-lexicon

`pipeworks-namegen-lexicon` is the creator and exploration side of the
PipeWorks name-generation stack. It owns corpus processing, syllable and
feature analysis, candidate exploration, package authoring, and the browser
applications used to work with prepared name data.

## PipeWorks Workspace

These repositories are designed to live inside a shared PipeWorks workspace
rooted at `/srv/work/pipeworks`.

- `repos/` contains source checkouts only.
- `venvs/` contains per-project virtual environments such as `pw-mud-server`.
- `runtime/` contains mutable runtime state such as databases, exports, session
  files, and caches.
- `logs/` contains service-owned log output when a project writes logs outside
  the process manager.
- `config/` contains workspace-level configuration files that should not be
  treated as source.
- `bin/` contains optional workspace helper scripts.
- `home/` is reserved for workspace-local user data when a project needs it.

Across the PipeWorks ecosphere, the rule is simple: keep source in `repos/`,
keep mutable state outside the repo checkout, and use explicit paths between
repos when one project depends on another.

## What This Repo Owns

This repository is the source of truth for:

- corpus ingestion, normalization, and feature annotation tooling
- syllable-walk and phonetic-space exploration tooling
- creator-facing package authoring workflows
- the creator workbench web app
- the consumer-facing names web app

This repository does not own:

- the pure deterministic runtime-library boundary
- the canonical runtime HTTP contract
- service-owned runtime package storage

## Relationship To The Other Namegen Repos

- `pipeworks-namegen-core`
  deterministic generation/rendering primitives
- `pipeworks-namegen-api`
  canonical runtime HTTP contract and service-owned persistence
- `pipeworks-namegen-lexicon`
  creator workflows, package authoring, and consumer-facing web apps

The important boundary is that this repo prepares and exports package material;
it does not own the runtime API that serves imported package data.

## Main Surfaces

### Creator Workbench

The creator workbench lives in `build_tools.syllable_walk_web` and combines:

- pipeline flows for extraction, normalization, annotation, and corpus DB runs
- walker flows for dual-patch exploration, profile-based walks, and candidate
  generation
- package export workflows for downstream API import

Its CLI entry point is:

- `pipeworks-namegen-lexicon-web`

### Names App

The consumer-facing names app lives in `build_tools.names_web`.

It provides a simpler surface for working with prepared package data while
respecting the API boundary owned by `pipeworks-namegen-api`.

Its CLI entry point is:

- `pipeworks-namegen-names-web`

## Repository Layout

- `src/build_tools/` corpus pipeline, analysis tools, web apps, and packaging
  workflows
- `src/pipeworks_namegen_lexicon/` package metadata surface
- `tests/` pytest coverage across pipeline, analysis, CLI, and web behavior
- `docs/` project documentation

## Quick Start

### Requirements

- Python `>=3.12`
- a PipeWorks workspace rooted at `/srv/work/pipeworks`
- Git access to the private `pipeworks-ipc` dependency referenced by
  `pyproject.toml`

### Install

```bash
python3 -m venv /srv/work/pipeworks/venvs/pw-namegen-lexicon
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/pip install -e ".[dev]"
```

### Suggested Workspace Runtime Paths

For workspace-backed local runs, keep generated output outside the repo
checkout where practical, for example:

- `/srv/work/pipeworks/runtime/namegen-lexicon/output`
- `/srv/work/pipeworks/runtime/namegen-lexicon/sessions`

The creator workbench can read those paths via its INI config or CLI overrides.

### Run The Creator Workbench

```bash
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/pipeworks-namegen-lexicon-web \
  --output-base /srv/work/pipeworks/runtime/namegen-lexicon/output \
  --sessions-dir /srv/work/pipeworks/runtime/namegen-lexicon/sessions \
  --bind-host 127.0.0.1
```

### Run The Names App

```bash
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/pipeworks-namegen-names-web \
  --api-base-url http://127.0.0.1:8360 \
  --bind-host 127.0.0.1
```

Both apps also accept `--config server.ini` and read repo-local INI settings
when present.

## Package Boundary

The normal package flow is:

1. prepare or inspect corpus material in this repo
2. generate candidates and select output classes
3. export package artifacts from the creator workbench
4. import those artifacts into `pipeworks-namegen-api`
5. serve runtime generation through the API layer

That means package creation belongs here, while runtime package serving does
not.

## Validation And Development

Run the main checks from the repo root:

```bash
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/pytest
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/ruff check src tests
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/black --check src tests
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/mypy src
```

If you need the docs toolchain:

```bash
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/pip install -e ".[docs]"
make -C docs html
```

## Documentation

Additional documentation lives in `docs/`.

## License

[GPL-3.0-or-later](LICENSE)
