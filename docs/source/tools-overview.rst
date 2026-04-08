Creator Workbench Modules
=========================

The maintained creator surface in this repository is the web workbench, but the
workbench sits on top of a larger build-tools layer under ``src/build_tools``.

This page documents the maintained tool families without recreating the full
archived monolith manual.

Pipeline Preparation
--------------------

These modules prepare corpus material for exploration and packaging:

- ``pyphen_syllable_extractor``
  Dictionary-driven extraction for many languages using pyphen.
- ``nltk_syllable_extractor``
  English-focused extraction using CMUDict-backed phonetic splitting.
- ``pyphen_syllable_normaliser``
  Cleanup and normalization for pyphen extraction output.
- ``nltk_syllable_normaliser``
  Cleanup and normalization for NLTK extraction output.
- ``syllable_feature_annotator``
  Adds explicit phonetic feature metadata to normalized syllables.
- ``corpus_sqlite_builder``
  Builds SQLite artifacts for faster corpus loading and repeatable run handling.

Exploration and Selection
-------------------------

These modules operate on prepared corpus material:

- ``syllable_walk``
  Core phonetic-space walker, profiles, and reach calculations.
- ``name_combiner``
  Structural candidate generation from prepared syllable material.
- ``name_selector``
  Policy-based filtering and ranking for candidate pools.
- ``name_renderer``
  Rendering helpers for turning selected material into readable names.

Analysis Support
----------------

The repository also includes analysis-oriented modules under
``syllable_analysis`` for inspecting corpus shape, dimensionality, and related
metrics while developing lexicon material.

How these pieces fit together
-----------------------------

The typical creator flow is:

1. Extract source material.
2. Normalize it.
3. Annotate it with explicit features.
4. Build a run directory and optional SQLite representation.
5. Explore the result through walker profiles and dual-patch comparison.
6. Combine and select candidate names.
7. Package the chosen output for downstream API import.

The web workbench exists to make this full chain usable from one maintained
interactive surface.

Retired Surfaces
----------------

Historical TUI applications from the monolith era are intentionally retired in
this repository. The maintained interactive surface is the web workbench, not a
parallel web-plus-TUI product line.
