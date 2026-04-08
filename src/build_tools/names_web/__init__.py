"""Pipe-Works consumer-facing names web app.

This package is the first dedicated home for the simpler "play with prepared
packages" surface that should eventually replace the legacy consumer UI still
embedded in ``pipeworks-namegen-api``.
"""

from __future__ import annotations

from build_tools.names_web.cli import NamesAppSettings, load_names_app_settings
from build_tools.names_web.server import NamesAppHandler, run_server

__all__ = [
    "NamesAppHandler",
    "NamesAppSettings",
    "load_names_app_settings",
    "run_server",
]
