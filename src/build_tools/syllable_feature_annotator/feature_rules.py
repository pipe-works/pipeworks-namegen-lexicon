"""
Feature detection rules for syllable annotation.

This module defines pure, deterministic feature detectors that observe structural
patterns in syllables. Each detector is a boolean function that takes a syllable
string and returns True or False based on observable character patterns.

Design Principles
-----------------
1. **Deterministic**: Same input always produces same output
2. **Pure Functions**: No state, no side effects, no randomness, no I/O
3. **Language-Agnostic**: Structural patterns only, no linguistic interpretation
4. **Feature Independence**: Detectors don't depend on each other
5. **Conservative Detection**: Approximate patterns without overthinking

Feature Categories
------------------
**Onset Features** - Syllable-initial patterns
    - starts_with_vowel: Syllable begins with vowel (open onset)
    - starts_with_cluster: Initial consonant cluster (2+ consonants)
    - starts_with_heavy_cluster: Heavy initial cluster (3+ consonants)

**Internal Features** - Manner of articulation presence
    - contains_plosive: Contains plosive consonant (p, t, k, b, d, g)
    - contains_fricative: Contains fricative consonant (f, s, z, v, h)
    - contains_liquid: Contains liquid consonant (l, r, w)
    - contains_nasal: Contains nasal consonant (m, n)

**Nucleus Features** - Vowel structure (length proxies)
    - short_vowel: Exactly one vowel (closed/short syllable)
    - long_vowel: Two or more vowels (open/long syllable)

**Coda Features** - Syllable-final patterns
    - ends_with_vowel: Syllable ends with vowel (open syllable)
    - ends_with_nasal: Syllable ends with nasal consonant
    - ends_with_stop: Syllable ends with stop consonant

Usage
-----
Feature detectors can be called directly::

    >>> from build_tools.syllable_feature_annotator.feature_rules import (
    ...     starts_with_cluster, contains_plosive, short_vowel
    ... )
    >>> starts_with_cluster("kran")
    True
    >>> contains_plosive("kran")
    True
    >>> short_vowel("kran")
    True

Or accessed via the feature registry::

    >>> from build_tools.syllable_feature_annotator.feature_rules import FEATURE_DETECTORS
    >>> detector = FEATURE_DETECTORS["starts_with_cluster"]
    >>> detector("kran")
    True

Applying all features to a syllable::

    >>> syllable = "spla"
    >>> features = {
    ...     name: detector(syllable)
    ...     for name, detector in FEATURE_DETECTORS.items()
    ... }
    >>> features["starts_with_heavy_cluster"]
    True

Implementation Notes
--------------------
**Nucleus Logic is Intentionally Simple**:

The short_vowel and long_vowel detectors are NOT linguistic vowel length.
They are *structural proxies* for:
- Syllable weight (light vs heavy)
- Openness/closedness patterns
- Nucleus complexity

This is a deliberate simplification that provides sufficient signal for
downstream pattern generation without requiring linguistic analysis.

**Heavy Cluster Definition is Future-Safe**:

The heavy cluster detector (3+ consonants) is a placeholder that can be
refined later without breaking downstream consumers. Current definition
is conservative and catches the most obvious cases.

**Conservative Detection**:

Detectors use simple character-based rules. For example, starts_with_cluster
just checks if first two characters are non-vowels. This intentionally:
- Catches clear cases (tr, kr, st, etc.)
- Avoids overthinking language-specific rules
- Maintains determinism across different syllable sources

Why Feature Independence Matters
---------------------------------
No detector depends on another detector's output. This is critical because:

1. **Composability**: Downstream consumers can combine features freely
2. **Invertibility**: Features can be weighted positively or negatively
3. **Extensibility**: New features don't break existing ones
4. **Testability**: Each feature can be tested in isolation
5. **Clarity**: Each rule has one clear responsibility

Examples
--------
Classify a simple syllable::

    >>> syllable = "na"
    >>> starts_with_cluster("na")
    False
    >>> short_vowel("na")
    True
    >>> ends_with_vowel("na")
    True

Classify a complex cluster::

    >>> syllable = "spla"
    >>> starts_with_heavy_cluster("spla")
    True
    >>> starts_with_cluster("spla")  # Also true - heavy clusters are clusters
    True
    >>> contains_liquid("spla")
    True

Classify a closed syllable::

    >>> syllable = "takt"
    >>> contains_plosive("takt")
    True
    >>> ends_with_stop("takt")
    True
    >>> short_vowel("takt")
    True

Test edge cases::

    >>> starts_with_vowel("")  # Empty string
    False
    >>> short_vowel("a")  # Single vowel
    True
    >>> long_vowel("ae")  # Diphthong
    True
"""

