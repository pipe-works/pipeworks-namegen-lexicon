"""
Policy evaluation logic for name candidates.

This module contains the core evaluation function that scores a name
candidate against a name class policy. It implements the ✓/~/✗ scoring
model defined in the Name Class Matrix.

Scoring Model
-------------
- **Preferred (✓)**: Feature present → +1 score
- **Tolerated (~)**: Feature present → 0 score (neutral)
- **Discouraged (✗)**: Feature present → Reject (hard) or -10 (soft)

The evaluation considers only features that are TRUE in the candidate.
Features that are FALSE do not contribute to the score (absence is neutral).

Evaluation Modes
----------------
**Hard Mode** (default):
    Any discouraged feature present causes immediate rejection.
    The candidate is not scored further.

**Soft Mode**:
    Discouraged features apply a -10 penalty instead of rejection.
    Useful for exploring edge cases or when flexibility is needed.

Usage
-----
>>> from build_tools.name_selector.policy import evaluate_candidate
>>> from build_tools.name_selector.name_class import NameClassPolicy
>>>
>>> policy = NameClassPolicy(
...     name="first_name",
...     description="Test",
...     syllable_range=(2, 3),
...     features={"ends_with_vowel": "preferred", "ends_with_stop": "discouraged"},
... )
>>> candidate = {
...     "name": "kali",
...     "features": {"ends_with_vowel": True, "ends_with_stop": False},
... }
>>> admitted, score, details = evaluate_candidate(candidate, policy, mode="hard")
>>> admitted
True
>>> score
1
>>> details["preferred_hits"]
['ends_with_vowel']
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from build_tools.name_selector.name_class import NameClassPolicy

# Scoring constants
PREFERRED_SCORE = 1
TOLERATED_SCORE = 0
DISCOURAGED_PENALTY = -10  # Used in soft mode


def evaluate_candidate(
    candidate: dict,
    policy: NameClassPolicy,
    mode: Literal["hard", "soft"] = "hard",
) -> tuple[bool, int, dict]:
    """
    Evaluate a name candidate against a name class policy.

    Scores the candidate based on which of its TRUE features match
    preferred, tolerated, or discouraged designations in the policy.

    Parameters
    ----------
    candidate : dict
        Candidate dictionary with "name", "features", and optionally "syllables".
        Features must be a dict[str, bool].

    policy : NameClassPolicy
        The policy to evaluate against.

    mode : {"hard", "soft"}, optional
        Evaluation mode. "hard" rejects on any discouraged feature.
        "soft" applies a -10 penalty instead. Default: "hard".

    Returns
    -------
    tuple[bool, int, dict]
        - admitted: True if candidate passes policy, False if rejected
        - score: Numeric score (higher is better)
        - details: Evaluation details for debugging

    Details dict structure:
        - preferred_hits: list[str] - Preferred features that are TRUE
        - tolerated_hits: list[str] - Tolerated features that are TRUE
        - discouraged_hits: list[str] - Discouraged features that are TRUE
        - rejection_reason: str | None - Reason for rejection (if any)

    Examples
    --------
    >>> # Candidate with preferred feature
    >>> candidate = {"name": "kali", "features": {"ends_with_vowel": True}}
    >>> admitted, score, details = evaluate_candidate(candidate, policy)
    >>> admitted, score
    (True, 1)

    >>> # Candidate with discouraged feature (hard mode)
    >>> candidate = {"name": "kalt", "features": {"ends_with_stop": True}}
    >>> admitted, score, details = evaluate_candidate(candidate, policy, mode="hard")
    >>> admitted
    False
    >>> details["rejection_reason"]
    'ends_with_stop'

    Notes
    -----
    Only TRUE features are evaluated. If a feature is FALSE in the candidate,
    it does not contribute to the score regardless of its policy designation.

    This means "discouraged" means "discouraged when present", not
    "required to be absent".
    """
    features = candidate.get("features", {})

    preferred_hits: list[str] = []
    tolerated_hits: list[str] = []
    discouraged_hits: list[str] = []

    score = 0

    # Evaluate each feature that is TRUE in the candidate
    for feature_name, is_present in features.items():
        if not is_present:
            # Feature is FALSE - does not contribute
            continue

        # Get policy for this feature (default to tolerated if not specified)
        policy_value = policy.features.get(feature_name, "tolerated")

        if policy_value == "preferred":
            preferred_hits.append(feature_name)
            score += PREFERRED_SCORE
        elif policy_value == "tolerated":
            tolerated_hits.append(feature_name)
            score += TOLERATED_SCORE
        elif policy_value == "discouraged":
            discouraged_hits.append(feature_name)
            if mode == "hard":
                # Hard mode: immediate rejection
                return (
                    False,
                    score,
                    {
                        "preferred_hits": preferred_hits,
                        "tolerated_hits": tolerated_hits,
                        "discouraged_hits": discouraged_hits,
                        "rejection_reason": feature_name,
                    },
                )
            else:
                # Soft mode: apply penalty
                score += DISCOURAGED_PENALTY

    # Build details
    details = {
        "preferred_hits": preferred_hits,
        "tolerated_hits": tolerated_hits,
        "discouraged_hits": discouraged_hits,
        "rejection_reason": None,
    }

    # In soft mode, check if cumulative penalties make this unviable
    # (optional: could add a threshold here)

    return (True, score, details)


def check_syllable_count(
    candidate: dict,
    policy: NameClassPolicy,
) -> bool:
    """
    Check if a candidate's syllable count is within policy range.

    Parameters
    ----------
    candidate : dict
        Candidate dictionary with "syllables" key (list of syllable strings).

    policy : NameClassPolicy
        The policy with syllable_range constraint.

    Returns
    -------
    bool
        True if syllable count is within range, False otherwise.

    Examples
    --------
    >>> policy = NameClassPolicy(..., syllable_range=(2, 3))
    >>> check_syllable_count({"syllables": ["ka", "li"]}, policy)
    True
    >>> check_syllable_count({"syllables": ["ka"]}, policy)
    False
    """
    syllables = candidate.get("syllables", [])
    count = len(syllables)
    min_syl, max_syl = policy.syllable_range
    return min_syl <= count <= max_syl
