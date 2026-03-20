"""Shared non-UI CLI helpers used by lexicon pipeline extractors.

The historical project exposed Textual widgets from this package, but the
lexicon repo retires all TUI surfaces. We intentionally keep only the reusable
non-UI helpers consumed by extractor CLIs and batch workflows.
"""

from build_tools.tui_common.batch import collect_files_from_args, run_batch_extraction
from build_tools.tui_common.cli_utils import (
    CORPUS_DB_AVAILABLE,
    READLINE_AVAILABLE,
    discover_files,
    input_with_completion,
    path_completer,
    record_corpus_db_safe,
    setup_tab_completion,
)
from build_tools.tui_common.interactive import (
    print_banner,
    print_extraction_complete,
    print_section,
    prompt_extraction_settings,
    prompt_input_file,
    prompt_integer,
)
from build_tools.tui_common.ledger import ExtractionLedgerContext

__all__ = [
    "CORPUS_DB_AVAILABLE",
    "READLINE_AVAILABLE",
    "ExtractionLedgerContext",
    "collect_files_from_args",
    "discover_files",
    "input_with_completion",
    "path_completer",
    "print_banner",
    "print_extraction_complete",
    "print_section",
    "prompt_extraction_settings",
    "prompt_input_file",
    "prompt_integer",
    "record_corpus_db_safe",
    "run_batch_extraction",
    "setup_tab_completion",
]
