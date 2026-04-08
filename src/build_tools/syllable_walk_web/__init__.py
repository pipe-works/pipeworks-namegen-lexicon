"""Pipe-Works creator workbench package.

This package contains the maintained interactive surface for lexicon creation:
pipeline orchestration, dual-patch walking, analysis, selection, and package
authoring. It is a creator-facing application, not a runtime-generation
service, and it deliberately consolidates the old TUI-heavy workflow into a
single browser-first surface.

Features:
    - Pipeline tool: extraction, normalization, annotation with live monitoring
    - Walker tool: dual-patch syllable walking, name combiner, name selector
    - Corpus analysis with terrain visualization and profile reach deep-dives
    - Name rendering and package export (ZIP with manifest + disk metadata persistence)
    - Dark/light theme support
    - 18 API endpoints across Pipeline, Walker, Browse, Settings, and Version groups

Architecture:
    - ``api/``: Request handlers (``browse``, ``pipeline``, ``walker``)
    - ``services/``: Business logic (``corpus_loader``, ``combiner_runner``,
      ``selector_runner``, ``walk_generator``, ``metrics``, ``packager``,
      ``pipeline_runner``)
    - ``state.py``: Dataclasses (``PatchState``, ``PipelineJobState``,
      ``CreatorWorkbenchState``)
    - ``server.py``: stdlib ``http.server`` with routing and static file serving

Usage:
    Launch the web server from the command line::

        python -m build_tools.syllable_walk_web
        python -m build_tools.syllable_walk_web --port 9000
        python -m build_tools.syllable_walk_web --output-base /path/to/output

    Or programmatically::

        >>> from build_tools.syllable_walk_web import run_server
        >>> run_server(port=8000)
"""

from build_tools.syllable_walk_web.server import (
    CreatorWorkbenchHandler,
    find_available_port,
    run_server,
)

__all__ = [
    "CreatorWorkbenchHandler",
    "find_available_port",
    "run_server",
]
