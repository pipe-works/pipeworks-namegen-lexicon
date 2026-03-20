"""
File I/O helper functions for syllable feature annotation.

This module provides simple, reusable functions for loading syllable data
and saving annotated results. All functions are designed to be deterministic,
predictable, and easy to test.

Design Principles
-----------------
1. **Boring is Good**: Simple, straightforward I/O operations
2. **Explicit Errors**: Clear error messages for common failure modes
3. **Minimal Abstraction**: Functions do exactly what they say
4. **Type Clarity**: Clear input/output types with type hints
5. **No Magic**: No hidden transformations or side effects

Functions
---------
load_syllables(file_path: Path) -> list[str]
    Load syllables from text file (one per line)

load_frequencies(file_path: Path) -> dict[str, int]
    Load frequency mapping from JSON file

save_annotated_syllables(syllables: list[dict], file_path: Path) -> None
    Save annotated syllables to JSON file with formatting

Usage
-----
Load syllables from normalizer output::

    >>> from pathlib import Path
    >>> from build_tools.syllable_feature_annotator.file_io import load_syllables
    >>> syllables = load_syllables(Path("data/normalized/syllables_unique.txt"))
    >>> print(f"Loaded {len(syllables)} syllables")

Load frequency data::

    >>> from build_tools.syllable_feature_annotator.file_io import load_frequencies
    >>> frequencies = load_frequencies(Path("data/normalized/syllables_frequencies.json"))
    >>> print(f"Most frequent: {max(frequencies.items(), key=lambda x: x[1])}")

Save annotated results::

    >>> from build_tools.syllable_feature_annotator.file_io import save_annotated_syllables
    >>> annotated = [
    ...     {"syllable": "ka", "frequency": 187, "features": {...}},
    ...     {"syllable": "ra", "frequency": 162, "features": {...}},
    ... ]
    >>> save_annotated_syllables(annotated, Path("output/syllables_annotated.json"))

Implementation Notes
--------------------
**Empty Line Handling**:

The load_syllables function filters out empty lines automatically. This is
consistent with the syllable normalizer's behavior and prevents issues with
trailing newlines or blank lines in input files.

**JSON Formatting**:

The save_annotated_syllables function uses indent=2 for human-readable output.
While this increases file size, it makes the annotated dataset much easier to
inspect, debug, and version control.

**UTF-8 Encoding**:

All file operations explicitly use UTF-8 encoding to ensure consistent behavior
across different platforms and locales. This is critical for syllables that may
contain non-ASCII characters before normalization.

**Error Handling**:

Functions raise clear exceptions with informative messages:
- FileNotFoundError: Input file doesn't exist
- ValueError: Malformed JSON or unexpected data format
- IOError: Permission errors or disk issues

Error Handling Strategy
-----------------------
These functions intentionally do NOT catch exceptions. Instead, they let
exceptions propagate to the caller with clear error messages. This follows
the principle of "fail fast" and makes debugging easier.

The caller (annotator.py or cli.py) is responsible for catching exceptions
and providing user-friendly error messages if needed.
"""

import json
from pathlib import Path


def load_syllables(file_path: Path) -> list[str]:
    """
    Load syllables from a text file (one syllable per line).

    Reads a text file containing one syllable per line and returns a list
    of syllable strings. Empty lines are automatically filtered out.

    This function is designed to load the output from the syllable normalizer,
    specifically the `syllables_unique.txt` file.

    Parameters
    ----------
    file_path : Path
        Path to text file containing syllables (one per line)

    Returns
    -------
    list[str]
        List of syllable strings, with empty lines filtered out

    Raises
    ------
    FileNotFoundError
        If the input file doesn't exist
    IOError
        If there are permission or disk errors

    Examples
    --------
    Load syllables from normalizer output::

        >>> from pathlib import Path
        >>> syllables = load_syllables(Path("data/normalized/syllables_unique.txt"))
        >>> len(syllables)
        1523
        >>> syllables[:3]
        ['ka', 'ra', 'mi']

    Handle missing file::

        >>> syllables = load_syllables(Path("nonexistent.txt"))
        Traceback (most recent call last):
            ...
        FileNotFoundError: [Errno 2] No such file or directory: 'nonexistent.txt'

    Notes
    -----
    - Empty lines are filtered automatically
    - Lines are stripped of leading/trailing whitespace
    - UTF-8 encoding is used explicitly
    - The file is read entirely into memory (suitable for typical syllable counts)
    - Order is preserved from the input file
    - Deterministic: same file always produces same output
    """
    with open(file_path, "r", encoding="utf-8") as f:
        # Read lines, strip whitespace, filter empty lines
        syllables = [line.strip() for line in f if line.strip()]
    return syllables


