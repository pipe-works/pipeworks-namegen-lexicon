"""
Database schema definitions for corpus extraction run tracking.

This module defines the SQLite database schema for tracking all syllable extractor
runs across different tools (pyphen, NLTK, eSpeak, etc.). The schema provides full
provenance tracking - who, what, when, with what settings, and which outputs.

The database serves as an **observational ledger only** - it records what happened
but does not influence extraction behavior. This keeps extraction logic pure and
deterministic while providing queryable build history.

Schema Design Philosophy:
    - Append-only: Runs are never modified, only added
    - Observational: Records outcomes, doesn't control behavior
    - Queryable: Easy to find "which run produced this file?"
    - Tool-agnostic: Works for pyphen, NLTK, eSpeak, or future extractors

Tables:
    runs: One row per extractor invocation with all configuration
    inputs: Source files/directories that were processed (one-to-many)
    outputs: Generated .syllables and .meta files (one-to-many)

Example Queries:
    -- Find all runs using en_GB
    SELECT * FROM runs WHERE pyphen_lang = 'en_GB';

    -- Which run produced this file?
    SELECT r.* FROM runs r
    JOIN outputs o ON r.id = o.run_id
    WHERE o.output_path = 'data/raw/en_US/corpus_v1.syllables';

    -- Compare syllable counts across tools
    SELECT extractor_tool, AVG(unique_syllable_count) as avg_unique
    FROM runs r JOIN outputs o ON r.id = o.run_id
    GROUP BY extractor_tool;
"""

# SQL schema version for migration tracking
SCHEMA_VERSION = 1

# SQL DDL statements for creating tables
CREATE_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL,
    extractor_tool TEXT NOT NULL,
    extractor_version TEXT,
    hostname TEXT,
    exit_code INTEGER,
    status TEXT CHECK(status IN ('running', 'completed', 'failed', 'interrupted')),
    pyphen_lang TEXT,
    auto_lang_detected TEXT,
    min_len INTEGER,
    max_len INTEGER,
    recursive INTEGER,
    pattern TEXT,
    command_line TEXT,
    notes TEXT
);
"""

CREATE_INPUTS_TABLE = """
CREATE TABLE IF NOT EXISTS inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    source_path TEXT NOT NULL,
    file_count INTEGER,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);
"""

CREATE_OUTPUTS_TABLE = """
CREATE TABLE IF NOT EXISTS outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    output_path TEXT NOT NULL,
    syllable_count INTEGER,
    unique_syllable_count INTEGER,
    meta_path TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);
"""

# Indexes for common queries
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON runs(run_timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_runs_tool ON runs(extractor_tool);",
    "CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);",
    "CREATE INDEX IF NOT EXISTS idx_runs_lang ON runs(pyphen_lang);",
    "CREATE INDEX IF NOT EXISTS idx_inputs_run ON inputs(run_id);",
    "CREATE INDEX IF NOT EXISTS idx_outputs_run ON outputs(run_id);",
    "CREATE INDEX IF NOT EXISTS idx_outputs_path ON outputs(output_path);",
]

# Schema metadata table for version tracking
CREATE_SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
"""


def get_all_ddl_statements() -> list[str]:
    """
    Get all DDL statements required to initialize the database schema.

    Returns a list of SQL statements that should be executed in order to
    create a fresh database with the current schema version.

    Returns:
        List of SQL DDL statements (CREATE TABLE, CREATE INDEX)

    Example:
        >>> statements = get_all_ddl_statements()
        >>> for stmt in statements:
        ...     cursor.execute(stmt)
    """
    return [
        CREATE_RUNS_TABLE,
        CREATE_INPUTS_TABLE,
        CREATE_OUTPUTS_TABLE,
        CREATE_SCHEMA_VERSION_TABLE,
        *CREATE_INDEXES,
    ]


def get_schema_description() -> str:
    """
    Generate a human-readable description of the database schema.

    Useful for documentation, debugging, and understanding the database
    structure without examining SQL directly.

    Returns:
        Multi-line string describing tables, columns, and relationships

    Example:
        >>> print(get_schema_description())
        Corpus Extraction Run Ledger Schema (v1)
        ========================================
        ...
    """
    lines = []
    lines.append(f"Corpus Extraction Run Ledger Schema (v{SCHEMA_VERSION})")
    lines.append("=" * 70)
    lines.append("")
    lines.append("Table: runs")
    lines.append("  One row per extractor invocation")
    lines.append("  Columns:")
    lines.append("    - id: Unique run identifier (autoincrement)")
    lines.append("    - run_timestamp: ISO 8601 timestamp when run started")
    lines.append(
        "    - extractor_tool: Tool name (e.g., 'syllable_extractor', 'syllable_extractor_nltk')"
    )
    lines.append("    - extractor_version: Version/git SHA of the tool")
    lines.append("    - hostname: Machine where extraction ran")
    lines.append("    - exit_code: Unix exit code (0=success, non-zero=failure)")
    lines.append("    - status: 'running'|'completed'|'failed'|'interrupted'")
    lines.append("    - pyphen_lang: Pyphen language code (NULL for non-pyphen tools)")
    lines.append("    - auto_lang_detected: Auto-detected language code")
    lines.append("    - min_len: Minimum syllable length constraint")
    lines.append("    - max_len: Maximum syllable length constraint")
    lines.append("    - recursive: 1 if source was processed recursively, 0 otherwise")
    lines.append("    - pattern: File pattern for filtering (e.g., '*.txt')")
    lines.append("    - command_line: Full command invocation for reproducibility")
    lines.append("    - notes: User-provided annotations")
    lines.append("")
    lines.append("Table: inputs")
    lines.append("  Source files/directories processed (many-to-one with runs)")
    lines.append("  Columns:")
    lines.append("    - id: Unique input record identifier")
    lines.append("    - run_id: Foreign key to runs.id")
    lines.append("    - source_path: Path to input file/directory")
    lines.append("    - file_count: Number of files if directory, NULL if single file")
    lines.append("")
    lines.append("Table: outputs")
    lines.append("  Generated output files (many-to-one with runs)")
    lines.append("  Columns:")
    lines.append("    - id: Unique output record identifier")
    lines.append("    - run_id: Foreign key to runs.id")
    lines.append("    - output_path: Path to .syllables file")
    lines.append("    - syllable_count: Total syllables (with duplicates)")
    lines.append("    - unique_syllable_count: Unique syllables")
    lines.append("    - meta_path: Path to .meta file")
    lines.append("")
    lines.append("Indexes:")
    lines.append("  - runs: timestamp, tool, status, pyphen_lang")
    lines.append("  - inputs: run_id")
    lines.append("  - outputs: run_id, output_path")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)
