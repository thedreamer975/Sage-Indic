"""Telugu linguistic pre-segmentation and morphological boundary analysis for SAGE Tokenizer."""

import re

# Telugu Akshara (orthographic syllable) regular expression
# Matches:
# 1. Consonant with optional virama-linked conjuncts, vowel signs, and anusvara/visarga
# 2. Independent vowels with optional anusvara/visarga
# 3. Non-Telugu character runs
TELUGU_AKSHARA_REGEX = re.compile(
    r"([\u0C15-\u0C39\u0C58-\u0C5A](?:\u0C4D[\u0C15-\u0C39\u0C58-\u0C5A])*[\u0C3E-\u0C4C]?[\u0C01-\u0C03]?"
    r"|[\u0C05-\u0C14][\u0C01-\u0C03]?"
    r"|[^\u0C00-\u0C7F\s]+"
    r"|\s+)"
)

# High-frequency Telugu nominal postpositions and case markers (Vibhakti pratyayalu)
# Sorted descending by length to match longest affixes first
NATIVE_TELUGU_NOMINAL_AFFIXES: tuple[str, ...] = (
    "గురించి",
    "నుంచి",
    "నుండి",
    "కోసం",
    "వరకు",
    "కన్నా",
    "వలన",
    "వల్ల",
    "లాగా",
    "మీద",
    "కింద",
    "తో",
    "లో",
    "కి",
    "కు",
    "గా",
    "లా",
    "లు",
    "ని",
    "ను",
)

# High-frequency Telugu verbal inflection endings
NATIVE_TELUGU_VERBAL_AFFIXES: tuple[str, ...] = (
    "త్తున్నాను",
    "తున్నారు",
    "త్తుంది",
    "తున్నారు",
    "చేశాను",
    "చేశారు",
    "వాలి",
    "యాలి",
    "య్యాలి",
    "డము",
    "ద్దము",
    "టం",
    "డం",
)

# Romanized Telugu postpositions and verbal endings
ROMANIZED_TELUGU_AFFIXES: tuple[str, ...] = (
    "gurinchi",
    "nunchi",
    "nundi",
    "kosam",
    "varaku",
    "kanna",
    "valana",
    "valla",
    "laaga",
    "laga",
    "thunnanu",
    "tunnanu",
    "thunnaru",
    "tunnaru",
    "thundi",
    "tundi",
    "chesanu",
    "chesaru",
    "ddamu",
    "damu",
    "aali",
    "yyali",
    "yali",
    "tho",
    "to",
    "lo",
    "ki",
    "ku",
    "ga",
    "lu",
    "ni",
    "nu",
)


def split_into_aksharas(word: str) -> list[str]:
    """Segment native Telugu word into atomic orthographic syllables (aksharas).

    Non-Telugu characters are grouped into contiguous runs.
    """
    if not word:
        return []
    return [m.group() for m in TELUGU_AKSHARA_REGEX.finditer(word) if m.group().strip()]


def segment_word_morphology(
    word: str,
    enable_affixes: bool = True,
    affix_marker: str = "##",
) -> list[str]:
    """Segment a word into base stem and high-frequency Telugu affixes with exact slicing.

    Args:
        word: Whitespace-delimited word token.
        enable_affixes: If True, identifies and detaches valid affixes.
        affix_marker: Prefix string for detached affixes (default '##').

    Returns:
        List of segments, e.g. ['హైదరాబాద్', '##\u200cలో'] or ['office', '##ki'].
    """
    if not enable_affixes or len(word) < 4:
        return [word]

    is_telugu = any("\u0c00" <= ch <= "\u0c7f" for ch in word)

    if is_telugu:
        # Check nominal postpositions first
        for affix in NATIVE_TELUGU_NOMINAL_AFFIXES:
            # Check with and without preceding ZWNJ / virama connecting sequences
            variants = [
                f"\u200c{affix}",
                f"\u0c4d\u200c{affix}",
                f"\u0c4d{affix}",
                affix,
            ]
            for pat in variants:
                if word.endswith(pat) and len(word) > len(pat) + 1:
                    split_idx = len(word) - len(pat)
                    stem = word[:split_idx]
                    suffix = word[split_idx:]
                    if len(stem) >= 2:
                        return [stem, f"{affix_marker}{suffix}"]

        # Check verbal inflection endings
        for affix in NATIVE_TELUGU_VERBAL_AFFIXES:
            variants = [
                f"\u200c{affix}",
                f"\u0c4d\u200c{affix}",
                f"\u0c4d{affix}",
                affix,
            ]
            for pat in variants:
                if word.endswith(pat) and len(word) > len(pat) + 1:
                    split_idx = len(word) - len(pat)
                    stem = word[:split_idx]
                    suffix = word[split_idx:]
                    if len(stem) >= 2:
                        return [stem, f"{affix_marker}{suffix}"]

    else:
        # Romanized / Latin Code-Mixed affixes
        norm = word.lower()
        for affix in ROMANIZED_TELUGU_AFFIXES:
            if norm.endswith(affix) and len(norm) > len(affix) + 2:
                split_idx = len(word) - len(affix)
                stem = word[:split_idx]
                suffix = word[split_idx:]
                if len(stem) >= 3:
                    return [stem, f"{affix_marker}{suffix}"]

    return [word]


def presegment_sentence(
    sentence: str,
    enable_affixes: bool = True,
    affix_marker: str = "##",
) -> list[str]:
    """Pre-segment sentence into whitespace-delimited word tokens and morphology-split units."""
    if not sentence:
        return []

    words = sentence.split()
    segments: list[str] = []
    for w in words:
        sub_units = segment_word_morphology(
            w, enable_affixes=enable_affixes, affix_marker=affix_marker
        )
        segments.extend(sub_units)

    return segments