from build_tools.syllable_feature_annotator.phoneme_sets import (
    FRICATIVES,
    LIQUIDS,
    NASALS,
    PLOSIVES,
    STOPS,
    VOWELS,
)

# -------------------------------------------------
# Onset Features - Syllable-initial patterns
# -------------------------------------------------


def starts_with_vowel(s: str) -> bool:
    """
    Detect if syllable starts with a vowel (vowel-initial or open onset).

    This feature identifies syllables that begin directly with a vowel,
    without any initial consonant. Such syllables have an "open onset"
    in phonological terms.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable starts with vowel, False otherwise

    Examples
    --------
    >>> starts_with_vowel("apple")
    True
    >>> starts_with_vowel("kran")
    False
    >>> starts_with_vowel("a")
    True
    >>> starts_with_vowel("")  # Edge case: empty string
    False

    Notes
    -----
    - Empty strings return False (no onset to analyze)
    - Only checks the first character
    - Vowels are defined in phoneme_sets.VOWELS (a, e, i, o, u)
    """
    return bool(s) and s[0] in VOWELS


def starts_with_cluster(s: str) -> bool:
    """
    Detect if syllable starts with a consonant cluster (2+ consonants).

    A consonant cluster is two or more adjacent consonants at the beginning
    of a syllable. This creates increased phonetic complexity and affects
    pronunciation difficulty and syllable weight.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable starts with 2+ consonants, False otherwise

    Examples
    --------
    >>> starts_with_cluster("kran")
    True
    >>> starts_with_cluster("train")
    True
    >>> starts_with_cluster("na")
    False
    >>> starts_with_cluster("a")
    False

    Notes
    -----
    - Requires at least 2 characters
    - Checks that first two characters are both non-vowels
    - Conservative detection: catches obvious clusters (tr, kr, st, etc.)
    - Does not handle vowel-glides or language-specific edge cases
    - Heavy clusters (3+ consonants) will also trigger this detector
    """
    return len(s) >= 2 and s[0] not in VOWELS and s[1] not in VOWELS


def starts_with_heavy_cluster(s: str) -> bool:
    """
    Detect if syllable starts with a heavy consonant cluster (3+ consonants).

    Heavy clusters are particularly complex initial consonant sequences.
    These are relatively rare in natural language but create distinctive
    phonetic patterns when present.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable starts with 3+ consonants, False otherwise

    Examples
    --------
    >>> starts_with_heavy_cluster("spla")
    True
    >>> starts_with_heavy_cluster("stra")
    True
    >>> starts_with_heavy_cluster("kran")
    False
    >>> starts_with_heavy_cluster("na")
    False

    Notes
    -----
    - Requires at least 3 characters
    - Checks that first three characters are all non-vowels
    - Future-safe: can be refined or replaced without breaking consumers
    - This is a placeholder definition that catches obvious cases
    - Syllables with heavy clusters will also trigger starts_with_cluster
    """
    return len(s) >= 3 and all(c not in VOWELS for c in s[:3])


# -------------------------------------------------
# Internal Features - Manner of articulation
# -------------------------------------------------


def contains_plosive(s: str) -> bool:
    """
    Detect if syllable contains any plosive consonant.

    Plosives (p, t, k, b, d, g) are consonants produced by completely
    blocking airflow then releasing it suddenly. They inject "hardness"
    and percussive texture into syllables.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable contains any plosive, False otherwise

    Examples
    --------
    >>> contains_plosive("takt")
    True
    >>> contains_plosive("pat")
    True
    >>> contains_plosive("sal")
    False
    >>> contains_plosive("")
    False

    Notes
    -----
    - Checks entire syllable, not just specific positions
    - Plosives defined in phoneme_sets.PLOSIVES (p, t, k, b, d, g)
    - Multiple plosives in one syllable still return True
    - Empty strings return False
    """
    return any(c in PLOSIVES for c in s)


