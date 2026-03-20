"""
Feature aggregation for name-level evaluation.

This module implements the rules for aggregating syllable-level features
into name-level features. The aggregation produces a boolean feature vector
for each name candidate, enabling policy evaluation by the name_selector.

Aggregation Rules
-----------------
**Onset Features** (first syllable only):
    - starts_with_vowel
    - starts_with_cluster
    - starts_with_heavy_cluster

    These features describe how a name begins. Only the first syllable's
    onset features are relevant - internal syllable onsets don't affect
    how the name "enters" the listener's ear.

**Coda Features** (final syllable only):
    - ends_with_vowel
    - ends_with_nasal
    - ends_with_stop

    These features describe how a name ends. Only the final syllable's
    coda features are relevant - internal syllable codas don't affect
    how the name "lands" or closes.

**Internal Features** (OR across all syllables):
    - contains_plosive
    - contains_fricative
    - contains_liquid
    - contains_nasal

    These features describe the texture of a name. If ANY syllable contains
    the feature, the name has it. A name like "kalira" contains_liquid=True
    because "li" has a liquid, even though "ka" and "ra" might not.

**Nucleus Features** (majority rule):
    - short_vowel
    - long_vowel

    These features describe the dominant vowel character of a name.
    We use majority rule (>50% of syllables) to determine the name-level
    value. See the module docstring for detailed rationale.

Why Majority Rule for Nucleus Features
--------------------------------------
We use majority (>50% of syllables) rather than proportional scoring.

1. **Preserves Architectural Consistency**: The entire feature registry is
   built on boolean features. The policy matrix uses checkmark/tilde/cross
   symbols that map cleanly to boolean logic. Introducing fractional
   features would break this elegant simplicity.

2. **Keeps the Implementation Simple**: Majority rule means the name-level
   feature vector remains a simple boolean array, identical in structure
   to syllable-level vectors. No special cases, no type conversions.

3. **Sufficient for Initial Policy Evaluation**: For a first implementation,
   knowing "this name is mostly short-vowel" vs. "this name is mostly
   long-vowel" is enough information to make good selection decisions.
   Precise ratios are not needed yet.

4. **Easier to Debug and Explain**: When a name gets rejected, you can say
   "this name has short_vowel=true (2 of 3 syllables), which is discouraged
   for Place Names." That's clear and inspectable. Proportional scoring
   makes debugging harder.

5. **Aligns with Project Philosophy**: The system is about shape and
   suitability, not precise optimization. Majority rule captures the
   dominant character of a name, which is what matters for admissibility.

Future Consideration
--------------------
If finer-grained nucleus control is needed, proportional scoring could be
introduced as an optional mode. This would require extending the policy
matrix to handle float thresholds (e.g., short_vowel > 0.6). For now,
majority rule provides the right balance of simplicity and expressiveness.

Usage
-----
>>> from build_tools.name_combiner.aggregator import aggregate_features
>>> syllables = [
...     {"syllable": "ka", "features": {"starts_with_vowel": False, ...}},
...     {"syllable": "li", "features": {"contains_liquid": True, ...}},
... ]
>>> name_features = aggregate_features(syllables)
>>> name_features["starts_with_vowel"]  # From first syllable
False
>>> name_features["contains_liquid"]  # OR across all
True
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# Feature categories for aggregation
ONSET_FEATURES = frozenset(
    {
        "starts_with_vowel",
        "starts_with_cluster",
        "starts_with_heavy_cluster",
    }
)

CODA_FEATURES = frozenset(
    {
        "ends_with_vowel",
        "ends_with_nasal",
        "ends_with_stop",
    }
)

INTERNAL_FEATURES = frozenset(
    {
        "contains_plosive",
        "contains_fricative",
        "contains_liquid",
        "contains_nasal",
    }
)

NUCLEUS_FEATURES = frozenset(
    {
        "short_vowel",
        "long_vowel",
    }
)

# All 12 features in canonical order (matches feature_rules.py)
ALL_FEATURES = (
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


def aggregate_features(syllables: Sequence[dict]) -> dict[str, bool]:
    """
    Aggregate syllable-level features into a name-level feature vector.

    Takes a sequence of syllable dictionaries (each with a "features" key)
    and produces a single boolean feature vector for the combined name.

    Parameters
    ----------
    syllables : Sequence[dict]
        List of syllable dictionaries, each containing:
        - "syllable": str - The syllable text
        - "features": dict[str, bool] - The 12 boolean features

    Returns
    -------
    dict[str, bool]
        Name-level feature vector with all 12 features as booleans.

    Raises
    ------
    ValueError
        If syllables list is empty or missing required keys.

    Examples
    --------
    >>> syllables = [
    ...     {"syllable": "ka", "features": {
    ...         "starts_with_vowel": False,
    ...         "starts_with_cluster": False,
    ...         "starts_with_heavy_cluster": False,
    ...         "contains_plosive": True,
    ...         "contains_fricative": False,
    ...         "contains_liquid": False,
    ...         "contains_nasal": False,
    ...         "short_vowel": True,
    ...         "long_vowel": False,
    ...         "ends_with_vowel": True,
    ...         "ends_with_nasal": False,
    ...         "ends_with_stop": False,
    ...     }},
    ...     {"syllable": "li", "features": {
    ...         "starts_with_vowel": False,
    ...         "starts_with_cluster": False,
    ...         "starts_with_heavy_cluster": False,
    ...         "contains_plosive": False,
    ...         "contains_fricative": False,
    ...         "contains_liquid": True,
    ...         "contains_nasal": False,
    ...         "short_vowel": True,
    ...         "long_vowel": False,
    ...         "ends_with_vowel": True,
    ...         "ends_with_nasal": False,
    ...         "ends_with_stop": False,
    ...     }},
    ... ]
    >>> features = aggregate_features(syllables)
    >>> features["starts_with_vowel"]  # From first syllable ("ka")
    False
    >>> features["ends_with_vowel"]  # From final syllable ("li")
    True
    >>> features["contains_liquid"]  # OR: True because "li" has it
    True
    >>> features["short_vowel"]  # Majority: 2/2 = 100% > 50%
    True

    Notes
    -----
    Aggregation follows these rules:

    - **Onset** (starts_with_*): First syllable only
    - **Coda** (ends_with_*): Final syllable only
    - **Internal** (contains_*): OR across all syllables
    - **Nucleus** (short_vowel, long_vowel): Majority rule (>50%)

    See module docstring for detailed rationale on majority rule.
    """
    if not syllables:
        raise ValueError("Cannot aggregate features from empty syllable list")

    # Validate structure
    for i, syl in enumerate(syllables):
        if "features" not in syl:
            raise ValueError(f"Syllable at index {i} missing 'features' key")

    first_features = syllables[0]["features"]
    final_features = syllables[-1]["features"]

    result: dict[str, bool] = {}

    # Onset features: first syllable only
    for feature in ONSET_FEATURES:
        result[feature] = first_features.get(feature, False)

    # Coda features: final syllable only
    for feature in CODA_FEATURES:
        result[feature] = final_features.get(feature, False)

    # Internal features: OR across all syllables
    for feature in INTERNAL_FEATURES:
        result[feature] = any(syl["features"].get(feature, False) for syl in syllables)

    # Nucleus features: majority rule (>50%)
    total = len(syllables)
    for feature in NUCLEUS_FEATURES:
        count = sum(1 for syl in syllables if syl["features"].get(feature, False))
        # Majority means strictly more than half
        # For 2 syllables: need 2 (>1)
        # For 3 syllables: need 2 (>1.5)
        # For 4 syllables: need 3 (>2)
        result[feature] = count > total / 2

    return result
