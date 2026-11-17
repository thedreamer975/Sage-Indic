"""Manually checked demo queries for the SAGE-Indic local application.

These examples are prompts only. The application never displays a stored answer;
each query is executed through the real detection -> retrieval -> verification ->
composition pipeline. ``expected_behavior`` is a manual smoke-test expectation,
not a benchmark label or a performance claim.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DemoExample:
    id: str
    label: str
    query: str
    modality: str
    expected_behavior: str
    note: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


DEMO_EXAMPLES: list[DemoExample] = [
    DemoExample(
        id="native_golconda_location",
        label="Native Telugu · location",
        query="గోల్కొండ కోట ఎక్కడ ఉంది?",
        modality="native",
        expected_behavior="answer",
        note="Golconda Fort location; supported by TE_DOC_002 chunk 0.",
    ),
    DemoExample(
        id="romanized_golconda_location",
        label="Romanized Telugu · location",
        query="Golconda fort ekkada undi?",
        modality="romanized",
        expected_behavior="answer",
        note="Romanized equivalent; exercises transliteration-aware retrieval.",
    ),
    DemoExample(
        id="codemixed_golconda_location",
        label="Code-mixed · location",
        query="Golconda fort location gurinchi cheppu",
        modality="code_mixed",
        expected_behavior="answer",
        note="Telugu-English mixed equivalent; exercises code-mix normalization.",
    ),
    DemoExample(
        id="native_charminar_date",
        label="Native Telugu · date",
        query="చార్మినార్ ఎప్పుడు నిర్మించారు?",
        modality="native",
        expected_behavior="answer",
        note="Charminar construction date (1591 CE) in TE_DOC_001 chunk 1.",
    ),
    DemoExample(
        id="romanized_charminar_date",
        label="Romanized Telugu · date",
        query="Charminar eppudu nirmincharu?",
        modality="romanized",
        expected_behavior="answer",
        note="Romanized date query; uses morphological query expansion.",
    ),
    DemoExample(
        id="codemixed_charminar_date",
        label="Code-mixed · date",
        query="Charminar construction date gurinchi cheppu",
        modality="code_mixed",
        expected_behavior="answer",
        note="Code-mixed date query with English technical terms preserved.",
    ),
    DemoExample(
        id="partial_height_ticket",
        label="Partially answerable",
        query="Charminar height and entry fee enti?",
        modality="code_mixed",
        expected_behavior="partial",
        note="Height is in the corpus; entry fee is not. Expect a partial answer with a caveat.",
    ),
    DemoExample(
        id="unanswerable_france",
        label="Unanswerable",
        query="ఫ్రాన్స్ రాజధాని ఏది?",
        modality="native",
        expected_behavior="abstain",
        note="France is absent from the corpus. Expect an honest abstention, not an answer.",
    ),
    DemoExample(
        id="unanswerable_france_en",
        label="Unanswerable (English)",
        query="What is the capital of France?",
        modality="english",
        expected_behavior="abstain",
        note="No English/France documents exist in the corpus.",
    ),
]


def get_examples() -> list[dict[str, str]]:
    return [example.to_dict() for example in DEMO_EXAMPLES]
