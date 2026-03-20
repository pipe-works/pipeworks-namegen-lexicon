"""
Core orchestration logic for syllable feature annotation.

This module provides the main annotation pipeline that:
1. Loads syllables and frequencies
2. Applies feature detectors
3. Assembles annotated records
4. Saves output

The annotator is intentionally "dumb" - it mechanically applies detectors
without making decisions, filtering, or interpreting results.

Design Principles
-----------------
1. **Pure Orchestration**: Coordinates I/O and feature detection, nothing more
2. **No Decisions**: Never asks "should we...", only "is this true/false?"
3. **Deterministic**: Same inputs always produce same outputs
4. **No Filtering**: Processes all syllables without exclusion or validation
5. **Single Responsibility**: Annotation only, no interpretation or selection

Classes
-------
AnnotatedSyllable : dataclass
    Structured record for a single annotated syllable
AnnotationStatistics : dataclass
    Statistics about the annotation process
AnnotationResult : dataclass
    Complete annotation result with syllables and metadata

Functions
---------
annotate_syllable(syllable, frequency, detectors) -> AnnotatedSyllable
    Apply all feature detectors to a single syllable
annotate_corpus(syllables, frequencies, detectors) -> AnnotationResult
    Annotate entire syllable corpus
run_annotation_pipeline(syllables_path, frequencies_path, output_path) -> AnnotationResult
    Complete end-to-end annotation pipeline

Usage
-----
Run full annotation pipeline::

    >>> from pathlib import Path
    >>> from build_tools.syllable_feature_annotator.annotator import (
    ...     run_annotation_pipeline
    ... )
    >>> result = run_annotation_pipeline(
    ...     syllables_path=Path("data/normalized/syllables_unique.txt"),
    ...     frequencies_path=Path("data/normalized/syllables_frequencies.json"),
    ...     output_path=Path("data/annotated/syllables_annotated.json")
    ... )
    >>> print(f"Annotated {result.statistics.syllable_count} syllables")
    >>> print(f"Processing time: {result.statistics.processing_time:.2f}s")

Annotate syllables programmatically::

    >>> from build_tools.syllable_feature_annotator.annotator import annotate_corpus
    >>> from build_tools.syllable_feature_annotator.feature_rules import FEATURE_DETECTORS
    >>> syllables = ["ka", "kran", "spla"]
    >>> frequencies = {"ka": 187, "kran": 7, "spla": 2}
    >>> result = annotate_corpus(syllables, frequencies, FEATURE_DETECTORS)
    >>> for record in result.annotated_syllables:
    ...     print(f"{record.syllable}: {sum(record.features.values())} features active")

Annotate single syllable::

    >>> from build_tools.syllable_feature_annotator.annotator import annotate_syllable
    >>> from build_tools.syllable_feature_annotator.feature_rules import FEATURE_DETECTORS
    >>> record = annotate_syllable("kran", 7, FEATURE_DETECTORS)
    >>> record.syllable
    'kran'
    >>> record.features["starts_with_cluster"]
    True

Architecture
------------
The annotator follows a simple three-layer architecture:

1. **Data Models** (AnnotatedSyllable, AnnotationStatistics, AnnotationResult)
   - Structured data containers with validation
   - Clear contracts for input/output
   - Type-safe access to annotation results

2. **Core Logic** (annotate_syllable, annotate_corpus)
   - Pure functions that transform data
   - No I/O, no side effects
   - Easily testable in isolation

3. **Pipeline** (run_annotation_pipeline)
   - Coordinates I/O and core logic
   - Handles timing and statistics
   - Entry point for CLI and programmatic use

This separation makes the code:
- Easy to test (test each layer independently)
- Easy to understand (each layer has clear responsibility)
- Easy to extend (add new features without breaking existing code)

Performance Considerations
--------------------------
The annotator processes syllables sequentially in a single pass. For typical
corpus sizes (1,000-10,000 syllables), this completes in under 1 second.

If processing very large corpora (100,000+ syllables), consider:
1. Using verbose mode to show progress
2. Processing in batches if memory is constrained
3. Profiling to identify bottlenecks

However, premature optimization is avoided. The current implementation is
simple, correct, and fast enough for the intended use case.
"""

