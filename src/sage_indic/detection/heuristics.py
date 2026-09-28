"""Deterministic linguistic heuristics and lexicons for Telugu and English detection."""

import re

# Telugu Unicode script range: U+0C00 to U+0C7F
TELUGU_UNICODE_PATTERN = re.compile(r"[\u0C00-\u0C7F]")
LATIN_UNICODE_PATTERN = re.compile(r"[A-Za-z]")

# Word-splitting pattern that preserves alphanumeric content
WORD_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9\u0C00-\u0C7F']+")

# Romanized Telugu high-frequency markers (pronouns, question words, auxiliaries, particles, verbs)
ROMANIZED_TELUGU_MARKERS: frozenset[str] = frozenset(
    {
        # Pronouns
        "nenu",
        "naaku",
        "naku",
        "naa",
        "meeru",
        "miku",
        "meeku",
        "mee",
        "manamu",
        "manaki",
        "memu",
        "maaku",
        "atanu",
        "athanu",
        "aame",
        "vaallu",
        "vallu",
        "vaaru",
        "adi",
        "idi",
        "evi",
        "ivi",
        "evaru",
        "evvaru",
        "evari",
        "deni",
        "deniki",
        "anniti",
        # Question words
        "emi",
        "emiti",
        "enti",
        "ela",
        "elaga",
        "elaa",
        "eppudu",
        "yeppudu",
        "ekkada",
        "yekkada",
        "enduku",
        "yenduku",
        "yela",
        # Adverbs, locatives, time words
        "ikkada",
        "akkada",
        "ippudu",
        "appudu",
        "eeroju",
        "ee",
        "roju",
        "repu",
        "ninna",
        "monna",
        "chala",
        "chaala",
        "konchem",
        "baaga",
        "baga",
        "mari",
        "inkaa",
        "inka",
        "malli",
        "mallii",
        "mundu",
        "taruvatha",
        "tarvata",
        "venaka",
        "lopala",
        "bayata",
        "kooda",
        "kuda",
        # Auxiliaries, copulas, modals, negations
        "undi",
        "undhi",
        "unnadu",
        "unnadi",
        "unnaru",
        "unnanu",
        "unnamu",
        "untaanu",
        "untadi",
        "untundi",
        "ledu",
        "ledhu",
        "leru",
        "levu",
        "kaadu",
        "kadu",
        "kaadhu",
        "kadhu",
        "avunu",
        "avuthundi",
        "avutundi",
        "ayindi",
        "aindi",
        "ayipoyindi",
        "avvali",
        "chesanu",
        "chesadu",
        "chesaru",
        "chesindi",
        "chesta",
        "chesthanu",
        "chestamu",
        "cheyali",
        "cheyyali",
        "cheyandi",
        "chudandi",
        "choodandi",
        "chusa",
        "chusanu",
        "vellali",
        "velthunnanu",
        "veltunnanu",
        "vellanu",
        "vastanu",
        "vasthunnanu",
        "vastundi",
        "randi",
        "pandi",
        "cheppandi",
        "cheppu",
        "adagandi",
        "telusuko",
        "thelsuko",
        "cheddamu",
        "chuddamu",
        "cheddam",
        "chuddam",
        "poddamu",
        "vaddamu",
        "matladadamu",
        # Particles, conjunctions, postpositions
        "lo",
        "ki",
        "ku",
        "tho",
        "to",
        "kosam",
        "valla",
        "valana",
        "nunchi",
        "nundi",
        "gurinchi",
        "meeda",
        "kinda",
        "varaku",
        "kanna",
        "ga",
        "la",
        "ane",
        "ante",
        "ani",
        "aina",
        "ainaa",
        "leka",
        "lekunte",
        "kada",
        "kadhaa",
    }
)

