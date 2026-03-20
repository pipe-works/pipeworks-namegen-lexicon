"""
Fragment cleaning logic for NLTK syllable normalization.

This module provides the FragmentCleaner class which handles reconstruction
of phonetically coherent syllables from NLTK's over-segmented output by
merging isolated single-letter fragments with their neighbors.

---------------------------------------------------------------------------
Design Note (for future maintainers, including future-me):

This module is intentionally *strict and dumb*.

Its responsibility is limited to:
- Orthographic normalization
- Structural reconstruction of broken fragments
- Enforcing minimal length and basic phonetic viability

It MUST NOT:
- Remove fragments based on perceived meaning or “word-likeness”
- Apply language-, culture-, or corpus-specific filtering
- Decide whether a fragment is suitable as a name, place, or object
- Encode aesthetic judgement or semantic assumptions

Fragments such as common function words or corpus artefacts
(e.g. "of", "the") are expected to survive this stage.

Such cases are handled explicitly and *downstream* via:
- Feature detection
- Candidate aggregation
- Name-class selection policies

If a fragment appears questionable here, the correct response is:
“preserve and annotate”, not “clean away”.

This separation is deliberate and non-negotiable.
---------------------------------------------------------------------------
"""

VOWELS = set("aeiouy")


class FragmentCleaner:
    """
    Clean NLTK-produced syllable fragments by merging isolated letters.

    The NLTK syllable extractor uses phonetically-guided splitting with
    onset/coda principles, which can sometimes over-segment words into
    isolated single-letter fragments. This cleaner reconstructs more
    coherent syllables by applying mechanical merging rules.

    Merging Rules:
        1. Single vowels (a, e, i, o, u, y) merge with next fragment
        2. Single consonants merge with next fragment
        3. Multi-character fragments remain unchanged

    Example:
        >>> cleaner = FragmentCleaner()
        >>> fragments = ["i", "down", "the", "ra", "bbit"]
        >>> cleaner.clean_fragments(fragments)
        ['idown', 'the', 'rabbit']

    Note:
        This is NLTK-specific preprocessing. Pyphen output doesn't need
        fragment cleaning as it uses typographic hyphenation rules.
    """

    @staticmethod
    def is_single_letter(token: str) -> bool:
        """
        Check if token is a single alphabetic character.

        Args:
            token: String to check.

        Returns:
            True if token is exactly one alphabetic character, False otherwise.

        Example:
            >>> FragmentCleaner.is_single_letter("a")
            True
            >>> FragmentCleaner.is_single_letter("ab")
            False
            >>> FragmentCleaner.is_single_letter("1")
            False
        """
        return len(token) == 1 and token.isalpha()

    @staticmethod
    def is_single_vowel(token: str) -> bool:
        """
        Check if token is a single vowel character.

        Args:
            token: String to check.

        Returns:
            True if token is a single vowel (a, e, i, o, u, y), False otherwise.

        Example:
            >>> FragmentCleaner.is_single_vowel("a")
            True
            >>> FragmentCleaner.is_single_vowel("b")
            False
            >>> FragmentCleaner.is_single_vowel("ae")
            False
        """
        return len(token) == 1 and token.lower() in VOWELS

    def clean_fragments(self, fragments: list[str]) -> list[str]:
        """
        Perform mechanical cleanup by merging single-letter fragments.

        Applies two merging rules in sequence:
        1. Merge isolated single vowels with the following fragment
        2. Merge isolated single consonants with the following fragment

        This reconstructs more phonetically coherent syllables from
        NLTK's onset/coda-based over-segmentation.

        Args:
            fragments: List of syllable fragments (possibly over-segmented).

        Returns:
            List of cleaned fragments with single letters merged.

        Example:
            >>> cleaner = FragmentCleaner()
            >>> # Example 1: Single vowel merging
            >>> cleaner.clean_fragments(["i", "down"])
            ['idown']
            >>>
            >>> # Example 2: Single consonant merging
            >>> cleaner.clean_fragments(["r", "abbit"])
            ['rabbit']
            >>>
            >>> # Example 3: Mixed fragments
            >>> cleaner.clean_fragments(["cha", "pter", "i", "down", "the", "r", "a"])
            ['cha', 'pter', 'idown', 'the', 'ra']
            >>>
            >>> # Example 4: Preserve multi-character fragments
            >>> cleaner.clean_fragments(["hel", "lo", "world"])
            ['hel', 'lo', 'world']

        Note:
            - Fragments are processed left-to-right
            - Single letters merge with next fragment (if available)
            - Last fragment never merges (no next fragment available)
            - Empty input returns empty output
        """
        if not fragments:
            return []

        cleaned = []
        i = 0

        while i < len(fragments):
            current = fragments[i]

            # Lookahead safely
            next_frag = fragments[i + 1] if i + 1 < len(fragments) else None

            # Rule 1: Merge isolated single vowels with the next fragment
            if next_frag and self.is_single_vowel(current):
                merged = current + next_frag
                cleaned.append(merged)
                i += 2  # Skip both current and next
                continue

            # Rule 2: Merge single consonants with the next fragment
            if next_frag and self.is_single_letter(current):
                merged = current + next_frag
                cleaned.append(merged)
                i += 2  # Skip both current and next
                continue

            # Otherwise, keep fragment as-is
            cleaned.append(current)
            i += 1

        return cleaned

    def clean_fragments_from_file(self, input_path: str, output_path: str) -> tuple[int, int]:
        """
        Clean fragments from input file and write to output file.

        Convenience method for file-based processing. Reads one fragment
        per line from input file, applies cleaning, and writes cleaned
        fragments to output file (one per line).

        Args:
            input_path: Path to input file (one fragment per line).
            output_path: Path to output file for cleaned fragments.

        Returns:
            Tuple of (original_count, cleaned_count) indicating how many
            fragments were merged.

        Raises:
            FileNotFoundError: If input file doesn't exist.
            IOError: If there's an error reading or writing files.

        Example:
            >>> # input.txt contains:
            >>> # i
            >>> # down
            >>> # the
            >>> # ra
            >>> # bbit
            >>>
            >>> cleaner = FragmentCleaner()
            >>> original, cleaned = cleaner.clean_fragments_from_file(
            ...     "input.txt", "output.txt"
            ... )
            >>> print(f"Cleaned {original} → {cleaned} fragments")
            Cleaned 5 → 3 fragments
            >>>
            >>> # output.txt now contains:
            >>> # idown
            >>> # the
            >>> # rabbit
        """
        from pathlib import Path

        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Read fragments
        with input_file.open("r", encoding="utf-8") as f:
            fragments = [line.strip() for line in f if line.strip()]

        original_count = len(fragments)

        # Clean fragments
        cleaned = self.clean_fragments(fragments)
        cleaned_count = len(cleaned)

        # Write cleaned output
        with output_file.open("w", encoding="utf-8") as f:
            for frag in cleaned:
                f.write(frag + "\n")

        return original_count, cleaned_count