import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from build_tools.syllable_feature_annotator import file_io
from build_tools.syllable_feature_annotator.feature_rules import FEATURE_DETECTORS


@dataclass
class AnnotatedSyllable:
    """
    Structured record for a single annotated syllable.

    This dataclass represents the output format for each syllable after
    feature annotation. It contains the syllable string, its frequency
    count, and a dictionary of feature detection results.

    Attributes
    ----------
    syllable : str
        The canonical syllable string (from normalizer)
    frequency : int
        Occurrence count in the corpus (from frequency analysis)
    features : dict[str, bool]
        Dictionary mapping feature names to boolean detection results
        Example: {"starts_with_cluster": True, "contains_plosive": True, ...}

    Examples
    --------
    Create an annotated syllable::

        >>> record = AnnotatedSyllable(
        ...     syllable="kran",
        ...     frequency=7,
        ...     features={
        ...         "starts_with_cluster": True,
        ...         "contains_plosive": True,
        ...         "short_vowel": True,
        ...         # ... other features ...
        ...     }
        ... )
        >>> record.syllable
        'kran'
        >>> record.features["starts_with_cluster"]
        True

    Convert to dictionary (for JSON serialization)::

        >>> from dataclasses import asdict
        >>> record_dict = asdict(record)
        >>> record_dict["syllable"]
        'kran'

    Notes
    -----
    - All feature values must be boolean (True or False)
    - Frequency defaults to 1 if not found in frequency mapping
    - The features dict should contain all 12 feature detectors
    - Order of features in dict matches FEATURE_DETECTORS registry order
    """

    syllable: str
    frequency: int
    features: dict[str, bool]


@dataclass
class AnnotationStatistics:
    """
    Statistics about the annotation process.

    Tracks metadata about the annotation run, including counts,
    feature coverage, and performance metrics.

    Attributes
    ----------
    syllable_count : int
        Total number of syllables annotated
    feature_count : int
        Total number of features applied per syllable
    processing_time : float
        Time taken for annotation in seconds
    total_frequency : int
        Sum of all syllable frequencies (total corpus size)

    Examples
    --------
    Create statistics manually::

        >>> stats = AnnotationStatistics(
        ...     syllable_count=1523,
        ...     feature_count=12,
        ...     processing_time=0.34,
        ...     total_frequency=8472
        ... )
        >>> stats.syllable_count
        1523

    Access statistics from result::

        >>> result = run_annotation_pipeline(...)  # doctest: +SKIP
        >>> print(f"Processed {result.statistics.syllable_count} syllables")
        >>> print(f"Time: {result.statistics.processing_time:.2f}s")

    Notes
    -----
    - processing_time uses time.perf_counter() for precision
    - total_frequency represents pre-deduplication corpus size
    - feature_count should always be 12 (current feature set size)
    """

    syllable_count: int
    feature_count: int
    processing_time: float
    total_frequency: int


@dataclass
class AnnotationResult:
    """
    Complete annotation result with syllables and metadata.

    Encapsulates the full output of the annotation process, including
    all annotated syllables and processing statistics.

    Attributes
    ----------
    annotated_syllables : list[AnnotatedSyllable]
        List of all annotated syllable records
    statistics : AnnotationStatistics
        Metadata about the annotation process

    Examples
    --------
    Access annotated syllables::

        >>> result = run_annotation_pipeline(...)  # doctest: +SKIP
        >>> for record in result.annotated_syllables[:3]:
        ...     print(f"{record.syllable}: {record.frequency}")

    Get statistics::

        >>> result.statistics.syllable_count  # doctest: +SKIP
        1523

    Convert to JSON-serializable format::

        >>> from dataclasses import asdict
        >>> output = [asdict(syl) for syl in result.annotated_syllables]

    Notes
    -----
    - annotated_syllables list order matches input syllables order
    - Each syllable appears exactly once (no duplicates)
    - statistics provides overview of the annotation run
    """

    annotated_syllables: list[AnnotatedSyllable]
    statistics: AnnotationStatistics


