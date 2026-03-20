"""
Core combination logic for name candidate generation.

This module provides the main combination functionality that takes an
annotated syllable corpus and produces N-syllable name candidates with
aggregated feature vectors.

The combiner is intentionally simple - it performs structural combination
without any policy evaluation. Policy-based filtering is the responsibility
of the name_selector module.

Combination Strategy
--------------------
The default combination strategy uses frequency-weighted random sampling:

1. Load annotated syllables with their frequencies
2. Build a weighted probability distribution (higher frequency = more likely)
3. Sample N syllables using the isolated RNG instance
4. Concatenate syllables to form a name
5. Aggregate features using the rules in aggregator.py

This produces candidates that reflect the natural distribution of the corpus
while maintaining full determinism through seed control.

Determinism
-----------
**Critical**: All combination uses `random.Random(seed)` to create isolated
RNG instances. This ensures:

- Same seed always produces identical candidates
- No global state contamination
- Reproducible builds across sessions

Usage
-----
>>> from build_tools.name_combiner.combiner import combine_syllables
>>> candidates = combine_syllables(
...     annotated_data=corpus,
...     syllable_count=2,
...     count=100,
...     seed=42,
... )
>>> for c in candidates[:3]:
...     print(f"{c['name']}: score-ready features")
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from build_tools.name_combiner.aggregator import aggregate_features

if TYPE_CHECKING:
    from collections.abc import Sequence


def combine_syllables(
    annotated_data: Sequence[dict],
    syllable_count: int,
    count: int,
    seed: int | None = None,
    frequency_weight: float = 1.0,
) -> list[dict]:
    """
    Generate name candidates by combining syllables from an annotated corpus.

    Takes an annotated syllable corpus and produces N-syllable name candidates
    with aggregated feature vectors suitable for policy evaluation.

    Parameters
    ----------
    annotated_data : Sequence[dict]
        List of annotated syllable dictionaries, each containing:
        - "syllable": str - The syllable text
        - "frequency": int - Occurrence count in source corpus
        - "features": dict[str, bool] - The 12 boolean features

    syllable_count : int
        Number of syllables per generated name (typically 2, 3, or 4).

    count : int
        Number of candidates to generate.

    seed : int | None, optional
        RNG seed for deterministic output. If None, uses system entropy.
        Default: None.

    frequency_weight : float, optional
        Weight for frequency-biased sampling. 0.0 = uniform sampling,
        1.0 = fully frequency-weighted. Values between 0 and 1 interpolate.
        Default: 1.0.

    Returns
    -------
    list[dict]
        List of candidate dictionaries, each containing:
        - "name": str - The combined name (concatenated syllables)
        - "syllables": list[str] - The constituent syllables
        - "features": dict[str, bool] - Aggregated name-level features

    Raises
    ------
    ValueError
        If annotated_data is empty or syllable_count < 1.

    Examples
    --------
    >>> corpus = [
    ...     {"syllable": "ka", "frequency": 100, "features": {...}},
    ...     {"syllable": "li", "frequency": 50, "features": {...}},
    ...     {"syllable": "ra", "frequency": 75, "features": {...}},
    ... ]
    >>> candidates = combine_syllables(corpus, syllable_count=2, count=5, seed=42)
    >>> len(candidates)
    5
    >>> candidates[0]["name"]  # Deterministic with seed=42
    'kali'  # Example output
    >>> candidates[0]["syllables"]
    ['ka', 'li']

    Notes
    -----
    **Determinism**: Uses `random.Random(seed)` for isolated RNG. Same seed
    always produces identical output.

    **Frequency Weighting**: Higher frequency syllables are more likely to
    be sampled. This reflects the natural distribution of the source corpus
    and tends to produce more "natural-sounding" combinations.

    **No Policy Evaluation**: This function performs structural combination
    only. Policy-based filtering is done by the name_selector module.
    """
    if not annotated_data:
        raise ValueError("Cannot combine from empty annotated data")
    if syllable_count < 1:
        raise ValueError(f"syllable_count must be >= 1, got {syllable_count}")
    if count < 1:
        raise ValueError(f"count must be >= 1, got {count}")

    # Create isolated RNG instance (critical for determinism)
    rng = random.Random(seed)  # nosec B311 - intentional seeded RNG for reproducibility

    # Build weighted probability distribution
    syllables_list = list(annotated_data)
    weights = _compute_weights(syllables_list, frequency_weight)

    candidates: list[dict] = []

    for _ in range(count):
        # Sample N syllables with replacement
        selected = rng.choices(syllables_list, weights=weights, k=syllable_count)

        # Build candidate
        name = "".join(s["syllable"] for s in selected)
        syllable_texts = [s["syllable"] for s in selected]
        features = aggregate_features(selected)

        candidates.append(
            {
                "name": name,
                "syllables": syllable_texts,
                "features": features,
            }
        )

    return candidates


def _compute_weights(
    annotated_data: Sequence[dict],
    frequency_weight: float,
) -> list[float]:
    """
    Compute sampling weights from syllable frequencies.

    Parameters
    ----------
    annotated_data : Sequence[dict]
        Annotated syllables with "frequency" key.

    frequency_weight : float
        Interpolation factor: 0.0 = uniform, 1.0 = fully weighted.

    Returns
    -------
    list[float]
        Sampling weights (not normalized, random.choices handles that).
    """
    if frequency_weight <= 0.0:
        # Uniform weights
        return [1.0] * len(annotated_data)

    frequencies = [s.get("frequency", 1) for s in annotated_data]

    if frequency_weight >= 1.0:
        # Fully frequency-weighted
        return [float(f) for f in frequencies]

    # Interpolate between uniform and frequency-weighted
    uniform = 1.0
    return [uniform * (1.0 - frequency_weight) + float(f) * frequency_weight for f in frequencies]
