Repository Philosophy
=====================

This repository exists to make phonetic possibility space explorable.

The central idea is not simple corpus imitation. PipeWorks lexicon work takes
source text, splits it into syllables, annotates those syllables with explicit
features, and then treats the resulting corpus as a navigable space. The point
is to discover conditions that produce interesting names, not merely to replay
the most common source patterns.

Why this repository exists
--------------------------

`pipeworks-namegen-lexicon` is where the novel part of the system lives:

- corpus preparation
- feature annotation
- phonetic-space walking
- side-by-side patch comparison
- candidate generation and selection
- package authoring for downstream runtime import

The creator workbench is therefore a research and authorship surface, not just
an internal preprocessor.

Why the maintained surface is web-first
---------------------------------------

Earlier versions of the project explored both TUI and web interfaces. The
current repository intentionally retires the TUI applications and keeps the web
workbench as the maintained surface.

That decision keeps the product coherent:

- one interactive creator environment instead of two parallel UI stacks
- browser-based access to the full pipeline and walker workflow
- less duplicated maintenance around state, controls, and export paths

Retiring the TUI does not reduce the ambition of the project. It narrows the
maintained surface so the creator workbench can mature in one place.

Repository Boundary
-------------------

The PipeWorks name-generation system is split across three repositories:

- `pipeworks-namegen-core`
  Pure deterministic library code. No UI, no runtime HTTP service, no package
  storage.
- `pipeworks-namegen-api`
  Canonical runtime contract and package-backed HTTP service. Owns import and
  serving of package data at runtime.
- `pipeworks-namegen-lexicon`
  Creator/research environment and package-authoring surface.

If a change is mainly about runtime serving, API payload validation, or
service-owned state, it should usually land in `pipeworks-namegen-api`, not
here.
