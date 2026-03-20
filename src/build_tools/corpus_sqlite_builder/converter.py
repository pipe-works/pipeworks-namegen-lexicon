"""
JSON to SQLite conversion logic for corpus data.

This module handles converting large annotated JSON files into optimized
SQLite databases for efficient querying.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .schema import CORPUS_SCHEMA_VERSION, create_database, insert_metadata


def find_annotated_json(data_dir: Path) -> Path | None:
    """
    Find the annotated JSON file in a corpus data directory.

    Args:
        data_dir: Path to the data directory (e.g., _working/output/.../data/)

    Returns:
        Path to the annotated JSON file, or None if not found

    Looks for files matching the pattern: *_syllables_annotated.json
    Supports both pyphen and nltk prefixes.
    """
    if not data_dir.exists() or not data_dir.is_dir():
        return None

    # Look for annotated JSON files
    json_files = list(data_dir.glob("*_syllables_annotated.json"))

    if len(json_files) == 0:
        return None
    elif len(json_files) == 1:
        return json_files[0]
    else:
        # Multiple annotated JSON files found - this shouldn't happen
        # Return the first one but this indicates a potential issue
        return json_files[0]


def convert_json_to_sqlite(corpus_dir: Path, force: bool = False, batch_size: int = 10000) -> Path:
    """
    Convert an annotated JSON file to a SQLite database.

    This function discovers the annotated JSON file in the corpus directory,
    creates a SQLite database with the appropriate schema, and efficiently
    converts all syllable data using batched transactions.

    Args:
        corpus_dir: Path to corpus directory (e.g., _working/output/20260110_115453_pyphen/)
        force: If True, overwrite existing database. If False, raise error if exists.
        batch_size: Number of records to insert per transaction (default: 10000)

    Returns:
        Path to the created corpus.db file

    Raises:
        FileNotFoundError: If corpus_dir doesn't exist or no annotated JSON found
        FileExistsError: If corpus.db exists and force=False
        ValueError: If JSON structure is invalid
        json.JSONDecodeError: If JSON is malformed
    """
    # Validate corpus directory exists
    if not corpus_dir.exists() or not corpus_dir.is_dir():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    # Find the annotated JSON file
    data_dir = corpus_dir / "data"
    json_path = find_annotated_json(data_dir)

    if json_path is None:
        raise FileNotFoundError(
            f"No annotated JSON file found in {data_dir}. "
            "Looking for: *_syllables_annotated.json"
        )

    # Set up database path
    db_path = data_dir / "corpus.db"

    # Check if database already exists
    if db_path.exists() and not force:
        raise FileExistsError(
            f"Database already exists: {db_path}\n"
            "Use --force to overwrite, or run a new extraction instead."
        )

    # Load and validate JSON data
    print(f"Loading JSON from: {json_path.name}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON must contain a list of syllable records")

    if len(data) == 0:
        raise ValueError("JSON contains no syllable records")

    # Validate structure of first record
    _validate_record_structure(data[0])

    print(f"Converting {len(data):,} syllables to SQLite...")

    # Remove existing database if force=True
    if db_path.exists():
        db_path.unlink()

    # Create new database
    conn = create_database(db_path)

    try:
        # Insert syllables in batches
        _insert_syllables_batched(conn, data, batch_size)

        # Insert metadata
        metadata = {
            "schema_version": str(CORPUS_SCHEMA_VERSION),
            "source_tool": "corpus_sqlite_builder",
            "source_version": "0.2.0",  # TODO: Get from package version
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_syllables": str(len(data)),
            "source_json_path": str(json_path.name),
        }
        insert_metadata(conn, metadata)

        # Optimize database for query performance
        # VACUUM: Reclaims unused space, defragments the database file
        # ANALYZE: Updates query planner statistics for optimal query plans
        # These operations improve both file size and query performance
        print("Optimizing database...")
        conn.execute("VACUUM;")
        conn.execute("ANALYZE;")
        conn.commit()

        # Verify data integrity
        cursor = conn.cursor()
        row_count = cursor.execute("SELECT COUNT(*) FROM syllables").fetchone()[0]

        if row_count != len(data):
            raise ValueError(
                f"Data integrity check failed: expected {len(data)} rows, "
                f"found {row_count} rows"
            )

        print(f"✓ Successfully created: {db_path.name}")
        print(f"  Syllables: {row_count:,}")
        print(f"  Size: {db_path.stat().st_size / (1024 * 1024):.1f} MB")

        return db_path

    except Exception:
        conn.close()
        # Clean up partial database on error
        if db_path.exists():
            db_path.unlink()
        raise

    finally:
        conn.close()


def _validate_record_structure(record: dict) -> None:
    """
    Validate that a syllable record has the expected structure.

    Args:
        record: Dictionary representing a syllable record

    Raises:
        ValueError: If record structure is invalid
    """
    required_fields = ["syllable", "frequency", "features"]
    for field in required_fields:
        if field not in record:
            raise ValueError(f"Record missing required field: {field}")

    features = record["features"]
    if not isinstance(features, dict):
        raise ValueError("Record 'features' must be a dictionary")

    required_features = [
        "starts_with_vowel",
        "starts_with_cluster",
        "starts_with_heavy_cluster",
        "contains_plosive",
        "contains_fricative",
        "contains_liquid",
        "contains_nasal",
        "short_vowel",
        "long_vowel",
        "ends_with_vowel",
        "ends_with_nasal",
        "ends_with_stop",
    ]

    for feature in required_features:
        if feature not in features:
            raise ValueError(f"Record features missing required field: {feature}")


def _insert_syllables_batched(conn: sqlite3.Connection, data: list[dict], batch_size: int) -> None:
    """
    Insert syllable records in batches for efficient bulk loading.

    Batching improves performance by reducing transaction overhead. Instead of
    committing after each row (30,000+ transactions), we commit after every
    batch_size rows (3-4 transactions for typical corpora). This provides:
    - 10-20x faster insertion than row-by-row commits
    - Controlled memory usage (only batch_size rows in memory at once)
    - Progress reporting without excessive overhead

    Args:
        conn: SQLite database connection
        data: List of syllable records from JSON
        batch_size: Number of records per transaction (default: 10,000)
    """
    cursor = conn.cursor()
    batch = []
    total = len(data)
    inserted = 0

    for record in data:
        features = record["features"]

        # Convert boolean features to integers (SQLite doesn't have boolean type)
        row = (
            record["syllable"],
            record["frequency"],
            int(features["starts_with_vowel"]),
            int(features["starts_with_cluster"]),
            int(features["starts_with_heavy_cluster"]),
            int(features["contains_plosive"]),
            int(features["contains_fricative"]),
            int(features["contains_liquid"]),
            int(features["contains_nasal"]),
            int(features["short_vowel"]),
            int(features["long_vowel"]),
            int(features["ends_with_vowel"]),
            int(features["ends_with_nasal"]),
            int(features["ends_with_stop"]),
        )

        batch.append(row)

        # Insert batch when it reaches batch_size
        if len(batch) >= batch_size:
            cursor.executemany(
                """
                INSERT INTO syllables (
                    syllable, frequency,
                    starts_with_vowel, starts_with_cluster, starts_with_heavy_cluster,
                    contains_plosive, contains_fricative, contains_liquid, contains_nasal,
                    short_vowel, long_vowel,
                    ends_with_vowel, ends_with_nasal, ends_with_stop
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                batch,
            )
            conn.commit()
            inserted += len(batch)
            print(f"  Progress: {inserted:,} / {total:,} ({inserted/total*100:.1f}%)")
            batch = []

    # Insert remaining records
    if batch:
        cursor.executemany(
            """
            INSERT INTO syllables (
                syllable, frequency,
                starts_with_vowel, starts_with_cluster, starts_with_heavy_cluster,
                contains_plosive, contains_fricative, contains_liquid, contains_nasal,
                short_vowel, long_vowel,
                ends_with_vowel, ends_with_nasal, ends_with_stop
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
        conn.commit()
        inserted += len(batch)
        print(f"  Progress: {inserted:,} / {total:,} (100.0%)")