def contains_fricative(s: str) -> bool:
    """
    Detect if syllable contains any fricative consonant.

    Fricatives (f, s, z, v, h) are consonants produced by forcing air
    through a narrow channel, creating turbulent airflow and friction.
    They create "hissing" or "buzzing" texture.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable contains any fricative, False otherwise

    Examples
    --------
    >>> contains_fricative("fish")
    True
    >>> contains_fricative("zone")
    True
    >>> contains_fricative("bat")
    False
    >>> contains_fricative("")
    False

    Notes
    -----
    - Checks entire syllable, not just specific positions
    - Fricatives defined in phoneme_sets.FRICATIVES (f, s, z, v, h)
    - Multiple fricatives in one syllable still return True
    - Empty strings return False
    """
    return any(c in FRICATIVES for c in s)


def contains_liquid(s: str) -> bool:
    """
    Detect if syllable contains any liquid consonant.

    Liquids (l, r, w) are consonants with vowel-like qualities that
    flow smoothly. They have lateral (l) or rhotic (r) characteristics
    and contribute to syllable fluidity.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable contains any liquid, False otherwise

    Examples
    --------
    >>> contains_liquid("kran")
    True
    >>> contains_liquid("slow")
    True
    >>> contains_liquid("bat")
    False
    >>> contains_liquid("")
    False

    Notes
    -----
    - Checks entire syllable, not just specific positions
    - Liquids defined in phoneme_sets.LIQUIDS (l, r, w)
    - 'w' is included due to its semi-vowel/glide properties
    - Multiple liquids in one syllable still return True
    - Empty strings return False
    """
    return any(c in LIQUIDS for c in s)


def contains_nasal(s: str) -> bool:
    """
    Detect if syllable contains any nasal consonant.

    Nasals (m, n) are consonants where air flows through the nasal
    cavity. They have resonant qualities and often appear in coda
    positions, contributing to syllable closure patterns.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable contains any nasal, False otherwise

    Examples
    --------
    >>> contains_nasal("kran")
    True
    >>> contains_nasal("man")
    True
    >>> contains_nasal("bat")
    False
    >>> contains_nasal("")
    False

    Notes
    -----
    - Checks entire syllable, not just specific positions
    - Nasals defined in phoneme_sets.NASALS (m, n)
    - Multiple nasals in one syllable still return True
    - Empty strings return False
    - See also: ends_with_nasal for coda-specific detection
    """
    return any(c in NASALS for c in s)


# -------------------------------------------------
# Nucleus Features - Vowel structure (length proxies)
# -------------------------------------------------


def short_vowel(s: str) -> bool:
    """
    Detect if syllable has exactly one vowel (short vowel proxy).

    This is a structural proxy for syllable weight and nucleus complexity,
    not linguistic vowel length. Syllables with one vowel tend to be
    lighter and more closed.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable contains exactly one vowel, False otherwise

    Examples
    --------
    >>> short_vowel("bat")
    True
    >>> short_vowel("kran")
    True
    >>> short_vowel("beat")  # 'ea' = 2 vowels
    False
    >>> short_vowel("")
    False

    Notes
    -----
    - Counts total vowels in syllable (any position)
    - Returns True only if count == 1
    - Not linguistic vowel length (short vs long /a/ vs /aː/)
    - Provides proxy for syllable weight and openness
    - Mutually exclusive with long_vowel
    - Empty strings return False (no nucleus)
    """
    return sum(1 for c in s if c in VOWELS) == 1


def long_vowel(s: str) -> bool:
    """
    Detect if syllable has two or more vowels (long vowel proxy).

    This is a structural proxy for syllable weight and nucleus complexity,
    not linguistic vowel length. Syllables with multiple vowels tend to
    be heavier and more open, including diphthongs and vowel sequences.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable contains 2+ vowels, False otherwise

    Examples
    --------
    >>> long_vowel("beat")  # 'ea' = 2 vowels
    True
    >>> long_vowel("aura")  # 'au' + 'a' = 3 vowels
    True
    >>> long_vowel("bat")
    False
    >>> long_vowel("")
    False

    Notes
    -----
    - Counts total vowels in syllable (any position)
    - Returns True if count >= 2
    - Not linguistic vowel length (short vs long /a/ vs /aː/)
    - Catches diphthongs (ae, au, etc.) and vowel sequences
    - Provides proxy for syllable weight and complexity
    - Mutually exclusive with short_vowel
    - Empty strings return False (no nucleus)
    """
    return sum(1 for c in s if c in VOWELS) >= 2


