"""
Corpus SQLite Builder - JSON to SQLite Conversion Tool

Converts large annotated JSON files into optimized SQLite databases for
efficient querying in interactive tools like the syllable_walk_tui.

This is a **build-time tool only** - not used during runtime name generation.

Features:
- Memory-efficient conversion of 100MB+ JSON files
- Batched transactions for performance
- Idempotent conversion (safe to re-run)
- Auto-discovery of annotated JSON files
- Batch conversion support

Usage:
    >>> from build_tools.corpus_sqlite_builder import convert_json_to_sqlite
    >>> from pathlib import Path
    >>> corpus_dir = Path("_working/output/20260110_115453_pyphen")
    >>> db_path = convert_json_to_sqlite(corpus_dir)
    >>> print(f"Created: {db_path}")

Command-line usage:

.. code-block:: bash

    # Convert single corpus
    python -m build_tools.corpus_sqlite_builder _working/output/20260110_115453_pyphen/

    # Force overwrite
    python -m build_tools.corpus_sqlite_builder _working/output/20260110_115453_pyphen/ --force

    # Batch convert all
    python -m build_tools.corpus_sqlite_builder --batch _working/output/

Design Philosophy:
    - JSON is the canonical source of truth (human-readable, portable)
    - SQLite is derived data (optimized for queries, regeneratable)
    - Both formats coexist in data/ subdirectory
    - TUI prefers SQLite, falls back to JSON
"""

from .converter import convert_json_to_sqlite, find_annotated_json
from .schema import (
    CORPUS_SCHEMA_VERSION,
    create_database,
    get_metadata,
    insert_metadata,
    verify_schema_version,
)

__all__ = [
    # Conversion functions
    "convert_json_to_sqlite",
    "find_annotated_json",
    # Schema functions
    "create_database",
    "insert_metadata",
    "get_metadata",
    "verify_schema_version",
    "CORPUS_SCHEMA_VERSION",
]