def annotate_syllable(
    syllable: str,
    frequency: int,
    detectors: Mapping[str, Callable[[str], bool]],
) -> AnnotatedSyllable:
    """
    Apply all feature detectors to a single syllable.

    This is the core annotation function. It mechanically applies each
    feature detector to the syllable and assembles the results into an
    AnnotatedSyllable record.

    The function is pure: it has no side effects and always produces
    the same output for the same inputs.

    Parameters
    ----------
    syllable : str
        The syllable string to annotate
    frequency : int
        Occurrence count for this syllable
    detectors : dict[str, Callable[[str], bool]]
        Dictionary mapping feature names to detector functions
        (typically FEATURE_DETECTORS from feature_rules.py)

    Returns
    -------
    AnnotatedSyllable
        Complete annotated record with all feature detection results

    Examples
    --------
    Annotate a simple syllable::

        >>> from build_tools.syllable_feature_annotator.feature_rules import FEATURE_DETECTORS
        >>> record = annotate_syllable("ka", 187, FEATURE_DETECTORS)
        >>> record.syllable
        'ka'
        >>> record.frequency
        187
        >>> record.features["starts_with_cluster"]
        False
        >>> record.features["short_vowel"]
        True

    Annotate a complex cluster::

        >>> record = annotate_syllable("spla", 2, FEATURE_DETECTORS)
        >>> record.features["starts_with_heavy_cluster"]
        True
        >>> record.features["contains_liquid"]
        True

    Notes
    -----
    - Function is deterministic (same input → same output)
    - All detectors are applied (no short-circuiting or skipping)
    - Features are stored in detector iteration order
    - No validation or filtering of results
    - Empty syllables will produce all-False features
    - Processing is fast: O(n*m) where n=syllable length, m=detector count
    """
    # Apply each detector and store result
    features = {name: detector(syllable) for name, detector in detectors.items()}

    # Assemble annotated record
    return AnnotatedSyllable(syllable=syllable, frequency=frequency, features=features)


def annotate_corpus(
    syllables: list[str],
    frequencies: dict[str, int],
    detectors: Mapping[str, Callable[[str], bool]],
) -> AnnotationResult:
    """
    Annotate entire syllable corpus with feature detection.

    Processes a list of syllables and produces annotated records with
    feature detection results and processing statistics.

    This is a pure function with no I/O operations. It takes data
    structures as input and returns data structures as output.

    Parameters
    ----------
    syllables : list[str]
        List of syllable strings to annotate (typically from syllables_unique.txt)
    frequencies : dict[str, int]
        Dictionary mapping syllables to occurrence counts
        (typically from syllables_frequencies.json)
    detectors : dict[str, Callable[[str], bool]]
        Dictionary mapping feature names to detector functions
        (typically FEATURE_DETECTORS from feature_rules.py)

    Returns
    -------
    AnnotationResult
        Complete result with annotated syllables and statistics

    Examples
    --------
    Annotate a small corpus::

        >>> from build_tools.syllable_feature_annotator.feature_rules import FEATURE_DETECTORS
        >>> syllables = ["ka", "kran", "spla"]
        >>> frequencies = {"ka": 187, "kran": 7, "spla": 2}
        >>> result = annotate_corpus(syllables, frequencies, FEATURE_DETECTORS)
        >>> result.statistics.syllable_count
        3
        >>> result.statistics.feature_count
        12

    Handle missing frequency (defaults to 1)::

        >>> syllables = ["xyz"]
        >>> frequencies = {}  # Empty frequency dict
        >>> result = annotate_corpus(syllables, frequencies, FEATURE_DETECTORS)
        >>> result.annotated_syllables[0].frequency
        1

    Check processing time::

        >>> result = annotate_corpus(syllables, frequencies, FEATURE_DETECTORS)
        >>> result.statistics.processing_time < 1.0  # Should be very fast
        True

    Notes
    -----
    - Syllables are processed in input order (deterministic)
    - Missing frequencies default to 1 (no error raised)
    - All syllables are processed (no filtering or exclusion)
    - Processing time uses time.perf_counter() for precision
    - Function is deterministic (same inputs → same outputs)
    - Memory usage: O(n) where n = number of syllables
    """
    start_time = time.perf_counter()

    # Annotate each syllable
    annotated = []
    for syllable in syllables:
        frequency = frequencies.get(syllable, 1)  # Default to 1 if missing
        record = annotate_syllable(syllable, frequency, detectors)
        annotated.append(record)

    end_time = time.perf_counter()
    processing_time = end_time - start_time

    # Calculate statistics
    statistics = AnnotationStatistics(
        syllable_count=len(syllables),
        feature_count=len(detectors),
        processing_time=processing_time,
        total_frequency=sum(frequencies.get(syl, 1) for syl in syllables),
    )

    return AnnotationResult(annotated_syllables=annotated, statistics=statistics)


