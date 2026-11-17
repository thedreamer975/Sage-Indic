"""Deterministic query understanding and evidence sentence selection for Phase 2G.

This module is intentionally rule-based and inspectable. It does not claim to be a
semantic parser or an NLI model. Its purpose is to make the demo's evidence
selection reproducible and to make weak/irrelevant retrieval visible instead of
silently answering from unrelated passages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sage_indic.composition.types import QueryAnalysis, QueryIntent
from sage_indic.rag.retriever import tokenize_for_bm25
from sage_indic.rag.types import RetrievalResult

# Function words and meta-question vocabulary are excluded from evidence-coverage
# scoring. This list is deliberately small and documented as a demo heuristic.
STOPWORDS: set[str] = {
    # Telugu
    "ఏమిటి",
    "ఏది",
    "ఏమి",
    "ఎప్పుడు",
    "ఎక్కడ",
    "ఎవరు",
    "ఎంత",
    "ఎన్ని",
    "ఏ",
    "ఈ",
    "ఆ",
    "ఒక",
    "మరియు",
    "లో",
    "కి",
    "కు",
    "నుండి",
    "తో",
    "గా",
    "ఉంది",
    "ఉన్న",
    "ఉన్నది",
    "ఉన్నాయి",
    "ఉంటుంది",
    "ఉన్డి",
    "ఉన్డ",
    "గురించి",
    "చెప్పు",
    "చెప్పండి",
    "చెప్పగలరా",
    "వివరించు",
    "వివరించండి",
    "వివరాలు",
    "తెలుపు",
    "తెలపండి",
    "ఏమిటంటే",
    "అంటే",
    "ప్రకారం",
    "దయచేసి",
    # Romanized Telugu
    "eppudu",
    "ekkada",
    "evaru",
    "entha",
    "enni",
    "emi",
    "enti",
    "gurinchi",
    "cheppu",
    "cheppandi",
    "vivarinchu",
    "vivaralu",
    "telupu",
    "unnai",
    "unnadi",
    "unna",
    "unnayi",
    "undhi",
    "undi",
    "lo",
    "ki",
    "ku",
    "nunchi",
    "tho",
    "ga",
    "oka",
    "mariyu",
    # English
    "what",
    "is",
    "are",
    "the",
    "of",
    "a",
    "an",
    "in",
    "on",
    "for",
    "to",
    "and",
    "tell",
    "me",
    "about",
    "please",
    "explain",
    "describe",
    "give",
    "information",
    "details",
    "where",
    "when",
    "who",
    "how",
    "many",
    "much",
    "which",
}

# Transparent, generic query-expansion groups. These are not answers; they are
# alternate surface forms used only for evidence matching.
SYNONYM_GROUPS: list[set[str]] = [
    {"గోల్కొండ", "golconda", "golkonda"},
    {"చార్మినార్", "charminar"},
    {"కోట", "fort", "qila", "దుర్గం"},
    {"దేవాలయం", "temple", "ఆలయం", "గుడి"},
    {"నది", "river", "ఏరు"},
    {"నగరం", "city", "పట్టణం"},
    {"ప్రాంతం", "location", "place", "area", "స్థానం", "భాగం"},
    {
        "నిర్మాణం",
        "construction",
        "built",
        "build",
        "నిర్మించ",
        "నిర్మించాడు",
        "నిర్మించారు",
        "కట్ట",
        "nirmincharu",
        "nirminchadu",
        "nirmicharu",
        "kattaru",
    },
    {"చరిత్ర", "history", "historical", "చారిత్రక"},
    {"సంవత్సరం", "year", "date", "తేదీ", "శకం", "కాలం"},
    {"ఎత్తు", "height", "tall"},
    {"ఖర్చు", "cost", "price", "వ్యయం", "బడ్జెట్"},
    {"రాజు", "king", "ruler", "సుల్తాన్", "చక్రవర్తి", "పాలకుడు"},
    {"రాజధాని", "capital"},
    {"ఫ్రాన్స్", "france"},
    {"భాష", "language"},
    {"ప్రాచీన", "ancient", "old", "ప్రాచీనత"},
    {"మినార్", "minaret", "minarets", "మినార్లు"},
    {"వజ్రం", "diamond", "diamonds", "వజ్రాలు"},
    {"మ్యూజియం", "museum"},
    {"జలాశయం", "dam", "reservoir", "ఆనకట్ట"},
    {"చేనేత", "weaving", "handloom"},
    {"శ్రీకృష్ణదేవరాయలు", "కృష్ణదేవరాయలు", "కృష్ణదేవరాయ", "krishnadevarayalu", "krishnadevaraya", "srikrishnadevarayalu"},
    {"విజయనగర", "విజయనగరం", "vijayanagara", "vijayanagaram"},
    {"కాకతీయులు", "కాకతీయ", "kakatiya", "kakatiyulu"},
    {"రుద్రమదేవి", "రుద్రమ", "rudramadevi", "rudrama"},
    {"శాతవాహనులు", "శాతవాహన", "satavahana", "satavahanulu"},
    {"వరంగల్", "warangal"},
    {"తిరుమల", "తిరుపతి", "tirumala", "tirupati"},
]

_GROUP_LOOKUP: dict[str, int] = {}
for _idx, _group in enumerate(SYNONYM_GROUPS):
    for _term in _group:
        _GROUP_LOOKUP[_term.lower()] = _idx


@dataclass
class SentenceCandidate:
    """One evidence sentence considered for extractive answer composition."""

    evidence_id: str
    document_id: str
    chunk_id: str
    sentence: str
    score: float
    matched_terms: list[str] = field(default_factory=list)


def _stem_prefix_len(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    idx = 0
    while idx < limit and left[idx] == right[idx]:
        idx += 1
    return idx


def fuzzy_term_in_text(term: str, text: str, text_tokens: set[str] | None = None) -> bool:
    """Return True if ``term`` occurs in ``text`` exactly or as a close stem prefix.

    Telugu is agglutinative, and the demo corpus frequently inflects verbs
    (నిర్మించాడు vs నిర్మించారు). A conservative shared-prefix match lets the
    retriever/composer recognise these variants without pretending to perform
    full morphological analysis.
    """
    if not term:
        return False
    if term in text:
        return True
    tokens = text_tokens if text_tokens is not None else set(tokenize_for_bm25(text))
    is_telugu = any("\u0c00" <= ch <= "\u0c7f" for ch in term)
    min_prefix = 3 if is_telugu else 4
    for token in tokens:
        if token == term:
            return True
        if len(token) < 2:
            continue
        shared = _stem_prefix_len(term, token)
        if shared >= min_prefix and shared >= min(len(term), len(token)) - 2:
            return True
    return False


def _term_group_key(term: str) -> str:
    idx = _GROUP_LOOKUP.get(term.lower())
    if idx is None:
        return term.lower()
    return f"g{idx}:{sorted(SYNONYM_GROUPS[idx])[0]}"


def build_content_groups(text: str) -> dict[str, list[str]]:
    """Group informative query terms with their transparent synonym variants."""
    groups: dict[str, list[str]] = {}
    for token in tokenize_for_bm25(text):
        if token in STOPWORDS or len(token) < 2:
            continue
        key = _term_group_key(token)
        variants = groups.setdefault(key, [])
        idx = _GROUP_LOOKUP.get(token.lower())
        if idx is not None:
            for synonym in SYNONYM_GROUPS[idx]:
                if synonym not in variants:
                    variants.append(synonym)
        else:
            try:
                from sage_indic.rag.normalizer import SPECIAL_PHONETIC_LEXICON
                te_trans = SPECIAL_PHONETIC_LEXICON.get(token.lower())
                if te_trans and te_trans not in variants:
                    variants.append(te_trans)
            except Exception:
                pass
        if token not in variants:
            variants.append(token)
    return groups


def match_content_groups(
    groups: dict[str, list[str]],
    text: str,
) -> tuple[list[str], list[str]]:
    """Return (matched group keys, missing group keys) for a passage."""
    text_tokens = set(tokenize_for_bm25(text))
    matched: list[str] = []
    missing: list[str] = []
    for key, variants in groups.items():
        if any(fuzzy_term_in_text(v, text, text_tokens) for v in variants):
            matched.append(key)
        else:
            missing.append(key)
    return matched, missing


def detect_intent(text: str) -> QueryIntent:
    """Classify a coarse question type from Telugu/Romanized/English cues."""
    lowered = text.lower()
    if re.search(
        r"ఎప్పుడు|ఏ\s*సంవత్సరం|ఏ\s*శతాబ్దం|\beppudu\b|\bwhen\b|"
        r"what\s+year|which\s+year|\bdate\b",
        lowered,
    ):
        return QueryIntent.WHEN
    if re.search(r"ఎక్కడ|ఎక్కడి|\bekkada\b|\bwhere\b|\blocation\b|స్థానం|ప్రాంతం", lowered):
        return QueryIntent.WHERE
    if re.search(r"ఎవరు|ఎవరిచే|ఎవరు\s*నిర్మించ|\bevaru\b|\bwho\b", lowered):
        return QueryIntent.WHO
    if re.search(r"ఎంత|ఎన్ని|ఎత్తు|\bentha\b|\benni\b|how\s+many|how\s+much|\bheight\b", lowered):
        return QueryIntent.HOW_MANY
    if re.search(
        r"గురించి|అంటే|ఏమిటి|వివరించు|\babout\b|what\s+is|explain|describe|"
        r"చరిత్ర|\bhistory\b",
        lowered,
    ):
        return QueryIntent.DEFINITION
    return QueryIntent.GENERAL


def _intent_bonus(intent: QueryIntent, sentence: str) -> float:
    bonus = 0.0
    if intent == QueryIntent.WHEN:
        if re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", sentence):
            bonus += 1.8
        if re.search(r"సంవత్సరం|శకం|శతాబ్ద|కాలంలో|తర్వాత|ముందు", sentence):
            bonus += 0.7
    elif intent == QueryIntent.WHERE:
        if re.search(r"ఉంది|ఉన్న|ప్రాంతంలో|భాగంలో|నగరంలో|ఒడ్డున|జిల్లా|సమీపంలో|లో", sentence):
            bonus += 0.9
    elif intent == QueryIntent.HOW_MANY:
        if re.search(r"\b\d+\b|నాలుగు|మూడు|రెండు|ఐదు|ఆరు|ఏడు|ఎనిమిది|తొమ్మిది|పది", sentence):
            bonus += 1.4
    elif intent == QueryIntent.WHO:
        if re.search(r"సుల్తాన్|రాజు|చక్రవర్తి|కవి|పాలకుడు|నిర్మించాడు|నిర్మించారు", sentence):
            bonus += 0.7
    elif intent == QueryIntent.DEFINITION:
        bonus += 0.15
    return bonus


def split_sentences(text: str) -> list[str]:
    """Split evidence text into sentences without destroying Telugu punctuation."""
    candidates = re.split(r"(?<=[.!?।])\s+", text.strip())
    return [c.strip() for c in candidates if len(c.strip()) >= 8]


def select_sentences(
    query_text: str,
    results: list[RetrievalResult],
    groups: dict[str, list[str]],
    intent: QueryIntent,
    max_sentences: int = 2,
) -> list[SentenceCandidate]:
    """Rank evidence sentences by query-term coverage, title overlap, and intent cues."""
    candidates: list[SentenceCandidate] = []
    for result in results:
        title_groups, _ = match_content_groups(groups, result.title)
        for position, sentence in enumerate(split_sentences(result.text)):
            matched, _ = match_content_groups(groups, sentence)
            if not matched:
                continue
            coverage = len(matched) / max(len(groups), 1)
            score = coverage * 3.0
            score += min(len(matched), 3) * 0.35
            score += _intent_bonus(intent, sentence)
            score += 0.45 * len(title_groups)
            if position == 0:
                score += 0.10
            if len(sentence) > 500:
                score -= 0.5
            candidates.append(
                SentenceCandidate(
                    evidence_id=result.chunk_id,
                    document_id=result.document_id,
                    chunk_id=result.chunk_id,
                    sentence=sentence,
                    score=round(score, 4),
                    matched_terms=matched,
                )
            )

    candidates.sort(key=lambda c: (-c.score, c.document_id, c.chunk_id))
    if not candidates:
        return []

    selected: list[SentenceCandidate] = [candidates[0]]
    best_score = candidates[0].score
    covered_groups = set(candidates[0].matched_terms)
    for candidate in candidates[1:]:
        if len(selected) >= max_sentences:
            break
        if candidate.score < best_score * 0.72:
            continue
        if candidate.sentence == selected[0].sentence:
            continue
        # A second sentence must add coverage or come from the same passage.
        adds_coverage = bool(set(candidate.matched_terms) - covered_groups)
        same_chunk = candidate.chunk_id == selected[0].chunk_id
        if adds_coverage or same_chunk:
            selected.append(candidate)
            covered_groups.update(candidate.matched_terms)

    return selected


def build_retrieval_expansion(query_text: str) -> str:
    """Return canonical Telugu variants for retrieval recall.

    This is a query-side expansion only. It does not add facts to the answer and
    does not alter the frozen Phase 2D retrieval benchmark.
    """
    extra: list[str] = []
    for variants in build_content_groups(query_text).values():
        telugu = [v for v in variants if any("\u0c00" <= ch <= "\u0c7f" for ch in v)]
        for term in telugu[:3]:
            if term not in extra:
                extra.append(term)
    return " ".join(extra)


def analyse_query(
    query_text: str,
    expanded_query: str,
    results: list[RetrievalResult],
) -> tuple[QueryAnalysis, list[SentenceCandidate], dict[str, list[str]], QueryIntent]:
    """Produce query analysis, selected sentences, and term groups in one pass."""
    groups = build_content_groups(query_text)
    # Expanded-query text is used by the retriever, not for evidence-coverage
    # scoring. Transliteration noise must not create phantom missing terms.
    intent = detect_intent(query_text)
    max_sentences = 1 if intent in {
        QueryIntent.WHEN,
        QueryIntent.WHERE,
        QueryIntent.WHO,
        QueryIntent.HOW_MANY,
    } else 2
    selected = select_sentences(query_text, results, groups, intent, max_sentences=max_sentences)

    matched_keys: set[str] = set()
    for result in results:
        matched, _ = match_content_groups(groups, f"{result.title} {result.text}")
        matched_keys.update(matched)

    missing = [k for k in groups if k not in matched_keys]
    coverage = len(matched_keys) / max(len(groups), 1) if groups else 0.0

    analysis = QueryAnalysis(
        intent=intent,
        content_terms=[sorted(v)[0] for v in groups.values()],
        matched_terms=[sorted(groups[k])[0] for k in matched_keys if k in groups],
        missing_terms=[sorted(groups[k])[0] for k in missing if k in groups],
        evidence_coverage=round(coverage, 4),
        expanded_query=expanded_query,
    )
    return analysis, selected, groups, intent


def evidence_is_sufficient(
    analysis: QueryAnalysis,
    results: list[RetrievalResult],
    selected: list[SentenceCandidate],
) -> tuple[bool, str]:
    """Apply a conservative evidence gate.

    The gate is a demo/application heuristic, not a calibrated relevance model.
    It prevents answering a France-capital question from a Charminar passage that
    merely shares the word "capital".
    """
    if not results or not selected:
        return False, "No retrieved passage contains query-relevant content."

    total_groups = max(len(analysis.content_terms), 1)
    matched = len(analysis.matched_terms)
    coverage = analysis.evidence_coverage

    strong_title_match = False
    for result in results:
        title_matches = [
            term
            for term in analysis.matched_terms
            if term and term.lower() in result.title.lower()
        ]
        if title_matches:
            strong_title_match = True
            break

    if coverage >= 0.67 and matched >= 2:
        return True, "Retrieved passages cover most informative query terms."
    if coverage >= 0.5 and (strong_title_match or matched >= 2):
        return True, "Retrieved passages cover the query entity and at least one relation term."
    if total_groups == 1 and matched == 1:
        return True, "Single-entity query is attested in retrieved evidence."

    return (
        False,
        "Retrieved passages do not cover enough informative query terms "
        f"({matched}/{total_groups} groups; coverage {coverage:.2f}).",
    )
