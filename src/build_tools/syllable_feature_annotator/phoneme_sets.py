"""
Character class definitions for syllable feature annotation.

This module defines character sets used for structural pattern detection in syllables.
These sets are language-agnostic and based purely on observable character properties.

Design Principles
-----------------
1. **Pure data structures**: Sets only, no logic or behavior
2. **Explicit membership**: Clear, enumerable character classes
3. **Immutable definitions**: Constants that don't change at runtime
4. **Set-based lookup**: O(1) membership testing for performance

Character Classes
-----------------
VOWELS : set[str]
    Vowel characters (a, e, i, o, u)
PLOSIVES : set[str]
    Plosive/stop consonants that inject hardness (p, t, k, b, d, g)
FRICATIVES : set[str]
    Fricative consonants with continuous airflow (f, s, z, v, h)
NASALS : set[str]
    Nasal consonants (m, n)
LIQUIDS : set[str]
    Liquid consonants (l, r, w)
STOPS : set[str]
    Consonants that terminate flow (plosives + q)

Usage
-----
Character sets are used for membership testing in feature detection::

    >>> from build_tools.syllable_feature_annotator.phoneme_sets import VOWELS, PLOSIVES
    >>> 'a' in VOWELS
    True
    >>> 't' in PLOSIVES
    True
    >>> 's' in PLOSIVES
    False

Implementation Notes
--------------------
- **Set Construction**: Using ``set("abc")`` converts a string to a character set efficiently
- **Set Operations**: STOPS is constructed using set union (``|``) operator
- **Performance**: Set membership testing is O(1), making it ideal for frequent lookups
- **Immutability**: These are module-level constants and should not be modified at runtime

Why Sets?
---------
Using sets instead of lists or strings provides:

1. **Fast Membership Testing**: O(1) vs O(n) for lists
2. **Clear Intent**: "Does this character belong to this class?"
3. **Set Operations**: Easy to combine classes (union, intersection, difference)
4. **No Duplicates**: Character uniqueness enforced automatically

Example
-------
Check if a syllable starts with a vowel::

    from build_tools.syllable_feature_annotator.phoneme_sets import VOWELS

    syllable = "apple"
    if syllable and syllable[0] in VOWELS:
        print("Starts with vowel")

Combining character classes::

    from build_tools.syllable_feature_annotator.phoneme_sets import PLOSIVES, FRICATIVES

    # All consonants that are either plosives or fricatives
    obstruents = PLOSIVES | FRICATIVES

    if any(char in obstruents for char in syllable):
        print("Contains obstruent")

Design Notes
------------
**Why 'q' is in STOPS but not PLOSIVES**:

The distinction between PLOSIVES and STOPS is subtle but intentional:

- **PLOSIVES**: Characters that inject hardness/texture *anywhere* in a syllable
- **STOPS**: Characters that specifically *terminate flow* at syllable boundaries

The character 'q' contributes to closure (stopping flow) but doesn't necessarily
contribute the same internal plosive texture as 'p', 't', 'k', etc. This separation
allows for more nuanced feature detection in coda positions.

**Why these specific characters?**:

These character classes are designed for the canonical syllables produced by the
syllable normalizer, which strips diacritics and normalizes to ASCII lowercase.
The sets focus on the most common phonetic patterns in the normalized corpus.

Future Extensions
-----------------
Additional character classes can be added as needed for more sophisticated
feature detection (e.g., APPROXIMANTS, SIBILANTS, GLIDES). The modular design
makes extension straightforward without affecting existing detectors.
"""

# Core vowel set - defines syllable nuclei
VOWELS = set("aeiou")

# Plosive/stop consonants - inject hardness and texture
# Also known as "stops" in phonetics, but we use PLOSIVES to distinguish
# from the STOPS set which includes terminal closures
PLOSIVES = set("ptkbdg")

# Fricative consonants - continuous airflow with friction
FRICATIVES = set("fszvh")

# Nasal consonants - airflow through nasal cavity
NASALS = set("mn")

# Liquid consonants - vowel-like consonants with lateral or rhotic quality
LIQUIDS = set("lrw")

# Stop consonants - consonants that terminate flow
# Includes all plosives plus 'q' which contributes to closure
# The distinction: PLOSIVES for internal texture, STOPS for coda detection
STOPS = PLOSIVES | {"q"}
