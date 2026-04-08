Creator Workbench
=================

The main interactive surface in this repository is
``build_tools.syllable_walk_web``.

It is a browser-based creator workbench that combines pipeline execution and
exploratory syllable walking in one maintained UI.

Workbench Structure
-------------------

The workbench has two major tool families:

- Pipeline
  Runs extraction, normalization, annotation, and database stages from the
  browser, with live monitoring and manifest-backed run history.
- Walker
  Loads prepared corpora into Patch A and Patch B for comparison, then supports
  walk generation, candidate combination, selection, analysis, rendering, and
  packaging.

What the web app is for
-----------------------

The maintained web workbench supports:

- selecting source and output directories
- choosing extractor mode such as ``pyphen`` or ``nltk``
- running pipeline stages with progress and logs
- discovering prior runs from manifest-backed output directories
- loading dual patches for side-by-side comparison
- using named walk profiles or custom walk settings
- generating candidate pools in flat or walk-based modes
- selecting names by policy such as ``first_name`` or ``place_name``
- exporting ZIP packages plus companion metadata for downstream runtime use

Why the workbench matters
-------------------------

This is not just a convenience wrapper around CLI tools.

The workbench is the environment where a creator can compare corpus patches,
explore different walk profiles, observe how phonetic constraints change the
resulting space, and decide what is worth packaging. In practice, that makes it
the main authorship surface for PipeWorks lexicon material.

Implementation Notes
--------------------

The current implementation is organized around a few main areas:

- ``build_tools.syllable_walk_web.api``
  Route-level request handlers for browse, pipeline, and walker operations.
- ``build_tools.syllable_walk_web.services``
  Corpus loading, run discovery, pipeline execution, metrics, package building,
  and session/run-state helpers.
- ``build_tools.syllable_walk_web.static``
  Browser frontend assets for the maintained web surface.
- ``build_tools.syllable_walk_web.server``
  The stdlib HTTP server that wires the application together.

The web surface is the maintained interactive interface in this repository.
Historical TUI surfaces are not part of the supported product shape here.
