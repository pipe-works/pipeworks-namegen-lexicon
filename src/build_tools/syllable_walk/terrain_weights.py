"""
Terrain axis weight configuration.

This module defines the weights used to compute phonaesthetic terrain scores
from feature saturation percentages. Weights are configurable to allow
calibration based on different phonaesthetic models or user preferences.

Design Philosophy:
    - Weights should reflect phonaesthetic reality, not be tuned to produce
      desired results for specific corpora
    - Each weight should have a defensible rationale independent of test outcomes
    - Users can override defaults to match their own phonaesthetic intuitions
    - All weights are documented with their phonaesthetic justification

The Three Axes:
    - Shape (Round ↔ Jagged): Bouba/Kiki dimension - perceptual "softness" vs "hardness"
    - Craft (Flowing ↔ Worked): Sung/Forged dimension - ease vs effort of articulation
    - Space (Open ↔ Dense): Valley/Workshop dimension - acoustic spaciousness vs compression

Weight Conventions:
    - Negative weights pull toward the first pole (Round, Flowing, Open)
    - Positive weights pull toward the second pole (Jagged, Worked, Dense)
    - Magnitude indicates strength of contribution (0.0-1.0 typical range)
    - Weights can exceed 1.0 for features with outsized phonaesthetic impact

References:
    - Ramachandran & Hubbard (2001): Bouba/Kiki effect
    - Köhler (1929): Original "maluma/takete" experiments
    - See _working/sfa_shapes_terrain_map.md for calibration notes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class AxisWeights:
    """
    Weights for a single terrain axis.

    Each weight maps a feature name to its contribution to the axis score.
    Negative weights pull toward the low pole, positive toward the high pole.
    """

    weights: dict[str, float] = field(default_factory=dict)

    def get(self, feature: str, default: float = 0.0) -> float:
        """Get weight for a feature, returning default if not defined."""
        return self.weights.get(feature, default)

    def set(self, feature: str, value: float) -> None:
        """Set weight for a feature."""
        self.weights[feature] = value

    def items(self):
        """Iterate over (feature, weight) pairs."""
        return self.weights.items()

    def feature_names(self) -> list[str]:
        """Get ordered list of feature names."""
        return list(self.weights.keys())

    def __len__(self) -> int:
        """Return number of weights."""
        return len(self.weights)


@dataclass
class TerrainWeights:
    """
    Complete terrain weight configuration for all three axes.

    This is the primary configuration interface. Users can:
    1. Use defaults (well-documented phonaesthetic rationale)
    2. Override specific weights
    3. Load entirely custom configurations

    Attributes:
        shape: Weights for Shape axis (Round ↔ Jagged)
        craft: Weights for Craft axis (Flowing ↔ Worked)
        space: Weights for Space axis (Open ↔ Dense)
    """

    shape: AxisWeights = field(default_factory=AxisWeights)
    craft: AxisWeights = field(default_factory=AxisWeights)
    space: AxisWeights = field(default_factory=AxisWeights)


# =============================================================================
# Default Weights with Phonaesthetic Rationale
# =============================================================================
#
# IMPORTANT: These defaults are based on phonaesthetic principles, not tuned
# to produce specific results for test corpora. Each weight has a documented
# rationale that should be defensible independent of empirical outcomes.
#
# If test results seem "wrong", consider:
# 1. Is the phonaesthetic claim actually correct?
# 2. Are other features washing out the effect?
# 3. Is the test corpus representative?
#
# Do NOT adjust weights simply to make test cases "look right".


def create_default_shape_weights() -> AxisWeights:
    """
    Create default weights for Shape axis (Round ↔ Jagged).

    The Shape axis captures the Bouba/Kiki dimension — the perceptual
    "roundness" or "jaggedness" of sounds. This is one of the most robust
    findings in phonaesthetics research.

    Phonaesthetic Rationale:

    TOWARD ROUND (negative weights):
        contains_liquid (-0.8):
            Liquids (l, r) have smooth, continuous airflow. The tongue
            creates no hard obstruction. Perceptually "flowing" and "soft".
            Weight: -0.8 (strong but not dominant, as liquids are common)

        contains_nasal (-0.6):
            Nasals (m, n, ng) have resonant, humming quality. No hard
            closure release. Perceptually "warm" and "rounded".
            Weight: -0.6 (moderate, nasals are soft but less defining than liquids)

        ends_with_vowel (-0.6):
            Vowel endings create open, unobstructed syllable close.
            No abrupt stop. Perceptually "open" and "soft".
            Weight: -0.6 (moderate contribution to roundness)

    TOWARD JAGGED (positive weights):
        contains_plosive (+0.6):
            Plosives (p, b, t, d, k, g) have complete airflow obstruction
            followed by sudden release. Perceptually "hard" and "abrupt".
            Weight: +0.6 (reduced from 1.0 to prevent English saturation,
            as plosives are extremely common in all languages)

        ends_with_stop (+1.0):
            Stop codas create hard syllable boundaries. The syllable
            "cuts off" rather than fading. Perceptually very "sharp".
            Weight: +1.0 (strong signal of jaggedness)

        starts_with_heavy_cluster (+0.8):
            Heavy clusters (3+ consonants: "str", "spr") require complex
            articulation. Multiple obstructions in sequence. Perceptually
            "effortful" and "jagged".
            Weight: +0.8 (distinctive marker, but relatively rare)

        contains_fricative (+0.3):
            Fricatives (f, s, sh, th) have turbulent airflow but no complete
            obstruction. Add "texture" and slight edge. Not as hard as plosives.
            Weight: +0.3 (mild contribution, more textural than defining)

    Returns:
        AxisWeights configured for Shape axis
    """
    return AxisWeights(
        weights={
            # Toward Round (negative)
            "contains_liquid": -0.8,
            "contains_nasal": -0.6,
            "ends_with_vowel": -0.6,
            # Toward Jagged (positive)
            "contains_plosive": 0.6,
            "ends_with_stop": 1.0,
            "starts_with_heavy_cluster": 0.8,
            "contains_fricative": 0.3,
        }
    )


def create_default_craft_weights() -> AxisWeights:
    """
    Create default weights for Craft axis (Flowing ↔ Worked).

    The Craft axis captures articulatory effort — whether sounds feel
    "sung" (easy, flowing) or "forged" (effortful, constructed).

    Phonaesthetic Rationale:

    TOWARD FLOWING (negative weights):
        ends_with_vowel (-1.0):
            Vowel endings allow breath to continue naturally. No effort
            to close the syllable. Like singing — notes sustain and connect.
            Weight: -1.0 (primary marker of flowing character)

        starts_with_vowel (-0.8):
            Vowel onsets require no articulatory preparation. Sound begins
            immediately with open vocal tract. Effortless initiation.
            Weight: -0.8 (strong contributor to ease)

        long_vowel (-0.6):
            Long vowels sustain without consonant interruption. The sound
            "dwells" rather than moving quickly. Singing vs speaking.
            Weight: -0.6 (moderate, as vowel length varies by context)

    TOWARD WORKED (positive weights):
        starts_with_cluster (+1.0):
            Consonant clusters require coordinated articulation of multiple
            obstructions before the vowel. Effortful onset. Like forging —
            hammering multiple strikes.
            Weight: +1.0 (primary marker of worked character)

        starts_with_heavy_cluster (+0.8):
            Heavy clusters (3+ consonants) amplify the effort further.
            Maximum articulatory complexity at syllable onset.
            Weight: +0.8 (intensifier for already-worked onsets)

        short_vowel (+0.4):
            Short vowels move quickly to the next consonant. Less dwell time.
            Clipped, efficient, constructed feel.
            Weight: +0.4 (mild contribution, very common feature)

    Returns:
        AxisWeights configured for Craft axis
    """
    return AxisWeights(
        weights={
            # Toward Flowing (negative)
            "ends_with_vowel": -1.0,
            "starts_with_vowel": -0.8,
            "long_vowel": -0.6,
            # Toward Worked (positive)
            "starts_with_cluster": 1.0,
            "starts_with_heavy_cluster": 0.8,
            "short_vowel": 0.4,
        }
    )


def create_default_space_weights() -> AxisWeights:
    """
    Create default weights for Space axis (Open ↔ Dense).

    The Space axis captures acoustic "spaciousness" — whether the syllable
    inventory feels airy and expansive or compact and closed.

    Phonaesthetic Rationale:

    TOWARD OPEN (negative weights):
        ends_with_vowel (-1.0):
            Vowel endings leave acoustic space after the syllable. Sound
            can "breathe" and resonate. Valley-like openness.
            Weight: -1.0 (primary marker of openness)

        starts_with_vowel (-0.8):
            Vowel onsets create immediate acoustic space. No consonant
            barrier at the beginning. Open initiation.
            Weight: -0.8 (strong contributor)

        long_vowel (-0.6):
            Long vowels expand the acoustic duration. More time in open
            vocal tract configuration. Spacious sound.
            Weight: -0.6 (moderate, duration contributes to spaciousness)

    TOWARD DENSE (positive weights):
        short_vowel (+0.6):
            Short vowels compress the acoustic core. Less resonant space.
            Compact, efficient syllable structure.
            Weight: +0.6 (moderate-strong, common feature)

        ends_with_stop (+0.6):
            Stop codas close off the acoustic space abruptly. No resonance
            after the syllable. Compact, bounded.
            Weight: +0.6 (contributes to closure/density)

        ends_with_nasal (+0.4):
            Nasal codas partially close the oral cavity. Less open than
            vowel endings, but resonant through the nose. Moderate closure.
            Weight: +0.4 (mild density contribution)

    Returns:
        AxisWeights configured for Space axis
    """
    return AxisWeights(
        weights={
            # Toward Open (negative)
            "ends_with_vowel": -1.0,
            "starts_with_vowel": -0.8,
            "long_vowel": -0.6,
            # Toward Dense (positive)
            "short_vowel": 0.6,
            "ends_with_stop": 0.6,
            "ends_with_nasal": 0.4,
        }
    )


def create_default_terrain_weights() -> TerrainWeights:
    """
    Create complete terrain weights with all defaults.

    This is the primary entry point for getting default configuration.
    All weights are documented with phonaesthetic rationale in their
    respective creation functions.

    Returns:
        TerrainWeights with all three axes configured to defaults
    """
    return TerrainWeights(
        shape=create_default_shape_weights(),
        craft=create_default_craft_weights(),
        space=create_default_space_weights(),
    )


# =============================================================================
# Configuration Loading (Future: TOML file support)
# =============================================================================


def load_terrain_weights(config_path: Path | None = None) -> TerrainWeights:
    """
    Load terrain weights from configuration or use defaults.

    Currently returns defaults. Future versions will support loading
    from a TOML configuration file for user customization.

    Args:
        config_path: Optional path to TOML config file (not yet implemented)

    Returns:
        TerrainWeights configuration
    """
    # TODO: Implement TOML loading when needed
    # For now, always return defaults
    if config_path is not None:
        # Future: parse TOML and merge with defaults
        pass

    return create_default_terrain_weights()


# =============================================================================
# Module-level default instance
# =============================================================================

# Pre-created default weights for convenient access
DEFAULT_TERRAIN_WEIGHTS = create_default_terrain_weights()
