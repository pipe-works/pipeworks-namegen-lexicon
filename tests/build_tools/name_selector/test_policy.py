"""Tests for policy evaluation logic."""

from build_tools.name_selector.name_class import NameClassPolicy
from build_tools.name_selector.policy import (
    DISCOURAGED_PENALTY,
    PREFERRED_SCORE,
    TOLERATED_SCORE,
    check_syllable_count,
    evaluate_candidate,
)


def make_policy(**feature_policies) -> NameClassPolicy:
    """Helper to create a policy with specified feature policies."""
    return NameClassPolicy(
        name="test",
        description="Test policy",
        syllable_range=(2, 3),
        features=feature_policies,
    )


def make_candidate(name: str, syllables: list[str], **features: bool) -> dict:
    """Helper to create a candidate with specified features."""
    # Default all features to False
    all_features = {
        "starts_with_vowel": False,
        "starts_with_cluster": False,
        "starts_with_heavy_cluster": False,
        "contains_plosive": False,
        "contains_fricative": False,
        "contains_liquid": False,
        "contains_nasal": False,
        "short_vowel": False,
        "long_vowel": False,
        "ends_with_vowel": False,
        "ends_with_nasal": False,
        "ends_with_stop": False,
    }
    all_features.update(features)
    return {
        "name": name,
        "syllables": syllables,
        "features": all_features,
    }


class TestScoreConstants:
    """Test scoring constants."""

    def test_preferred_score(self):
        """Preferred features should add +1."""
        assert PREFERRED_SCORE == 1

    def test_tolerated_score(self):
        """Tolerated features should add 0."""
        assert TOLERATED_SCORE == 0

    def test_discouraged_penalty(self):
        """Discouraged penalty should be significantly negative."""
        assert DISCOURAGED_PENALTY < 0
        assert DISCOURAGED_PENALTY <= -10


class TestEvaluateCandidate:
    """Test candidate evaluation."""

    def test_preferred_feature_adds_score(self):
        """Preferred feature that is True should add +1."""
        policy = make_policy(ends_with_vowel="preferred")
        candidate = make_candidate("kali", ["ka", "li"], ends_with_vowel=True)

        admitted, score, details = evaluate_candidate(candidate, policy)

        assert admitted is True
        assert score == PREFERRED_SCORE
        assert "ends_with_vowel" in details["preferred_hits"]

    def test_tolerated_feature_no_score(self):
        """Tolerated feature that is True should add 0."""
        policy = make_policy(contains_plosive="tolerated")
        candidate = make_candidate("kata", ["ka", "ta"], contains_plosive=True)

        admitted, score, details = evaluate_candidate(candidate, policy)

        assert admitted is True
        assert score == TOLERATED_SCORE
        assert "contains_plosive" in details["tolerated_hits"]

    def test_discouraged_hard_mode_rejects(self):
        """Discouraged feature in hard mode should reject."""
        policy = make_policy(ends_with_stop="discouraged")
        candidate = make_candidate("kalt", ["kal", "t"], ends_with_stop=True)

        admitted, score, details = evaluate_candidate(candidate, policy, mode="hard")

        assert admitted is False
        assert details["rejection_reason"] == "ends_with_stop"
        assert "ends_with_stop" in details["discouraged_hits"]

    def test_discouraged_soft_mode_penalizes(self):
        """Discouraged feature in soft mode should apply penalty."""
        policy = make_policy(ends_with_stop="discouraged")
        candidate = make_candidate("kalt", ["kal", "t"], ends_with_stop=True)

        admitted, score, details = evaluate_candidate(candidate, policy, mode="soft")

        assert admitted is True
        assert score == DISCOURAGED_PENALTY
        assert "ends_with_stop" in details["discouraged_hits"]

    def test_false_features_ignored(self):
        """Features that are False should not contribute."""
        policy = make_policy(
            ends_with_vowel="preferred",
            ends_with_stop="discouraged",
        )
        # ends_with_vowel=False, ends_with_stop=False
        candidate = make_candidate("kaln", ["kal", "n"])

        admitted, score, details = evaluate_candidate(candidate, policy)

        assert admitted is True
        assert score == 0  # No features are True, so no score contribution
        assert details["preferred_hits"] == []
        assert details["discouraged_hits"] == []

    def test_multiple_preferred_features(self):
        """Multiple preferred features should accumulate score."""
        policy = make_policy(
            ends_with_vowel="preferred",
            contains_liquid="preferred",
            short_vowel="preferred",
        )
        candidate = make_candidate(
            "kali",
            ["ka", "li"],
            ends_with_vowel=True,
            contains_liquid=True,
            short_vowel=True,
        )

        admitted, score, details = evaluate_candidate(candidate, policy)

        assert admitted is True
        assert score == 3 * PREFERRED_SCORE
        assert len(details["preferred_hits"]) == 3

    def test_unspecified_feature_defaults_to_tolerated(self):
        """Features not in policy should default to tolerated."""
        policy = make_policy()  # Empty policy
        candidate = make_candidate("kali", ["ka", "li"], contains_plosive=True)

        admitted, score, details = evaluate_candidate(candidate, policy)

        assert admitted is True
        assert score == 0  # Tolerated = 0
        assert "contains_plosive" in details["tolerated_hits"]


