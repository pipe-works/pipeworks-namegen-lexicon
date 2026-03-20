"""
Corpus Database - Build Provenance Ledger for Syllable Extraction

This module provides observational tracking for all syllable extractor runs across
different tools (pyphen, NLTK, eSpeak, etc.). The database records who ran what
extraction, when, with which settings, and what outputs were produced.

**This is a build-time tool only** - not used during runtime name generation.

Design Philosophy:
    - **Observational only**: Records outcomes, doesn't control behavior
    - **Append-only**: Runs are never modified, only added
    - **Tool-agnostic**: Works for pyphen, NLTK, eSpeak, or future extractors
    - **Queryable**: Easy to find "which run produced this file?"

Key Features:
    - Full provenance tracking (inputs, outputs, settings, timestamps)
    - Support for multiple extractor tools
    - Command-line reproducibility via full CLI capture
    - Manual annotation support via notes field
    - Simple query API for run history analysis

Main Components:
    - CorpusLedger: Main API for recording and querying runs
    - SCHEMA_VERSION: Schema version for migration tracking
    - get_schema_description: Human-readable schema documentation

Usage:
    >>> from build_tools.corpus_db import CorpusLedger
    >>> from pathlib import Path
    >>>
    >>> # Initialize ledger (creates database if needed)
    >>> ledger = CorpusLedger()
    >>>
    >>> # Start recording a run
    >>> run_id = ledger.start_run(
    ...     extractor_tool="syllable_extractor",
    ...     extractor_version="0.2.0",
    ...     pyphen_lang="en_US",
    ...     min_len=2,
    ...     max_len=8,
    ...     command_line="python -m build_tools.syllable_extractor --file input.txt"
    ... )
    >>>
    >>> # Record what went in
    >>> ledger.record_input(run_id, Path("data/corpus/english.txt"))
    >>>
    >>> # ... extraction happens (ledger doesn't participate) ...
    >>>
    >>> # Record what came out
    >>> ledger.record_output(
    ...     run_id,
    ...     output_path=Path("data/raw/en_US/corpus.syllables"),
    ...     unique_syllable_count=1234
    ... )
    >>>
    >>> # Mark run complete
    >>> ledger.complete_run(run_id, exit_code=0, status="completed")
    >>>
    >>> # Query runs later
    >>> recent = ledger.get_recent_runs(limit=10)
    >>> for run in recent:
    ...     print(f"{run['run_timestamp']}: {run['extractor_tool']}")

Common Queries:
    # Which run produced this file?
    >>> run = ledger.find_run_by_output(Path("data/raw/corpus.syllables"))
    >>> print(run['command_line'])

    # Show all runs using en_GB
    >>> runs = ledger.get_runs_by_tool("syllable_extractor")
    >>> en_gb = [r for r in runs if r['pyphen_lang'] == 'en_GB']

    # Get overall statistics
    >>> stats = ledger.get_stats()
    >>> print(f"Total runs: {stats['total_runs']}")
    >>> print(f"Success rate: {stats['completed_runs']/stats['total_runs']*100:.1f}%")

Database Location:
    Default: data/raw/syllable_extractor.db
    Custom:  Pass db_path to CorpusLedger(db_path=Path(...))

Context Manager Support:
    >>> with CorpusLedger() as ledger:
    ...     run_id = ledger.start_run(...)
    ...     # Connection automatically closed on exit
"""

from .ledger import CorpusLedger
from .schema import SCHEMA_VERSION, get_schema_description

__all__ = [
    "CorpusLedger",
    "SCHEMA_VERSION",
    "get_schema_description",
]

__version__ = "0.1.0"
