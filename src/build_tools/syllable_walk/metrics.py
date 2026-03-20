"""
Corpus shape metrics computation.

This module provides dataclasses and pure functions for computing raw,
objective metrics about corpus shape. These metrics characterize the
statistical structure of a syllable corpus without interpretation.

Design Philosophy:
    - Raw numbers only, no interpretation or judgment
    - Pure functions (no side effects, no I/O)
    - All metrics are observable facts about the corpus
    - Users draw their own conclusions from the data

Metric Categories:
    - Inventory: What exists (counts, lengths)
    - Frequency: Weight distribution (how syllables are distributed)
    - Feature Saturation: Phonetic feature coverage (per-feature counts)

Usage:
    >>> from build_tools.syllable_walk.metrics import (
    ...     compute_corpus_shape_metrics
    ... )
    >>> metrics = compute_corpus_shape_metrics(syllables, frequencies, annotated_data)
    >>> print(f"Total syllables: {metrics.inventory.total_count}")
    >>> print(f"Hapax count: {metrics.frequency.hapax_count}")
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from build_tools.syllable_walk.terrain_weights import (
    DEFAULT_TERRAIN_WEIGHTS,
    AxisWeights,
    TerrainWeights,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

# =============================================================================
# Inventory Metrics
# =============================================================================


@dataclass(frozen=True)
class InventoryMetrics:
    """
    Raw inventory metrics describing what exists in the corpus.

    All metrics are objective counts and statistics about syllable inventory.

    Attributes:
        total_count: Total number of unique syllables
        length_min: Minimum syllable length (characters)
        length_max: Maximum syllable length (characters)
        length_mean: Mean syllable length
        length_median: Median syllable length
        length_std: Standard deviation of syllable lengths
        length_distribution: Count of syllables at each length {length: count}
    """

    total_count: int
    length_min: int
    length_max: int
    length_mean: float
    length_median: float
    length_std: float
    length_distribution: dict[int, int] = field(default_factory=dict)


def compute_inventory_metrics(syllables: Sequence[str]) -> InventoryMetrics:
    """
    Compute inventory metrics from a list of syllables.

    Args:
        syllables: List of unique syllables

    Returns:
        InventoryMetrics with all computed values

    Raises:
        ValueError: If syllables list is empty
    """
    if not syllables:
        raise ValueError("Cannot compute metrics for empty syllable list")

    lengths = [len(s) for s in syllables]

    # Build length distribution
    length_dist: dict[int, int] = {}
    for length in lengths:
        length_dist[length] = length_dist.get(length, 0) + 1

    # Handle edge case of single syllable (stdev requires 2+ values)
    length_std = 0.0
    if len(lengths) >= 2:
        length_std = statistics.stdev(lengths)

    return InventoryMetrics(
        total_count=len(syllables),
        length_min=min(lengths),
        length_max=max(lengths),
        length_mean=statistics.mean(lengths),
        length_median=statistics.median(lengths),
        length_std=length_std,
        length_distribution=dict(sorted(length_dist.items())),
    )


# =============================================================================
# Frequency Metrics
# =============================================================================


@dataclass(frozen=True)
class FrequencyMetrics:
    """
    Raw frequency distribution metrics.

    Describes how syllable occurrences are distributed across the corpus.

    Attributes:
        total_occurrences: Sum of all frequency counts
        freq_min: Minimum frequency value
        freq_max: Maximum frequency value
        freq_mean: Mean frequency
        freq_median: Median frequency
        freq_std: Standard deviation of frequencies
        percentile_10: 10th percentile frequency
        percentile_25: 25th percentile frequency (Q1)
        percentile_50: 50th percentile frequency (median)
        percentile_75: 75th percentile frequency (Q3)
        percentile_90: 90th percentile frequency
        percentile_99: 99th percentile frequency
        unique_freq_count: Number of distinct frequency values
        hapax_count: Count of syllables appearing exactly once
        top_10: Top 10 syllables by frequency [(syllable, freq), ...]
        bottom_10: Bottom 10 syllables by frequency [(syllable, freq), ...]
    """

    total_occurrences: int
    freq_min: int
    freq_max: int
    freq_mean: float
    freq_median: float
    freq_std: float
    percentile_10: int
    percentile_25: int
    percentile_50: int
    percentile_75: int
    percentile_90: int
    percentile_99: int
    unique_freq_count: int
    hapax_count: int
    top_10: tuple[tuple[str, int], ...] = field(default_factory=tuple)
    bottom_10: tuple[tuple[str, int], ...] = field(default_factory=tuple)


def compute_frequency_metrics(frequencies: dict[str, int]) -> FrequencyMetrics:
    """
    Compute frequency distribution metrics.

    Args:
        frequencies: Dictionary mapping syllable to frequency count

    Returns:
        FrequencyMetrics with all computed values

    Raises:
        ValueError: If frequencies dict is empty
    """
    if not frequencies:
        raise ValueError("Cannot compute metrics for empty frequencies dict")

    freq_values = list(frequencies.values())
    freq_array = np.array(freq_values, dtype=np.int64)

    # Compute percentiles
    percentiles = np.percentile(freq_array, [10, 25, 50, 75, 90, 99])

    # Count hapax legomena (frequency = 1)
    hapax_count = sum(1 for f in freq_values if f == 1)

    # Unique frequency values
    unique_freq_count = len(set(freq_values))

    # Sort for top/bottom
    sorted_by_freq = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
    top_10 = tuple(sorted_by_freq[:10])
    bottom_10 = tuple(sorted_by_freq[-10:][::-1])  # Reverse to show lowest first

    # Handle edge case of single entry
    freq_std = 0.0
    if len(freq_values) >= 2:
        freq_std = statistics.stdev(freq_values)

    return FrequencyMetrics(
        total_occurrences=sum(freq_values),
        freq_min=min(freq_values),
        freq_max=max(freq_values),
        freq_mean=statistics.mean(freq_values),
        freq_median=statistics.median(freq_values),
        freq_std=freq_std,
        percentile_10=int(percentiles[0]),
        percentile_25=int(percentiles[1]),
        percentile_50=int(percentiles[2]),
        percentile_75=int(percentiles[3]),
        percentile_90=int(percentiles[4]),
        percentile_99=int(percentiles[5]),
        unique_freq_count=unique_freq_count,
        hapax_count=hapax_count,
        top_10=top_10,
        bottom_10=bottom_10,
    )


# =============================================================================
# Feature Saturation Metrics
# =============================================================================

# Canonical feature order (matches annotator output)
FEATURE_NAMES: tuple[str, ...] = (
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
)


@dataclass(frozen=True)
class FeatureSaturation:
    """
    Saturation metrics for a single phonetic feature.

    Attributes:
        feature_name: Name of the feature
        true_count: Number of syllables with feature = True
        false_count: Number of syllables with feature = False
        true_percentage: Percentage of corpus with feature = True
    """

    feature_name: str
    true_count: int
    false_count: int
    true_percentage: float


@dataclass(frozen=True)
class FeatureSaturationMetrics:
    """
    Feature saturation metrics for all 12 phonetic features.

    Attributes:
        total_syllables: Total syllables analyzed
        features: Tuple of FeatureSaturation for each feature (in canonical order)
        by_name: Dict mapping feature name to FeatureSaturation (for lookup)
    """

    total_syllables: int
    features: tuple[FeatureSaturation, ...] = field(default_factory=tuple)
    by_name: dict[str, FeatureSaturation] = field(default_factory=dict)


def compute_feature_saturation_metrics(
    annotated_data: Sequence[dict],
) -> FeatureSaturationMetrics:
    """
    Compute feature saturation metrics from annotated syllable data.

    Args:
        annotated_data: List of dicts with 'syllable', 'frequency', 'features' keys

    Returns:
        FeatureSaturationMetrics with per-feature saturation counts

    Raises:
        ValueError: If annotated_data is empty or malformed
    """
    if not annotated_data:
        raise ValueError("Cannot compute metrics for empty annotated data")

    # Validate first entry has expected structure
    first = annotated_data[0]
    if "features" not in first:
        raise ValueError("Annotated data entries must have 'features' key")

    total = len(annotated_data)

    # Count True values for each feature
    feature_counts: dict[str, int] = {name: 0 for name in FEATURE_NAMES}

    for entry in annotated_data:
        features = entry.get("features", {})
        for name in FEATURE_NAMES:
            if features.get(name, False):
                feature_counts[name] += 1

    # Build FeatureSaturation objects
    saturations: list[FeatureSaturation] = []
    by_name: dict[str, FeatureSaturation] = {}

    for name in FEATURE_NAMES:
        true_count = feature_counts[name]
        false_count = total - true_count
        true_pct = (true_count / total) * 100.0 if total > 0 else 0.0

        sat = FeatureSaturation(
            feature_name=name,
            true_count=true_count,
            false_count=false_count,
            true_percentage=true_pct,
        )
        saturations.append(sat)
        by_name[name] = sat

    return FeatureSaturationMetrics(
        total_syllables=total,
        features=tuple(saturations),
        by_name=by_name,
    )


# =============================================================================
# Terrain Metrics (Phonaesthetic Axes)
# =============================================================================

# Weights are defined in terrain_weights.py with full phonaesthetic rationale.
# See that module for documentation of each weight's justification.
#
# IMPORTANT: Each axis must be BIPOLAR - features pulling BOTH directions.
# Without this, axes measure "Englishness" not phonaesthetic shape.
# See Section 12 of _working/sfa_shapes_terrain_map.md for calibration findings.


@dataclass(frozen=True)
class PoleExemplars:
    """
    Exemplar syllables from each pole of a terrain axis.

    These concrete examples help users understand what syllables
    represent each end of the phonaesthetic spectrum.

    Attributes:
        axis_name: Name of the axis ("shape", "craft", or "space")
        low_pole_exemplars: Syllables from the low pole (Round/Flowing/Open)
        high_pole_exemplars: Syllables from the high pole (Jagged/Worked/Dense)
    """

    axis_name: str
    low_pole_exemplars: tuple[str, ...]
    high_pole_exemplars: tuple[str, ...]


@dataclass(frozen=True)
class TerrainMetrics:
    """
    Phonaesthetic terrain metrics describing corpus character.

    Three axes derived from feature saturation percentages:
    - Shape: Round (0.0) ↔ Jagged (1.0) - Bouba/Kiki dimension
    - Craft: Flowing (0.0) ↔ Worked (1.0) - Sung/Forged dimension
    - Space: Open (0.0) ↔ Dense (1.0) - Valley/Workshop dimension

    Scores are normalized to 0.0-1.0 range where 0.5 is neutral.

    Attributes:
        shape_score: Position on Round↔Jagged axis (0.0-1.0)
        craft_score: Position on Flowing↔Worked axis (0.0-1.0)
        space_score: Position on Open↔Dense axis (0.0-1.0)
        shape_label: Human-readable label for shape position
        craft_label: Human-readable label for craft position
        space_label: Human-readable label for space position
        shape_exemplars: Optional exemplar syllables for shape axis
        craft_exemplars: Optional exemplar syllables for craft axis
        space_exemplars: Optional exemplar syllables for space axis
    """

    shape_score: float
    craft_score: float
    space_score: float
    shape_label: str
    craft_label: str
    space_label: str
    shape_exemplars: PoleExemplars | None = None
    craft_exemplars: PoleExemplars | None = None
    space_exemplars: PoleExemplars | None = None


def _compute_axis_score(
    feature_saturation: FeatureSaturationMetrics,
    axis_weights: AxisWeights,
) -> float:
    """
    Compute a single axis score from weighted feature percentages.

    Args:
        feature_saturation: Feature saturation metrics
        axis_weights: AxisWeights containing feature-to-weight mappings

    Returns:
        Score normalized to 0.0-1.0 range (0.5 = neutral)
    """
    # Compute weighted sum of feature percentages (as 0-1 values)
    weighted_sum = 0.0
    total_weight = 0.0

    for feature_name, weight in axis_weights.items():
        if feature_name in feature_saturation.by_name:
            pct = feature_saturation.by_name[feature_name].true_percentage / 100.0
            weighted_sum += pct * weight
            total_weight += abs(weight)

    if total_weight == 0:
        return 0.5  # Neutral if no features match

    # Normalize: weighted_sum can range from -total_weight to +total_weight
    # Map to 0.0-1.0 where 0.5 is neutral
    normalized = (weighted_sum / total_weight + 1.0) / 2.0

    # Clamp to valid range
    return max(0.0, min(1.0, normalized))


def score_syllable_on_axis(
    features: dict[str, bool],
    axis_weights: AxisWeights,
) -> float:
    """
    Compute axis score for a single syllable from its boolean features.

    Unlike _compute_axis_score() which uses corpus percentages, this uses
    binary features (0 or 1) to rank individual syllables.

    Args:
        features: Dictionary of feature_name -> boolean
        axis_weights: AxisWeights containing feature-to-weight mappings

    Returns:
        Raw weighted sum (not normalized). Higher = more toward high pole.
    """
    weighted_sum = 0.0
    for feature_name, weight in axis_weights.items():
        if features.get(feature_name, False):
            weighted_sum += weight
    return weighted_sum


def sample_pole_exemplars(
    annotated_data: Sequence[dict],
    axis_weights: AxisWeights,
    axis_name: str,
    n_exemplars: int = 3,
    rng: random.Random | None = None,
) -> PoleExemplars:
    """
    Sample exemplar syllables from each pole of an axis.

    Scores all syllables in the corpus and samples from the low and high
    tails to provide concrete examples of syllables at each pole.

    Args:
        annotated_data: List of {"syllable": str, "features": dict} entries
        axis_weights: Weights for the axis
        axis_name: Name of axis ("shape", "craft", "space")
        n_exemplars: Number of exemplars per pole (default 3)
        rng: Optional RNG for shuffling within tails (isolated from generation)

    Returns:
        PoleExemplars with syllables from low and high poles
    """
    if not annotated_data:
        return PoleExemplars(
            axis_name=axis_name,
            low_pole_exemplars=(),
            high_pole_exemplars=(),
        )

    # Score all syllables
    scored = [
        (entry["syllable"], score_syllable_on_axis(entry["features"], axis_weights))
        for entry in annotated_data
    ]

    # Shuffle BEFORE sorting if RNG provided - this randomizes tie-breaking
    # (Python's sort is stable, so equal scores would otherwise stay in
    # original alphabetical order, always giving 'a' syllables for low pole
    # and 'z' syllables for high pole)
    if rng:
        rng.shuffle(scored)

    # Sort by score (ascending: low pole first, high pole last)
    scored.sort(key=lambda x: x[1])

    # Take exemplars directly from the sorted tails
    low_exemplars = tuple(s[0] for s in scored[:n_exemplars])
    high_exemplars = tuple(s[0] for s in scored[-n_exemplars:])

    return PoleExemplars(
        axis_name=axis_name,
        low_pole_exemplars=low_exemplars,
        high_pole_exemplars=high_exemplars,
    )


def _score_to_label(score: float, low_label: str, high_label: str) -> str:
    """
    Convert a 0-1 score to a human-readable label.

    Args:
        score: Value from 0.0 to 1.0
        low_label: Label for low end (e.g., "ROUND")
        high_label: Label for high end (e.g., "JAGGED")

    Returns:
        Appropriate label based on score position
    """
    if score < 0.35:
        return low_label
    elif score > 0.65:
        return high_label
    else:
        return "BALANCED"


def compute_terrain_metrics(
    feature_saturation: FeatureSaturationMetrics,
    weights: TerrainWeights | None = None,
    annotated_data: Sequence[dict] | None = None,
    exemplar_rng: random.Random | None = None,
    n_exemplars: int = 3,
) -> TerrainMetrics:
    """
    Compute phonaesthetic terrain metrics from feature saturation.

    Derives three axis scores representing the corpus's position in
    phonaesthetic space. These are descriptive, not prescriptive -
    they characterize the acoustic terrain without imposing meaning.

    Args:
        feature_saturation: Computed feature saturation metrics
        weights: Optional TerrainWeights configuration. If None, uses
                 DEFAULT_TERRAIN_WEIGHTS from terrain_weights module.
                 Custom weights allow calibration for different phonaesthetic
                 models or user preferences.
        annotated_data: Optional list of {"syllable": str, "features": dict}
                        entries. If provided, pole exemplars will be computed.
        exemplar_rng: Optional RNG for shuffling exemplars. Isolated from
                      name generation to maintain determinism.
        n_exemplars: Number of exemplars per pole (default 3)

    Returns:
        TerrainMetrics with scores and labels for all three axes

    Example:
        >>> terrain = compute_terrain_metrics(feature_saturation)
        >>> print(f"Shape: {terrain.shape_score:.2f} ({terrain.shape_label})")
        >>> print(f"Craft: {terrain.craft_score:.2f} ({terrain.craft_label})")

        # With custom weights:
        >>> from build_tools.syllable_walk.terrain_weights import (
        ...     TerrainWeights, AxisWeights
        ... )
        >>> custom = TerrainWeights(shape=AxisWeights({"contains_plosive": 1.5}))
        >>> terrain = compute_terrain_metrics(feature_saturation, weights=custom)

        # With exemplars:
        >>> terrain = compute_terrain_metrics(
        ...     feature_saturation, annotated_data=corpus_data
        ... )
        >>> print(terrain.shape_exemplars.low_pole_exemplars)
    """
    if weights is None:
        weights = DEFAULT_TERRAIN_WEIGHTS

    shape_score = _compute_axis_score(feature_saturation, weights.shape)
    craft_score = _compute_axis_score(feature_saturation, weights.craft)
    space_score = _compute_axis_score(feature_saturation, weights.space)

    # Compute exemplars if annotated_data provided
    shape_exemplars = None
    craft_exemplars = None
    space_exemplars = None

    if annotated_data:
        shape_exemplars = sample_pole_exemplars(
            annotated_data, weights.shape, "shape", n_exemplars, exemplar_rng
        )
        craft_exemplars = sample_pole_exemplars(
            annotated_data, weights.craft, "craft", n_exemplars, exemplar_rng
        )
        space_exemplars = sample_pole_exemplars(
            annotated_data, weights.space, "space", n_exemplars, exemplar_rng
        )

    return TerrainMetrics(
        shape_score=shape_score,
        craft_score=craft_score,
        space_score=space_score,
        shape_label=_score_to_label(shape_score, "ROUND", "JAGGED"),
        craft_label=_score_to_label(craft_score, "FLOWING", "WORKED"),
        space_label=_score_to_label(space_score, "OPEN", "DENSE"),
        shape_exemplars=shape_exemplars,
        craft_exemplars=craft_exemplars,
        space_exemplars=space_exemplars,
    )


# =============================================================================
# Composite Corpus Shape Metrics
# =============================================================================


@dataclass(frozen=True)
class CorpusShapeMetrics:
    """
    Complete corpus shape metrics combining all categories.

    This is the primary interface for corpus analysis. Contains all raw
    metrics needed to understand corpus structure.

    Attributes:
        inventory: Inventory metrics (counts, lengths)
        frequency: Frequency distribution metrics
        feature_saturation: Per-feature saturation metrics
        terrain: Phonaesthetic terrain metrics (derived from features)
    """

    inventory: InventoryMetrics
    frequency: FrequencyMetrics
    feature_saturation: FeatureSaturationMetrics
    terrain: TerrainMetrics


def compute_corpus_shape_metrics(
    syllables: Sequence[str],
    frequencies: dict[str, int],
    annotated_data: Sequence[dict],
) -> CorpusShapeMetrics:
    """
    Compute complete corpus shape metrics.

    This is the main entry point for corpus analysis. Computes all metric
    categories and returns a composite result.

    Args:
        syllables: List of unique syllables
        frequencies: Dictionary mapping syllable to frequency count
        annotated_data: List of annotated syllable dicts

    Returns:
        CorpusShapeMetrics containing all computed metrics

    Raises:
        ValueError: If any input is empty or malformed

    Example:
        >>> metrics = compute_corpus_shape_metrics(syllables, frequencies, annotated_data)
        >>> print(f"Corpus has {metrics.inventory.total_count} syllables")
        >>> print(f"Hapax legomena: {metrics.frequency.hapax_count}")
        >>> vowel_pct = metrics.feature_saturation.by_name['starts_with_vowel'].true_percentage
        >>> print(f"Starts with vowel: {vowel_pct:.1f}%")
        >>> print(f"Terrain: {metrics.terrain.shape_label}")
    """
    feature_saturation = compute_feature_saturation_metrics(annotated_data)

    return CorpusShapeMetrics(
        inventory=compute_inventory_metrics(syllables),
        frequency=compute_frequency_metrics(frequencies),
        feature_saturation=feature_saturation,
        terrain=compute_terrain_metrics(feature_saturation, annotated_data=annotated_data),
    )
