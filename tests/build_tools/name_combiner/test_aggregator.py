"""Tests for feature aggregation logic."""

import pytest

from build_tools.name_combiner.aggregator import (
    ALL_FEATURES,
    CODA_FEATURES,
    INTERNAL_FEATURES,
    NUCLEUS_FEATURES,
    ONSET_FEATURES,
    aggregate_features,
)


def make_syllable(syllable: str, **features: bool) -> dict:
    """Helper to create a syllable dict with default False features."""
    feature_dict = {f: False for f in ALL_FEATURES}
    feature_dict.update(features)
    return {"syllable": syllable, "features": feature_dict}


class TestFeatureCategories:
    """Test that feature categories are correctly defined."""

    def test_all_features_count(self):
        """All 12 features should be defined."""
        assert len(ALL_FEATURES) == 12

    def test_onset_features(self):
        """Onset features should include starts_with_* features."""
        assert "starts_with_vowel" in ONSET_FEATURES
        assert "starts_with_cluster" in ONSET_FEATURES
        assert "starts_with_heavy_cluster" in ONSET_FEATURES
        assert len(ONSET_FEATURES) == 3

    def test_coda_features(self):
        """Coda features should include ends_with_* features."""
        assert "ends_with_vowel" in CODA_FEATURES
        assert "ends_with_nasal" in CODA_FEATURES
        assert "ends_with_stop" in CODA_FEATURES
        assert len(CODA_FEATURES) == 3

    def test_internal_features(self):
        """Internal features should include contains_* features."""
        assert "contains_plosive" in INTERNAL_FEATURES
        assert "contains_fricative" in INTERNAL_FEATURES
        assert "contains_liquid" in INTERNAL_FEATURES
        assert "contains_nasal" in INTERNAL_FEATURES
        assert len(INTERNAL_FEATURES) == 4

    def test_nucleus_features(self):
        """Nucleus features should include vowel length proxies."""
        assert "short_vowel" in NUCLEUS_FEATURES
        assert "long_vowel" in NUCLEUS_FEATURES
        assert len(NUCLEUS_FEATURES) == 2


class TestOnsetAggregation:
    """Test onset feature aggregation (first syllable only)."""

    def test_onset_from_first_syllable(self):
        """Onset features should come from first syllable only."""
        syllables = [
            make_syllable("ka", starts_with_vowel=False, starts_with_cluster=False),
            make_syllable("li", starts_with_vowel=False, starts_with_cluster=False),
        ]
        result = aggregate_features(syllables)
        assert result["starts_with_vowel"] is False
        assert result["starts_with_cluster"] is False

    def test_onset_ignores_later_syllables(self):
        """Onset should not be affected by later syllables."""
        syllables = [
            make_syllable("ka", starts_with_vowel=False),
            make_syllable("a", starts_with_vowel=True),  # This should be ignored
        ]
        result = aggregate_features(syllables)
        assert result["starts_with_vowel"] is False

    def test_onset_vowel_start(self):
        """Test vowel-initial name."""
        syllables = [
            make_syllable("a", starts_with_vowel=True),
            make_syllable("ka", starts_with_vowel=False),
        ]
        result = aggregate_features(syllables)
        assert result["starts_with_vowel"] is True


class TestCodaAggregation:
    """Test coda feature aggregation (final syllable only)."""

    def test_coda_from_final_syllable(self):
        """Coda features should come from final syllable only."""
        syllables = [
            make_syllable("ka", ends_with_vowel=True),  # This should be ignored
            make_syllable("ton", ends_with_vowel=False, ends_with_nasal=True),
        ]
        result = aggregate_features(syllables)
        assert result["ends_with_vowel"] is False
        assert result["ends_with_nasal"] is True

    def test_coda_ignores_earlier_syllables(self):
        """Coda should not be affected by earlier syllables."""
        syllables = [
            make_syllable("ton", ends_with_nasal=True),
            make_syllable("ka", ends_with_vowel=True, ends_with_nasal=False),
        ]
        result = aggregate_features(syllables)
        assert result["ends_with_nasal"] is False
        assert result["ends_with_vowel"] is True