def run_annotation_pipeline(
    syllables_path: Path,
    frequencies_path: Path,
    output_path: Path,
    verbose: bool = False,
) -> AnnotationResult:
    """
    Run complete end-to-end annotation pipeline with I/O.

    This is the main entry point for the annotation tool. It:
    1. Loads syllables from file
    2. Loads frequencies from file
    3. Annotates corpus
    4. Saves output to file
    5. Returns results

    Parameters
    ----------
    syllables_path : Path
        Path to syllables text file (one per line)
        Example: data/normalized/syllables_unique.txt
    frequencies_path : Path
        Path to frequencies JSON file
        Example: data/normalized/syllables_frequencies.json
    output_path : Path
        Path where annotated JSON should be written
        Example: data/annotated/syllables_annotated.json
    verbose : bool, optional
        If True, print progress information (default: False)

    Returns
    -------
    AnnotationResult
        Complete annotation result with syllables and statistics

    Raises
    ------
    FileNotFoundError
        If input files don't exist
    ValueError
        If input data is malformed
    IOError
        If there are file permission or disk errors

    Examples
    --------
    Run full pipeline::

        >>> from pathlib import Path
        >>> result = run_annotation_pipeline(
        ...     syllables_path=Path("data/normalized/syllables_unique.txt"),
        ...     frequencies_path=Path("data/normalized/syllables_frequencies.json"),
        ...     output_path=Path("data/annotated/syllables_annotated.json"),
        ...     verbose=True
        ... )
        Loading syllables...
        Loading frequencies...
        Annotating corpus...
        Saving results...
        Annotated 1523 syllables in 0.34s

    Check results::

        >>> print(f"Processed {result.statistics.syllable_count} syllables")
        >>> print(f"Time: {result.statistics.processing_time:.2f}s")

    Notes
    -----
    - Input files must exist and be readable
    - Output directory is created automatically if needed
    - Output file is overwritten if it exists
    - Processing is deterministic (same inputs → same outputs)
    - Verbose mode prints progress to stdout
    - All exceptions from file I/O propagate to caller
    """
    if verbose:
        print(f"Loading syllables from {syllables_path}...")
    syllables = file_io.load_syllables(syllables_path)

    if verbose:
        print(f"Loading frequencies from {frequencies_path}...")
    frequencies = file_io.load_frequencies(frequencies_path)

    if verbose:
        print(f"Annotating {len(syllables)} syllables...")
    result = annotate_corpus(syllables, frequencies, FEATURE_DETECTORS)

    if verbose:
        print(f"Saving annotated syllables to {output_path}...")

    # Convert annotated syllables to dictionaries for JSON serialization
    from dataclasses import asdict

    syllables_as_dicts = [asdict(record) for record in result.annotated_syllables]
    file_io.save_annotated_syllables(syllables_as_dicts, output_path)

    if verbose:
        print("\nAnnotation complete!")
        print(f"  Syllables annotated: {result.statistics.syllable_count:,}")
        print(f"  Features per syllable: {result.statistics.feature_count}")
        print(f"  Total corpus frequency: {result.statistics.total_frequency:,}")
        print(f"  Processing time: {result.statistics.processing_time:.3f}s")
        print(f"  Output saved to: {output_path}")

    return result
