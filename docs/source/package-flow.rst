Package Flow
============

`pipeworks-namegen-lexicon` prepares package artifacts for
`pipeworks-namegen-api`.

The important boundary is that this repository creates packages, while the API
repository imports and serves them at runtime.

End-to-End Flow
---------------

The normal flow looks like this:

1. Raw source text is processed through extraction, normalization, annotation,
   and database-building stages.
2. A creator loads one or more runs into the walker workbench.
3. Patch A and Patch B can be compared, walked, combined, filtered, and
   selected.
4. The chosen material is exported as a ZIP package plus companion metadata.
5. `pipeworks-namegen-api` imports that package into its service-owned SQLite
   store.
6. Runtime clients generate names through the API from imported package data.

Package Output
--------------

The workbench can persist package artifacts under
``<output_base>/packages/``.

The package builder currently emits:

- a downloadable ZIP archive
- an embedded ``manifest.json`` inside the ZIP
- a companion ``_metadata.json`` file written to disk for provenance

The package build step is best understood as the handoff point between creator
workflow and runtime serving.

On the current Luminal deployment, those package artifacts are generated into
the host-managed runtime area configured by the creator workbench:

- ``/srv/work/pipeworks/runtime/namegen-lexicon/output``

That keeps generated artifacts out of the repo checkout while still leaving
them close to the hosted workbench surface.

What does not happen here
-------------------------

This repository does not own:

- runtime HTTP serving of generated names
- runtime favorites or user state
- service deployment or host-managed database state

Those responsibilities belong downstream, primarily in
`pipeworks-namegen-api`.