class TestInternalAggregation:
    """Test internal feature aggregation (OR across all)."""

    def test_internal_or_any_syllable(self):
        """Internal features should OR across all syllables."""
        syllables = [
            make_syllable("ka", contains_liquid=False),
            make_syllable("li", contains_liquid=True),
            make_syllable("ra", contains_liquid=True),
        ]
        result = aggregate_features(syllables)
        assert result["contains_liquid"] is True

    def test_internal_false_when_none_have(self):
        """Internal feature should be False if no syllable has it."""
        syllables = [
            make_syllable("ka", contains_liquid=False),
            make_syllable("ta", contains_liquid=False),
        ]
        result = aggregate_features(syllables)
        assert result["contains_liquid"] is False

    def test_internal_true_when_any_has(self):
        """Internal feature should be True if any syllable has it."""
        syllables = [
            make_syllable("ka", contains_plosive=True),
            make_syllable("ta", contains_plosive=False),
        ]
        result = aggregate_features(syllables)
        assert result["contains_plosive"] is True


class TestNucleusAggregation:
    """Test nucleus feature aggregation (majority rule)."""

    def test_nucleus_majority_two_syllables_both_true(self):
        """2 syllables, both short_vowel: 2/2 = 100% > 50%."""
        syllables = [
            make_syllable("ka", short_vowel=True),
            make_syllable("li", short_vowel=True),
        ]
        result = aggregate_features(syllables)
        assert result["short_vowel"] is True

    def test_nucleus_majority_two_syllables_split(self):
        """2 syllables, 1 short: 1/2 = 50%, NOT > 50%."""
        syllables = [
            make_syllable("ka", short_vowel=True),
            make_syllable("lee", short_vowel=False),
        ]
        result = aggregate_features(syllables)
        # 1/2 = 50% is NOT > 50%, so should be False
        assert result["short_vowel"] is False

    def test_nucleus_majority_three_syllables_two_true(self):
        """3 syllables, 2 short: 2/3 = 66.7% > 50%."""
        syllables = [
            make_syllable("ka", short_vowel=True),
            make_syllable("li", short_vowel=True),
            make_syllable("ree", short_vowel=False),
        ]
        result = aggregate_features(syllables)
        assert result["short_vowel"] is True

    def test_nucleus_majority_three_syllables_one_true(self):
        """3 syllables, 1 short: 1/3 = 33.3% < 50%."""
        syllables = [
            make_syllable("ka", short_vowel=True),
            make_syllable("lee", short_vowel=False),
            make_syllable("ree", short_vowel=False),
        ]
        result = aggregate_features(syllables)
        assert result["short_vowel"] is False

    def test_nucleus_majority_four_syllables_three_true(self):
        """4 syllables, 3 short: 3/4 = 75% > 50%."""
        syllables = [
            make_syllable("ka", short_vowel=True),
            make_syllable("li", short_vowel=True),
            make_syllable("ta", short_vowel=True),
            make_syllable("ree", short_vowel=False),
        ]
        result = aggregate_features(syllables)
        assert result["short_vowel"] is True

    def test_nucleus_majority_four_syllables_two_true(self):
        """4 syllables, 2 short: 2/4 = 50%, NOT > 50%."""
        syllables = [
            make_syllable("ka", short_vowel=True),
            make_syllable("li", short_vowel=True),
            make_syllable("ree", short_vowel=False),
            make_syllable("see", short_vowel=False),
        ]
        result = aggregate_features(syllables)
        # 2/4 = 50% is NOT > 50%, so should be False
        assert result["short_vowel"] is False


class TestAggregationEdgeCases:
    """Test edge cases in aggregation."""

    def test_empty_list_raises(self):
        """Empty syllable list should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            aggregate_features([])

    def test_missing_features_key_raises(self):
        """Syllable without features key should raise ValueError."""
        with pytest.raises(ValueError, match="missing 'features'"):
            aggregate_features([{"syllable": "ka"}])

    def test_single_syllable(self):
        """Single syllable should work (first = final)."""
        syllables = [
            make_syllable(
                "ka",
                starts_with_vowel=False,
                ends_with_vowel=True,
                contains_plosive=True,
                short_vowel=True,
            ),
        ]
        result = aggregate_features(syllables)
        assert result["starts_with_vowel"] is False
        assert result["ends_with_vowel"] is True
        assert result["contains_plosive"] is True
        assert result["short_vowel"] is True


class TestAggregationCompleteness:
    """Test that aggregation produces complete feature vectors."""

    def test_all_features_present_in_result(self):
        """Result should contain all 12 features."""
        syllables = [make_syllable("ka"), make_syllable("li")]
        result = aggregate_features(syllables)
        for feature in ALL_FEATURES:
            assert feature in result, f"Missing feature: {feature}"

    def test_result_is_boolean(self):
        """All feature values should be booleans."""
        syllables = [make_syllable("ka"), make_syllable("li")]
        result = aggregate_features(syllables)
        for feature, value in result.items():
            assert isinstance(value, bool), f"Feature {feature} is not bool: {type(value)}"
