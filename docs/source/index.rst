Pipeworks Namegen Lexicon
=========================

`pipeworks-namegen-lexicon` is the home of the human-facing PipeWorks apps.

It owns the corpus-to-lexicon workflow: extraction, normalization, feature
annotation, exploratory syllable walking, candidate generation, selection, and
package building for downstream runtime import. It also now contains the first
consumer-facing names app implementation, while the runtime API remains a
separate service boundary.

This documentation is intentionally smaller and more opinionated than the old
monolith docs. The goal is to explain the maintained web-first creator surface
and the repository boundary clearly, without restoring the full historical doc
sprawl.

.. toctree::
   :maxdepth: 2
   :caption: Guide

   philosophy
   tools-overview
   workbench
   names
   package-flow
   luminal
   development
   testing