def load_frequencies(file_path: Path) -> dict[str, int]:
    """
    Load syllable frequency mapping from a JSON file.

    Reads a JSON file containing a dictionary mapping syllables to their
    occurrence counts. The expected format is: {"syllable": count, ...}

    This function is designed to load the output from the syllable normalizer,
    specifically the `syllables_frequencies.json` file.

    Parameters
    ----------
    file_path : Path
        Path to JSON file containing frequency mapping

    Returns
    -------
    dict[str, int]
        Dictionary mapping syllable strings to integer counts

    Raises
    ------
    FileNotFoundError
        If the input file doesn't exist
    ValueError
        If the JSON is malformed or doesn't contain expected format
    IOError
        If there are permission or disk errors

    Examples
    --------
    Load frequencies from normalizer output::

        >>> from pathlib import Path
        >>> frequencies = load_frequencies(Path("data/normalized/syllables_frequencies.json"))
        >>> len(frequencies)
        1523
        >>> frequencies["ka"]
        187
        >>> frequencies["ra"]
        162

    Get most frequent syllable::

        >>> most_frequent = max(frequencies.items(), key=lambda x: x[1])
        >>> print(f"{most_frequent[0]}: {most_frequent[1]} occurrences")
        ka: 187 occurrences

    Handle missing syllable (returns default)::

        >>> frequencies.get("xyz", 1)  # Default to 1 if missing
        1

    Notes
    -----
    - UTF-8 encoding is used explicitly
    - The entire file is loaded into memory (suitable for typical dataset sizes)
    - No validation is performed on syllable strings or counts
    - Deterministic: same file always produces same output
    - Missing syllables should be handled by caller (use .get(syllable, 1))
    """
    with open(file_path, "r", encoding="utf-8") as f:
        frequencies: dict[str, int] = json.load(f)
    return frequencies


def save_annotated_syllables(syllables: list[dict], file_path: Path) -> None:
    """
    Save annotated syllables to a JSON file with human-readable formatting.

    Writes a list of annotated syllable dictionaries to a JSON file.
    Each dictionary should contain 'syllable', 'frequency', and 'features' keys.

    Output is formatted with 2-space indentation for readability and
    version control friendliness.

    Parameters
    ----------
    syllables : list[dict]
        List of annotated syllable dictionaries, each containing:
        - syllable (str): The syllable string
        - frequency (int): Occurrence count
        - features (dict[str, bool]): Feature detection results
    file_path : Path
        Path where JSON output should be written

    Returns
    -------
    None
        File is written to disk, nothing returned

    Raises
    ------
    IOError
        If there are permission or disk errors
    TypeError
        If syllables is not JSON-serializable

    Examples
    --------
    Save annotated syllables::

        >>> from pathlib import Path
        >>> annotated = [
        ...     {
        ...         "syllable": "kran",
        ...         "frequency": 7,
        ...         "features": {
        ...             "starts_with_cluster": True,
        ...             "contains_plosive": True,
        ...             "short_vowel": True,
        ...             # ... other features ...
        ...         }
        ...     },
        ...     # ... more syllables ...
        ... ]
        >>> save_annotated_syllables(annotated, Path("output/syllables_annotated.json"))

    Expected output format::

        [
          {
            "syllable": "kran",
            "frequency": 7,
            "features": {
              "starts_with_cluster": true,
              "contains_plosive": true,
              "short_vowel": true
            }
          }
        ]

    Notes
    -----
    - Parent directories are created automatically if they don't exist
    - UTF-8 encoding is used explicitly
    - 2-space indentation for readability
    - Output is valid JSON that can be consumed by other tools
    - File is overwritten if it already exists
    - Deterministic: same input always produces same output
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with human-readable formatting
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(syllables, f, indent=2, ensure_ascii=False)