class TestCheckSyllableCount:
    """Test syllable count validation."""

    def test_within_range(self):
        """Should return True when count is within range."""
        policy = make_policy()  # syllable_range=(2, 3)
        candidate = make_candidate("kali", ["ka", "li"])

        assert check_syllable_count(candidate, policy) is True

    def test_at_min_boundary(self):
        """Should return True at minimum boundary."""
        policy = make_policy()
        candidate = make_candidate("kali", ["ka", "li"])  # 2 syllables, min=2

        assert check_syllable_count(candidate, policy) is True

    def test_at_max_boundary(self):
        """Should return True at maximum boundary."""
        policy = make_policy()
        candidate = make_candidate("kalira", ["ka", "li", "ra"])  # 3 syllables, max=3

        assert check_syllable_count(candidate, policy) is True

    def test_below_min(self):
        """Should return False when below minimum."""
        policy = make_policy()
        candidate = make_candidate("ka", ["ka"])  # 1 syllable, min=2

        assert check_syllable_count(candidate, policy) is False

    def test_above_max(self):
        """Should return False when above maximum."""
        policy = make_policy()
        candidate = make_candidate("kalirata", ["ka", "li", "ra", "ta"])  # 4 syllables, max=3

        assert check_syllable_count(candidate, policy) is False


class TestEvaluationDetails:
    """Test evaluation details structure."""

    def test_details_structure(self):
        """Details should have expected keys."""
        policy = make_policy()
        candidate = make_candidate("kali", ["ka", "li"])

        admitted, score, details = evaluate_candidate(candidate, policy)

        assert "preferred_hits" in details
        assert "tolerated_hits" in details
        assert "discouraged_hits" in details
        assert "rejection_reason" in details

    def test_rejection_reason_none_when_admitted(self):
        """Rejection reason should be None when admitted."""
        policy = make_policy(ends_with_vowel="preferred")
        candidate = make_candidate("kali", ["ka", "li"], ends_with_vowel=True)

        admitted, score, details = evaluate_candidate(candidate, policy)

        assert admitted is True
        assert details["rejection_reason"] is None

    def test_rejection_reason_set_when_rejected(self):
        """Rejection reason should identify the feature."""
        policy = make_policy(ends_with_stop="discouraged")
        candidate = make_candidate("kalt", ["kal", "t"], ends_with_stop=True)

        admitted, score, details = evaluate_candidate(candidate, policy, mode="hard")

        assert admitted is False
        assert details["rejection_reason"] == "ends_with_stop"
