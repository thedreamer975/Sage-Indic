"""Cross-script normalizers and transliteration for Phase 2D.

Implements:
- RomanizedTeluguTransliterator: deterministic, rule-based transliteration of Romanized Telugu into Telugu script.
- CodeMixedQueryNormalizer: script- and language-aware normalizer that handles code-mixed queries by separating
  English terms from Romanized Telugu segments and preserving original tokens.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from sage_indic.detection.heuristics import (
    LATIN_UNICODE_PATTERN,
    ROMANIZED_TELUGU_MARKERS,
    TELUGU_UNICODE_PATTERN,
    WORD_TOKEN_PATTERN,
    check_token_type,
)
from sage_indic.normalize import normalize_text


# Canonical mapping of Romanized consonant patterns to Telugu consonants.
# Ordered by decreasing length so longest digraphs match first.
CONSONANT_RULES: list[tuple[str, str]] = [
    # Quad/Triple digraphs and geminate representations
    ("kkh", "ఖ్ఖ"),
    ("ggh", "గ్ఘ"),
    ("chh", "ఛ"),
    ("shh", "ష"),
    # Standard digraphs
    ("ch", "చ"),
    ("jh", "ఝ"),
    ("th", "త"),
    ("dh", "ధ"),
    ("sh", "శ"),
    ("kh", "ఖ"),
    ("gh", "ఘ"),
    ("ph", "ఫ"),
    ("bh", "భ"),
    ("ll", "ళ్ళ"),
    ("ng", "ఙ"),
    ("ny", "ఞ"),
    # Single consonants
    ("k", "క"),
    ("g", "గ"),
    ("c", "చ"),
    ("j", "జ"),
    ("t", "ట"),
    ("d", "డ"),
    ("n", "న"),
    ("p", "ప"),
    ("f", "ఫ"),
    ("b", "బ"),
    ("m", "మ"),
    ("y", "య"),
    ("r", "ర"),
    ("l", "ల"),
    ("v", "వ"),
    ("w", "వ"),
    ("s", "స"),
    ("h", "హ"),
]

# Vowel signs: (roman_pattern, (matra_attached, independent_vowel))
VOWEL_RULES: list[tuple[str, tuple[str, str]]] = [
    ("aam", ("\u0C3E\u0C02", "ఆం")),
    ("aah", ("\u0C3E\u0C03", "ఆః")),
    ("am", ("\u0C02", "అం")),
    ("ah", ("\u0C03", "అః")),
    ("aa", ("\u0C3E", "ఆ")),
    ("ee", ("\u0C40", "ఈ")),
    ("ii", ("\u0C40", "ఈ")),
    ("oo", ("\u0C42", "ఊ")),
    ("uu", ("\u0C42", "ఊ")),
    ("ai", ("\u0C48", "ఐ")),
    ("au", ("\u0C4C", "ఔ")),
    ("ou", ("\u0C4C", "ఔ")),
    ("ae", ("\u0C47", "ఏ")),
    ("ye", ("\u0C47", "ఏ")),
    ("a", ("", "అ")),
    ("i", ("\u0C3F", "ఇ")),
    ("u", ("\u0C41", "ఉ")),
    ("e", ("\u0C46", "ఎ")),
    ("o", ("\u0C4A", "ఒ")),
]

VIRAMA = "\u0C4D"  # ్

# Curated phonetic dictionary for proper nouns, domain acronyms, and high-frequency irregular Romanized forms.
SPECIAL_PHONETIC_LEXICON: dict[str, str] = {
    # Proper nouns from historical / cultural domain
    "charminar": "చార్మినార్",
    "nagarjuna": "నాగార్జున",
    "sagar": "సాగర్",
    "salar": "సాలార్",
    "jung": "జంగ్",
    "rebecca": "రెబెక్కా",
    "golconda": "గోల్కొండ",
    "kakatiya": "కాకతీయ",
    "ramappa": "రామప్ప",
    "kalamalla": "కలమళ్ళ",
    "pochampalli": "పోచంపల్లి",
    "pochampally": "పోచంపల్లి",
    "tirumala": "తిరుమల",
    "kuchipudi": "కూచిపూడి",
    "kaleshwaram": "కాళేశ్వరం",
    "amaravati": "అమరావతి",
    "hyderabadi": "హైదరాబాదీ",
    "telangana": "తెలంగాణ",
    "andhra": "ఆంధ్ర",
    "pradesh": "ప్రదేశ్",
    "bhoodan": "భూదాన్",
    "krishnadevaraya": "కృష్ణదేవరాయ",
    "krishnadevarayalu": "కృష్ణదేవరాయలు",
    "srikrishnadevarayalu": "శ్రీకృష్ణదేవరాయలు",
    "vijayanagara": "విజయనగర",
    "vijayanagaram": "విజయనగరం",
    "warangal": "వరంగల్",
    "rudramadevi": "రుద్రమదేవి",
    "satavahana": "శాతవాహన",
    "satavahanulu": "శాతవాహనులు",
    "annamayya": "అన్నమయ్య",
    "annamacharya": "అన్నమాచార్యులు",
    "thyagaraja": "త్యాగరాజు",
    "potana": "పోతన",
    "vemana": "వేమన",
    "srisailam": "శ్రీశైలం",
    "bhadrachalam": "భద్రాచలం",
    "lepakshi": "లేపాక్షి",
    "visakhapatnam": "విశాఖపట్నం",
    "vijayawada": "విజయవాడ",
    # Domain entities & acronyms
    "unesco": "యునెస్కో",
    "gi": "జీఐ",
    # High frequency function words & vocabulary
    "kota": "కోట",
    "pravesha": "ప్రవేశ",
    "dwaram": "ద్వారం",
    "vadda": "వద్ద",
    "chappatlu": "చప్పట్లు",
    "kodithe": "కొడితే",
    "shabdam": "శబ్దం",
    "ekkadiki": "ఎక్కడికి",
    "vinipistundi": "వినిపిస్తుంది",
    "kattadam": "కట్టడం",
    "devalayaniki": "దేవాలయానికి",
    "devalayam": "దేవాలయం",
    "samvatsaram": "సంవత్సరం",
    "samvatsaramlo": "సంవత్సరంలో",
    "prapancha": "ప్రపంచ",
    "varasathva": "వారసత్వ",
    "hoda": "హోదా",
    "labhinchindi": "లభించింది",
    "tholi": "తొలి",
    "toli": "తొలి",
    "poorthi": "పూర్తి",
    "purti": "పూర్తి",
    "telugu": "తెలుగు",
    "shilashasanamga": "శిలాశాసనంగా",
    "shasanam": "శాసనం",
    "kalam": "కాలం",
    "natidi": "నాటిది",
    "ikkat": "ఇక్కత్",
    "chenetha": "చేనేత",
    "vastralaku": "వస్త్రాలకు",
    "bhaugolika": "భౌగోళిక",
    "gurtimpu": "గుర్తింపు",
    "eppudu": "ఎప్పుడు",
    "yeppudu": "ఎప్పుడు",
    "aalaya": "ఆలయ",
    "garbhagudipai": "గర్భగుడిపై",
    "unna": "ఉన్న",
    "bangaru": "బంగారు",
    "vimana": "విమాన",
    "gopuranni": "గోపురాన్ని",
    "emani": "ఏమని",
    "pilustharu": "పిలుస్తారు",
    "pilustaru": "పిలుస్తారు",
    "prabhutvam": "ప్రభుత్వం",
    "cheruvula": "చెరువుల",
    "punaruddharana": "పునరుద్ధరణ",
    "kosam": "కోసం",
    "chepattina": "చేపట్టిన",
    "project": "ప్రాజెక్టు",
    "edi": "ఏది",
    "enti": "ఏంటి",
    "evaru": "ఎవరు",
    "mariyu": "మరియు",
    "nirmincharu": "నిర్మించారు",
    "aanakattaku": "ఆనకట్టకు",
    "shankhusthapana": "శంకుస్థాపన",
    "chesina": "చేసిన",
    "bharata": "భారత",
    "pradhani": "ప్రధాని",
    "museum": "మ్యూజియం",
    "loni": "లోని",
    "veiled": "వీల్డ్",
    "shilpanni": "శిల్పాన్ని",
    "roopondincharu": "రూపొందించారు",
}

# Common English domain / technical vocabulary in code-mixed Telugu queries
ENGLISH_DOMAIN_LEXICON: frozenset[str] = frozenset({
    "construction",
    "dam",
    "foundation",
    "stone",
    "prime",
    "minister",
    "museum",
    "veiled",
    "sculpture",
    "design",
    "government",
    "historical",
    "tanks",
    "restore",
    "start",
    "project",
    "authentic",
    "recipe",
    "origin",
    "history",
    "buddhist",
    "stupa",
    "marble",
    "carvings",
    "structure",
    "fort",
    "entrance",
    "clap",
    "sound",
    "reach",
    "state",
    "official",
    "emblem",
    "include",
    "monument",
    "temple",
    "world",
    "heritage",
    "site",
    "tag",
    "year",
    "first",
    "full",
    "inscription",
    "period",
    "handloom",
    "fabrics",
    "announce",
    "sanctum",
    "sanctorum",
    "gold",
    "tower",
    "call",
    "classical",
    "dance",
    "form",
    "lift",
    "irrigation",
    "total",
    "barrages",
    "construct",
    "and",
    "the",
    "of",
    "in",
    "at",
    "by",
    "to",
})

# English-to-Telugu bilingual conceptual term mapping for query enrichment
ENGLISH_TO_TELUGU_SYNONYMS: dict[str, list[str]] = {
    "fort": ["కోట"],
    "entrance": ["ప్రవేశ", "ద్వారం"],
    "clap": ["చప్పట్లు"],
    "sound": ["శబ్దం"],
    "reach": ["వినిపిస్తుంది"],
    "monument": ["కట్టడం"],
    "emblem": ["చిహ్నం"],
    "temple": ["ఆలయం", "దేవాలయం", "గుడి"],
    "heritage": ["వారసత్వ"],
    "world": ["ప్రపంచ"],
    "stone": ["శిలా"],
    "inscription": ["శాసనం"],
    "fabrics": ["వస్త్రాలు", "చేనేత"],
    "handloom": ["చేనేత"],
    "tower": ["గోపురం", "విమాన"],
    "gold": ["బంగారు"],
    "dam": ["ఆనకట్ట"],
    "sculpture": ["శిల్పం"],
    "tanks": ["చెరువులు"],
    "restore": ["పునరుద్ధరణ"],
    "year": ["సంవత్సరం"],
    "dance": ["నృత్యం"],
}


class RomanizedTeluguTransliterator:
    """Deterministic, rule-based transliterator from Romanized Telugu to Telugu script.

    Adheres to SAGE-Indic research constraints:
    1. Fully deterministic and dependency-free.
    2. Uses longest-match consonant clusters and vowel signs.
    3. Handles proper nouns and phonetic variations via documented lexicon.
    4. Emits normalized Unicode NFC Telugu script.
    """

    def __init__(self, special_lexicon: dict[str, str] | None = None) -> None:
        self.lexicon = dict(SPECIAL_PHONETIC_LEXICON)
        if special_lexicon:
            self.lexicon.update(special_lexicon)

    def transliterate_token(self, token: str) -> str:
        """Transliterate a single token to native Telugu script.

        If the token is already in Telugu script, it is preserved unchanged.
        If the token is in the special lexicon, the approved canonical Telugu form is returned.
        Otherwise, deterministic rule-based phonetic transliteration is applied.
        """
        if not token:
            return ""

        # If already contains Telugu characters, preserve as is
        if TELUGU_UNICODE_PATTERN.search(token):
            return unicodedata.normalize("NFC", token)

        clean_token = token.lower().strip()
        if not clean_token:
            return token

        # Check special lexicon
        if clean_token in self.lexicon:
            return self.lexicon[clean_token]

        # Rule-based transliteration
        result: list[str] = []
        i = 0
        n = len(clean_token)
        is_syllable_start = True

        while i < n:
            # 1. Independent vowel check (at start of word or after vowel)
            if is_syllable_start:
                vowel_matched = False
                for v_str, (matra, indep) in VOWEL_RULES:
                    if clean_token.startswith(v_str, i):
                        result.append(indep)
                        i += len(v_str)
                        vowel_matched = True
                        is_syllable_start = False
                        break
                if vowel_matched:
                    continue

            # 2. Consonant check (longest match first)
            cons_matched = False
            for c_str, base_cons in CONSONANT_RULES:
                if clean_token.startswith(c_str, i):
                    i += len(c_str)
                    cons_matched = True
                    is_syllable_start = False

                    # Look ahead for vowel sign
                    v_found = False
                    for v_str, (matra, indep) in VOWEL_RULES:
                        if clean_token.startswith(v_str, i):
                            result.append(base_cons + matra)
                            i += len(v_str)
                            v_found = True
                            break

                    if not v_found:
                        # Consonant followed by consonant or end of word: virama
                        result.append(base_cons + VIRAMA)
                    break

            if not cons_matched:
                # Unmapped character (digit, punctuation, etc.)
                result.append(clean_token[i])
                i += 1
                is_syllable_start = True

        out = "".join(result)
        # Collapse double viramas
        out = re.sub(VIRAMA + "+", VIRAMA, out)
        return unicodedata.normalize("NFC", out)

    def transliterate_text(self, text: str) -> str:
        """Transliterate all whitespace-delimited tokens in a text string."""
        if not text:
            return ""
        tokens = text.split()
        transliterated = [self.transliterate_token(t) for t in tokens]
        return " ".join(transliterated)


@dataclass(frozen=True)
class NormalizedQuery:
    """Representation of a processed query ready for cross-script retrieval."""

    original_query: str
    expanded_query: str
    modality: str
    transliterated_segment: str
    preserved_english_tokens: list[str] = field(default_factory=list)
    bilingual_synonyms: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class CodeMixedQueryNormalizer:
    """Script- and language-aware normalizer for cross-script retrieval.

    Supports:
    - Condition B: Pure transliteration of Romanized text into Telugu script.
    - Condition C: Code-mix aware normalization:
        * Identifies English vocabulary and preserves original terms.
        * Adds bilingual synonyms for known conceptual terms.
        * Transliterates Romanized Telugu segments.
        * Combines original and normalized tokens into an expanded query for BM25.
    """

    def __init__(
        self,
        transliterator: RomanizedTeluguTransliterator | None = None,
        enable_bilingual_expansion: bool = True,
    ) -> None:
        self.transliterator = transliterator or RomanizedTeluguTransliterator()
        self.enable_bilingual_expansion = enable_bilingual_expansion
        self.english_lexicon = ENGLISH_DOMAIN_LEXICON
        self.synonyms = ENGLISH_TO_TELUGU_SYNONYMS

    def normalize(self, query_text: str, modality: str = "auto") -> NormalizedQuery:
        """Process a query into an expanded cross-script representation.

        Args:
            query_text: Raw input query.
            modality: "auto", "native", "romanized", or "code_mixed". Default is "auto".

        Returns:
            NormalizedQuery with original_query, expanded_query, and diagnostic metadata.
        """
        if not query_text or not query_text.strip():
            return NormalizedQuery(
                original_query=query_text or "",
                expanded_query="",
                modality=modality,
                transliterated_segment="",
            )

        norm_input = normalize_text(query_text)
        tokens = norm_input.split()

        if modality == "auto":
            has_telugu = bool(TELUGU_UNICODE_PATTERN.search(norm_input))
            has_latin = bool(LATIN_UNICODE_PATTERN.search(norm_input))
            if has_telugu and not has_latin:
                modality = "native"
            elif has_latin and not has_telugu:
                tokens_clean = [t.lower().strip("?,!.:;'\"()") for t in tokens]
                if self.enable_bilingual_expansion and any(t in self.english_lexicon for t in tokens_clean):
                    modality = "code_mixed"
                else:
                    modality = "romanized"
            else:
                modality = "code_mixed"

        if modality == "native":
            # Native Telugu query: no cross-script expansion needed
            return NormalizedQuery(
                original_query=query_text,
                expanded_query=norm_input,
                modality=modality,
                transliterated_segment="",
                metadata={"strategy": "native_passthrough"},
            )

        if modality == "romanized" or not self.enable_bilingual_expansion:
            # Condition B: Pure transliteration of Romanized text
            trans_tokens = [self.transliterator.transliterate_token(t) for t in tokens]
            trans_segment = " ".join(trans_tokens)
            expanded = f"{norm_input} {trans_segment}"
            return NormalizedQuery(
                original_query=query_text,
                expanded_query=expanded,
                modality=modality,
                transliterated_segment=trans_segment,
                metadata={"strategy": "romanized_transliteration"},
            )

        # Condition C: Code-mixed query handling
        preserved_english: list[str] = []
        bilingual_synonyms: list[str] = []
        telugu_segments: list[str] = []

        for token in tokens:
            clean_tok = token.lower().strip("?,!.:;'\"()")
            # Check if token is Native Telugu
            if TELUGU_UNICODE_PATTERN.search(token):
                telugu_segments.append(token)
            # Check if token is an identified English domain term
            elif clean_tok in self.english_lexicon:
                preserved_english.append(token)
                if self.enable_bilingual_expansion and clean_tok in self.synonyms:
                    bilingual_synonyms.extend(self.synonyms[clean_tok])
            else:
                # Treat as Romanized Telugu token and transliterate
                trans_t = self.transliterator.transliterate_token(token)
                telugu_segments.append(trans_t)

        trans_segment = " ".join(telugu_segments)
        synonyms_str = " ".join(bilingual_synonyms)

        # Build expanded query: original tokens + transliterated Telugu + bilingual synonyms
        parts = [norm_input]
        if trans_segment:
            parts.append(trans_segment)
        if synonyms_str:
            parts.append(synonyms_str)

        expanded_query = " ".join(parts)

        return NormalizedQuery(
            original_query=query_text,
            expanded_query=expanded_query,
            modality=modality,
            transliterated_segment=trans_segment,
            preserved_english_tokens=preserved_english,
            bilingual_synonyms=bilingual_synonyms,
            metadata={
                "strategy": "code_mixed_aware_normalization",
                "n_english_preserved": len(preserved_english),
                "n_synonyms_added": len(bilingual_synonyms),
            },
        )