# -------------------------------------------------
# Coda Features - Syllable-final patterns
# -------------------------------------------------


def ends_with_vowel(s: str) -> bool:
    """
    Detect if syllable ends with a vowel (open syllable).

    Syllables ending in vowels are "open" in phonological terms.
    They tend to have higher sonority and different prosodic properties
    compared to consonant-final syllables.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable ends with vowel, False otherwise

    Examples
    --------
    >>> ends_with_vowel("na")
    True
    >>> ends_with_vowel("hello")
    True
    >>> ends_with_vowel("bat")
    False
    >>> ends_with_vowel("")
    False

    Notes
    -----
    - Only checks the final character
    - Vowels defined in phoneme_sets.VOWELS (a, e, i, o, u)
    - Open syllables (vowel-final) vs closed syllables (consonant-final)
    - Empty strings return False (no coda to analyze)
    - Mutually exclusive with ends_with_nasal and ends_with_stop
    """
    return bool(s) and s[-1] in VOWELS


def ends_with_nasal(s: str) -> bool:
    """
    Detect if syllable ends with a nasal consonant (nasal coda).

    Nasal codas (m, n) create specific closure patterns and resonance.
    They are common syllable-final consonants across many languages
    and contribute to syllable weight.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable ends with nasal, False otherwise

    Examples
    --------
    >>> ends_with_nasal("turn")
    True
    >>> ends_with_nasal("man")
    True
    >>> ends_with_nasal("bat")
    False
    >>> ends_with_nasal("")
    False

    Notes
    -----
    - Only checks the final character
    - Nasals defined in phoneme_sets.NASALS (m, n)
    - Nasal codas are distinct from stop codas in sonority
    - Empty strings return False (no coda to analyze)
    - See also: contains_nasal for position-independent detection
    """
    return bool(s) and s[-1] in NASALS


def ends_with_stop(s: str) -> bool:
    """
    Detect if syllable ends with a stop consonant (stop coda).

    Stop codas create abrupt syllable termination with complete
    airflow closure. They include plosives and other stops that
    contribute to syllable closure and weight.

    Parameters
    ----------
    s : str
        Syllable string to analyze

    Returns
    -------
    bool
        True if syllable ends with stop, False otherwise

    Examples
    --------
    >>> ends_with_stop("takt")
    True
    >>> ends_with_stop("bat")
    True
    >>> ends_with_stop("man")
    False
    >>> ends_with_stop("")
    False

    Notes
    -----
    - Only checks the final character
    - Stops defined in phoneme_sets.STOPS (p, t, k, b, d, g, q)
    - STOPS includes all PLOSIVES plus 'q' (terminal closure)
    - Stop codas create heavier, more closed syllables
    - Empty strings return False (no coda to analyze)
    - Distinction: STOPS for coda detection, PLOSIVES for internal texture
    """
    return bool(s) and s[-1] in STOPS


# -------------------------------------------------
# Feature Registry - Explicit enumerable feature set
# -------------------------------------------------

FEATURE_DETECTORS = {
    # Onset features - syllable-initial patterns
    "starts_with_vowel": starts_with_vowel,
    "starts_with_cluster": starts_with_cluster,
    "starts_with_heavy_cluster": starts_with_heavy_cluster,
    # Internal features - manner of articulation
    "contains_plosive": contains_plosive,
    "contains_fricative": contains_fricative,
    "contains_liquid": contains_liquid,
    "contains_nasal": contains_nasal,
    # Nucleus features - vowel structure (length proxies)
    "short_vowel": short_vowel,
    "long_vowel": long_vowel,
    # Coda features - syllable-final patterns
    "ends_with_vowel": ends_with_vowel,
    "ends_with_nasal": ends_with_nasal,
    "ends_with_stop": ends_with_stop,
}
# Explicit registry of all 12 feature detectors
# Total: 3 onset, 4 internal, 2 nucleus, 3 coda
# All detectors are pure functions (str -> bool)
# Features are independent (no detector depends on another)
