"""
SQLite schema definitions for corpus databases.

This module defines the database schema for storing syllable corpus data,
including syllables, features, and metadata.
"""

import sqlite3
from pathlib import Path

# Schema version for tracking database structure evolution
CORPUS_SCHEMA_VERSION = 1

# SQL DDL statements
CREATE_METADATA_TABLE = """
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

CREATE_SYLLABLES_TABLE = """
CREATE TABLE syllables (
    syllable TEXT PRIMARY KEY,
    frequency INTEGER NOT NULL,
    starts_with_vowel INTEGER NOT NULL,
    starts_with_cluster INTEGER NOT NULL,
    starts_with_heavy_cluster INTEGER NOT NULL,
    contains_plosive INTEGER NOT NULL,
    contains_fricative INTEGER NOT NULL,
    contains_liquid INTEGER NOT NULL,
    contains_nasal INTEGER NOT NULL,
    short_vowel INTEGER NOT NULL,
    long_vowel INTEGER NOT NULL,
    ends_with_vowel INTEGER NOT NULL,
    ends_with_nasal INTEGER NOT NULL,
    ends_with_stop INTEGER NOT NULL
);
"""

# Indexes for common TUI query patterns
# These indexes optimize the most frequent syllable_walk_tui queries:
# - Filter by vowel boundaries (e.g., "starts with vowel" toggle)
# - Sort by frequency (e.g., "show most common syllables")
# - Filter by consonant clusters (e.g., "starts with cluster" toggle)
# - Composite queries (e.g., "vowel-to-vowel" syllables)
CREATE_INDEXES = [
    "CREATE INDEX idx_starts_with_vowel ON syllables(starts_with_vowel);",
    "CREATE INDEX idx_ends_with_vowel ON syllables(ends_with_vowel);",
    "CREATE INDEX idx_frequency ON syllables(frequency DESC);",
    "CREATE INDEX idx_vowel_boundaries ON syllables(starts_with_vowel, ends_with_vowel);",
    "CREATE INDEX idx_starts_with_cluster ON syllables(starts_with_cluster);",
    "CREATE INDEX idx_ends_with_stop ON syllables(ends_with_stop);",
]

# Pragmas for read-optimized performance
# These settings optimize for our use case: write-once, read-many queries
OPTIMIZATION_PRAGMAS = [
    "PRAGMA journal_mode=WAL;",  # Write-Ahead Logging for better concurrency
    "PRAGMA synchronous=NORMAL;",  # Balanced durability/speed for bulk inserts
    "PRAGMA cache_size=-64000;",  # 64MB cache for faster queries (negative = KB)
    "PRAGMA temp_store=MEMORY;",  # Store temp tables in RAM for speed
]


def create_database(db_path: Path) -> sqlite3.Connection:
    """
    Create a new corpus database with the standard schema.

    Args:
        db_path: Path where the database will be created

    Returns:
        SQLite connection to the newly created database

    Raises:
        sqlite3.Error: If database creation fails
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Apply optimization pragmas
        for pragma in OPTIMIZATION_PRAGMAS:
            conn.execute(pragma)

        # Create tables
        conn.execute(CREATE_METADATA_TABLE)
        conn.execute(CREATE_SYLLABLES_TABLE)

        # Create indexes
        for index_sql in CREATE_INDEXES:
            conn.execute(index_sql)

        conn.commit()
        return conn

    except sqlite3.Error:
        conn.close()
        raise


def insert_metadata(conn: sqlite3.Connection, metadata: dict[str, str]) -> None:
    """
    Insert metadata key-value pairs into the database.

    Args:
        conn: SQLite database connection
        metadata: Dictionary of metadata key-value pairs

    Common metadata keys:
        - schema_version: Database schema version (int as string)
        - source_tool: Name of the tool that created this database
        - source_version: Version of the source tool
        - generated_at: ISO 8601 timestamp of creation
        - total_syllables: Number of syllables in the database (int as string)
        - source_json_path: Path to the source JSON file
    """
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO metadata (key, value) VALUES (?, ?)", metadata.items())
    conn.commit()


def get_metadata(conn: sqlite3.Connection) -> dict[str, str]:
    """
    Retrieve all metadata from the database.

    Args:
        conn: SQLite database connection

    Returns:
        Dictionary of metadata key-value pairs
    """
    cursor = conn.cursor()
    return dict(cursor.execute("SELECT key, value FROM metadata").fetchall())


def verify_schema_version(conn: sqlite3.Connection) -> int:
    """
    Verify the database schema version matches the current version.

    Args:
        conn: SQLite database connection

    Returns:
        Schema version number from the database

    Raises:
        ValueError: If schema version is missing or incompatible
    """
    metadata = get_metadata(conn)

    if "schema_version" not in metadata:
        raise ValueError("Database is missing schema_version metadata")

    db_version = int(metadata["schema_version"])

    if db_version != CORPUS_SCHEMA_VERSION:
        raise ValueError(
            f"Database schema version {db_version} is incompatible with "
            f"current version {CORPUS_SCHEMA_VERSION}. "
            "Run migration tool or regenerate from JSON."
        )

    return db_version