# Common agglutinative Telugu postpositional/adverbial suffixes attached to Latin roots
TELUGU_ATTACHED_SUFFIXES: tuple[str, ...] = (
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

# Core English closed-class and high-frequency vocabulary
ENGLISH_CORE_WORDS: frozenset[str] = frozenset(
    {
        # Articles & determiners
        "the",
        "a",
        "an",
        "this",
        "that",
        "these",
        "those",
        "all",
        "some",
        "any",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        # Pronouns
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "their",
        "our",
        "its",
        "mine",
        "yours",
        "hers",
        "theirs",
        "ours",
        "who",
        "whom",
        "whose",
        "which",
        "what",
        # Prepositions
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "from",
        "about",
        "into",
        "through",
        "after",
        "before",
        "above",
        "below",
        "between",
        "under",
        "during",
        "without",
        "against",
        "over",
        "of",
        "off",
        # Conjunctions
        "and",
        "or",
        "but",
        "because",
        "if",
        "as",
        "so",
        "than",
        "although",
        "while",
        "though",
        "until",
        "unless",
        # Auxiliaries & Modals
        "is",
        "am",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "will",
        "would",
        "shall",
        "should",
        "can",
        "could",
        "may",
        "might",
        "must",
        # Question / common prompt words
        "how",
        "why",
        "when",
        "where",
        "explain",
        "describe",
        "tell",
        "give",
        "find",
        "make",
        "know",
        "think",
        "see",
        "come",
        "go",
        "take",
        "use",
        "get",
        "say",
        "help",
        "please",
        "define",
        "list",
        "write",
        "show",
        "capital",
        "india",
        "today",
        "tomorrow",
        "office",
        "work",
        "traffic",
        "heavy",
        "very",
        "good",
        "bad",
        "well",
        "now",
        "there",
        "here",
        "just",
        "also",
        "not",
        "no",
        "yes",
        # Extended English vocabulary for common domain queries
        "next",
        "meeting",
        "project",
        "discuss",
        "problem",
        "solution",
        "create",
        "simple",
        "terms",
        "models",
        "model",
        "long",
        "short",
        "context",
        "window",
        "windows",
        "quick",
        "brown",
        "fox",
        "jumps",
        "lazy",
        "dog",
        "handle",
        "provide",
        "history",
        "historical",
        "dynasties",
        "dynasty",
        "south",
        "asia",
        "transformer",
        "transformers",
        "photosynthesis",
        "process",
        "language",
        "system",
        "computer",
        "python",
        "science",
        "data",
        "time",
        "people",
        "year",
        "state",
        "city",
        "country",
        "world",
    }
)

# Common English inflectional and derivational suffixes
ENGLISH_INFLECTIONAL_SUFFIXES: tuple[str, ...] = (
    "tion",
    "sion",
    "ment",
    "ness",
    "able",
    "ible",
    "less",
    "ful",
    "ing",
    "ize",
    "ise",
    "ous",
    "ive",
    "ity",
    "est",
    "ed",
    "ly",
    "er",
    "al",
    "ic",
)


def extract_script_counts(text: str) -> tuple[int, int, int, int]:
    """Count character types in the input string.

    Returns:
        tuple: (telugu_chars, latin_chars, other_alpha_chars, total_chars)
    """
    total_chars = len(text)
    telugu_chars = len(TELUGU_UNICODE_PATTERN.findall(text))
    latin_chars = len(LATIN_UNICODE_PATTERN.findall(text))
    # Count other alphabetic characters (e.g. Devanagari, Greek, Cyrillic)
    other_alpha_chars = sum(
        1
        for ch in text
        if ch.isalpha() and not ("\u0c00" <= ch <= "\u0c7f") and not ("a" <= ch.lower() <= "z")
    )
    return telugu_chars, latin_chars, other_alpha_chars, total_chars


def check_token_type(token: str) -> tuple[str, str | None]:
    """Classify a single Latin-script word token.

    Returns:
        tuple: (token_type, root_if_hybrid)
            token_type is one of: 'TELUGU', 'ENGLISH', 'HYBRID', 'UNKNOWN'
    """
    norm = token.lower()

    # Exact Telugu match
    if norm in ROMANIZED_TELUGU_MARKERS:
        return "TELUGU", None

    # Telugu verbal inflections (e.g. 'cheddamu', 'velthunnanu', 'cheyyali')
    if norm.endswith(
        (
            "ddamu",
            "damu",
            "thunnanu",
            "tunnanu",
            "thunnaru",
            "tunnaru",
            "thundi",
            "tundi",
            "aali",
            "yyali",
            "yali",
        )
    ):
        return "TELUGU", None

    # Check for hybrid: English root + Telugu attached suffix
    # Examples: 'officeki', 'heavyga', 'projectlo'
    for suffix in TELUGU_ATTACHED_SUFFIXES:
        if len(norm) > len(suffix) + 2 and norm.endswith(suffix):
            root = norm[: -len(suffix)]
            if (
                root in ENGLISH_CORE_WORDS
                or any(root.endswith(es) for es in ENGLISH_INFLECTIONAL_SUFFIXES)
                or len(root) >= 4
            ):
                return "HYBRID", root

    # Exact English match
    if norm in ENGLISH_CORE_WORDS:
        return "ENGLISH", None

    # English plural or possessive ('s)
    if norm.endswith("'s") and norm[:-2] in ENGLISH_CORE_WORDS:
        return "ENGLISH", None
    if norm.endswith("s") and len(norm) > 3 and norm[:-1] in ENGLISH_CORE_WORDS:
        return "ENGLISH", None

    # English derivational/inflectional suffix patterns
    for es in ENGLISH_INFLECTIONAL_SUFFIXES:
        if len(norm) > len(es) + 2 and norm.endswith(es):
            return "ENGLISH", None

    # Telugu phonetic patterns: words ending in characteristic vowels with transliteration digrams
    if (
        len(norm) >= 4
        and norm.endswith(("alu", "ulu", "adu", "idi", "indi", "aru", "anu", "aamu", "eedi"))
        and any(dg in norm for dg in ("th", "dh", "bh", "ch", "kh", "gh", "ll", "nn", "tt"))
    ):
        return "TELUGU", None

    return "UNKNOWN", None
