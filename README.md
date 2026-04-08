# pipeworks-namegen-lexicon

`pipeworks-namegen-lexicon` is the creator-facing PipeWorks workbench.

It owns the corpus-to-lexicon side of the system: extraction, normalization,
annotation, exploratory syllable walking, candidate generation, selection, and
package building for downstream runtime import.

This repository is not just a preprocessing bucket. It is the place where
phonetic space becomes playable. The central idea is not "generate more names
like this corpus" but "explore the conditions that make new names emerge."

## Repository Role

PipeWorks is split into three main name-generation repositories:

- `pipeworks-namegen-core`: pure deterministic library code.
- `pipeworks-namegen-api`: canonical runtime contract and package-backed HTTP
  service.
- `pipeworks-namegen-lexicon`: creator/research environment and package-authoring
  surface.

The important boundary is that `lexicon` does not serve runtime generation to
end users. It prepares, explores, and exports the material that the runtime API
later imports and serves.

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

The workbench combines two closely related activities:

- creator workflows for building and refining lexicon material
- exploratory generation workflows for interacting with prepared material while
  still inside the authoring environment

Those belong together here because they inform each other directly.

## Syllable Walk Web

The main interactive surface is `build_tools.syllable_walk_web`.

It combines:

- a Pipeline view for extraction, normalization, annotation, and database runs
- a Walker view for dual-patch corpus loading, feature walks, combining,
  selection, analysis, rendering, and packaging

The current implementation includes:

- run discovery from manifest-backed output directories
- patch A / patch B side-by-side comparison
- named walk profiles and custom walk parameters
- candidate generation in flat or walk-based modes
- selection policies such as `first_name`, `last_name`, and `place_name`
- package export as ZIP plus companion metadata persisted under
  `<output_base>/packages/`

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
- the browser-based syllable walk workbench
- artifact/package production for downstream runtime import
- analysis modules that support exploration of corpus and feature space

Out of scope:

- runtime HTTP serving and deployment of generation packages
- runtime favorites or user-profile state
- the pure deterministic generator boundary owned by `pipeworks-namegen-core`
- retired Textual/TUI surfaces from the monolith era

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
/srv/work/pipeworks/venvs/pw-namegen-lexicon/bin/python -m \
  build_tools.syllable_walk_web --help
cd docs && make clean html
```

## Working Principles

This repository is healthiest when it stays explicit about its role:

- it is the place to explore and shape phonetic possibility space
- it is the place to build reusable lexicon artifacts
- it is not the canonical runtime contract
- it is not the end of the deployment chain

If a change is primarily about runtime serving, HTTP contract semantics, or
service-owned state, it probably belongs in `pipeworks-namegen-api` instead.
