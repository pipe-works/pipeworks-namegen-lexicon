"""
Name class policy data models and YAML loading.

This module defines the dataclasses for representing name class policies
and provides functions to load them from YAML configuration files.

The Name Class Matrix is externalized to data/name_classes.yml, separating
policy configuration from code. This enables:
- Non-programmers to tune name classes
- Version control tracking of policy evolution
- Multiple projects sharing the codebase with different policies

Policy Structure
----------------
Each name class defines:
- description: Human-readable purpose
- syllable_range: [min, max] syllables (inclusive)
- features: Dict mapping feature names to policy values

Policy values:
- "preferred": Actively sought (+1 score)
- "tolerated": Neutral (0 score)
- "discouraged": Rejected or penalized

Usage
-----
>>> from build_tools.name_selector.name_class import load_name_classes
>>> policies = load_name_classes("data/name_classes.yml")
>>> first_name_policy = policies["first_name"]
>>> first_name_policy.description
'Direct social address. Optimized for addressability and mouth-feel.'
>>> first_name_policy.features["ends_with_vowel"]
'preferred'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

# Valid policy values for features
PolicyValue = Literal["preferred", "tolerated", "discouraged"]

# The 12 canonical feature names
FEATURE_NAMES = frozenset(
    {
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
    }
)


@dataclass(frozen=True)
class NameClassPolicy:
    """
    Policy configuration for a single name class.

    Defines feature preferences for evaluating name candidates.
    Policies are loaded from YAML and remain immutable during evaluation.

    Attributes
    ----------
    name : str
        Identifier for this name class (e.g., "first_name", "place_name").

    description : str
        Human-readable description of the name class purpose.

    syllable_range : tuple[int, int]
        Allowed syllable count range [min, max], inclusive.

    features : dict[str, PolicyValue]
        Mapping of feature name to policy value ("preferred", "tolerated",
        "discouraged").

    Examples
    --------
    >>> policy = NameClassPolicy(
    ...     name="first_name",
    ...     description="Direct social address.",
    ...     syllable_range=(2, 3),
    ...     features={"ends_with_vowel": "preferred", "ends_with_stop": "discouraged"},
    ... )
    >>> policy.features["ends_with_vowel"]
    'preferred'
    """

    name: str
    description: str
    syllable_range: tuple[int, int]
    features: dict[str, PolicyValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate policy configuration."""
        # Validate syllable range
        if len(self.syllable_range) != 2:
            raise ValueError(f"syllable_range must have 2 elements, got {self.syllable_range}")
        if self.syllable_range[0] > self.syllable_range[1]:
            raise ValueError(
                f"syllable_range min > max: {self.syllable_range[0]} > {self.syllable_range[1]}"
            )

        # Validate feature names
        unknown_features = set(self.features.keys()) - FEATURE_NAMES
        if unknown_features:
            raise ValueError(f"Unknown features in policy '{self.name}': {unknown_features}")

        # Validate policy values
        valid_values = {"preferred", "tolerated", "discouraged"}
        for feature, value in self.features.items():
            if value not in valid_values:
                raise ValueError(
                    f"Invalid policy value for '{feature}' in '{self.name}': "
                    f"'{value}'. Must be one of {valid_values}"
                )


def load_name_classes(yaml_path: str | Path) -> dict[str, NameClassPolicy]:
    """
    Load name class policies from a YAML file.

    Parameters
    ----------
    yaml_path : str | Path
        Path to the name_classes.yml file.

    Returns
    -------
    dict[str, NameClassPolicy]
        Dictionary mapping name class identifiers to their policies.

    Raises
    ------
    FileNotFoundError
        If the YAML file does not exist.
    ValueError
        If the YAML structure is invalid or policies fail validation.

    Examples
    --------
    >>> policies = load_name_classes("data/name_classes.yml")
    >>> "first_name" in policies
    True
    >>> policies["first_name"].syllable_range
    (2, 3)
    """
    yaml_path = Path(yaml_path)

    if not yaml_path.exists():
        raise FileNotFoundError(f"Name classes file not found: {yaml_path}")

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict at top level of {yaml_path}, got {type(data)}")

    if "name_classes" not in data:
        raise ValueError(f"Missing 'name_classes' key in {yaml_path}")

    name_classes_data = data["name_classes"]
    if not isinstance(name_classes_data, dict):
        raise ValueError(f"'name_classes' must be a dict, got {type(name_classes_data)}")

    policies: dict[str, NameClassPolicy] = {}

    for name, config in name_classes_data.items():
        if not isinstance(config, dict):
            raise ValueError(f"Name class '{name}' must be a dict, got {type(config)}")

        # Extract fields
        description = config.get("description", "")
        syllable_range_raw = config.get("syllable_range", [2, 3])
        features = config.get("features", {})

        # Convert syllable_range to tuple
        if isinstance(syllable_range_raw, list):
            syllable_range = tuple(syllable_range_raw)
        else:
            raise ValueError(
                f"syllable_range for '{name}' must be a list, got {type(syllable_range_raw)}"
            )

        # Create policy (validation happens in __post_init__)
        policies[name] = NameClassPolicy(
            name=name,
            description=description,
            syllable_range=syllable_range,  # type: ignore[arg-type]
            features=features,
        )

    return policies


def get_default_policy_path() -> Path:
    """
    Get the default path to name_classes.yml.

    Returns
    -------
    Path
        Path to data/name_classes.yml relative to project root.

    Notes
    -----
    This assumes the project structure has data/name_classes.yml at the root.
    """
    # Try to find project root by looking for pyproject.toml
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent / "data" / "name_classes.yml"

    # Fallback to relative path (only reached outside project structure)
    return Path("data/name_classes.yml")  # pragma: no cover
