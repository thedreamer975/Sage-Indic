"""Build and validate the Phase 2D Multi-Script Retrieval Benchmark.

Generates:
- Development set (dev): 6 query families (18 queries: 6 native, 6 romanized, 6 code-mixed)
  - 4 answerable families, 2 unanswerable families
- Held-out evaluation set (eval): 8 query families (24 queries: 8 native, 8 romanized, 8 code-mixed)
  - 6 answerable families, 2 unanswerable families
- Full relevance judgments (qrels) for both dev and eval splits with graded relevance (0, 1, 2).

All records are validated using validate_evaluation_query and validate_relevance_judgment.
"""

from __future__ import annotations

import json
from pathlib import Path

from sage_indic.rag.types import (
    AnnotationStatus,
    EvaluationQuery,
    QueryModality,
    RelevanceGrade,
    RelevanceJudgment,
)
from sage_indic.rag.validation import (
    validate_evaluation_query,
    validate_relevance_judgment,
)

# ---------------------------------------------------------------------------
# Benchmark Query Definitions
# ---------------------------------------------------------------------------

DEV_FAMILIES = [
    {
        "family_id": "QF_DEV_001",
        "doc_id": "TE_DOC_001",
        "primary_chunk_id": "TE_DOC_001#c0001",
        "supporting_chunk_ids": ["TE_DOC_001#c0000", "TE_DOC_001#c0002"],
        "topic": "Charminar construction year and ruler",
        "queries": [
            ("Q_DEV_001_NAT", "చార్మినార్‌ను ఏ సంవత్సరంలో మరియు ఎవరు నిర్మించారు?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_001"),
            ("Q_DEV_001_ROM", "charminar nu ye samvatsaram lo mariyu evaru nirmincharu?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_DEV_001_NAT"),
            ("Q_DEV_001_MIX", "Charminar construction ye year lo evari dwara jarigindi?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_DEV_001_NAT"),
        ],
    },
    {
        "family_id": "QF_DEV_002",
        "doc_id": "TE_DOC_004",
        "primary_chunk_id": "TE_DOC_004#c0001",
        "supporting_chunk_ids": ["TE_DOC_004#c0000", "TE_DOC_004#c0002"],
        "topic": "Nagarjuna Sagar dam foundation stone by Nehru",
        "queries": [
            ("Q_DEV_002_NAT", "నాగార్జున సాగర్ ఆనకట్టకు శంకుస్థాపన చేసిన భారత ప్రధాని ఎవరు?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_004"),
            ("Q_DEV_002_ROM", "nagarjuna sagar aanakattaku shankhusthapana chesina bharata pradhani evaru?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_DEV_002_NAT"),
            ("Q_DEV_002_MIX", "Nagarjuna Sagar dam ki foundation stone vesina Prime Minister evaru?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_DEV_002_NAT"),
        ],
    },
    {
        "family_id": "QF_DEV_003",
        "doc_id": "TE_DOC_007",
        "primary_chunk_id": "TE_DOC_007#c0002",
        "supporting_chunk_ids": ["TE_DOC_007#c0000", "TE_DOC_007#c0001"],
        "topic": "Salar Jung Museum Veiled Rebecca sculpture",
        "queries": [
            ("Q_DEV_003_NAT", "సాలార్ జంగ్ మ్యూజియంలోని వీల్డ్ రెబెక్కా శిల్పాన్ని ఎవరు రూపొందించారు?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_007"),
            ("Q_DEV_003_ROM", "salar jung museum loni veiled rebecca shilpanni evaru roopondincharu?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_DEV_003_NAT"),
            ("Q_DEV_003_MIX", "Salar Jung Museum lo unna Veiled Rebecca sculpture ni evaru design chesaru?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_DEV_003_NAT"),
        ],
    },
    {
        "family_id": "QF_DEV_004",
        "doc_id": "TE_DOC_010",
        "primary_chunk_id": "TE_DOC_010#c0002",
        "supporting_chunk_ids": ["TE_DOC_010#c0000", "TE_DOC_010#c0001"],
        "topic": "Mission Kakatiya tank restoration project",
        "queries": [
            ("Q_DEV_004_NAT", "తెలంగాణ ప్రభుత్వం చెరువుల పునరుద్ధరణ కోసం చేపట్టిన ప్రాజెక్టు ఏది?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_010"),
            ("Q_DEV_004_ROM", "telangana prabhutvam cheruvula punaruddharana kosam chepattina project edi?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_DEV_004_NAT"),
            ("Q_DEV_004_MIX", "Telangana government historical tanks restore cheyadaniki start chesina project enti?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_DEV_004_NAT"),
        ],
    },
    # Unanswerable queries (genuinely absent from corpus)
    {
        "family_id": "QF_DEV_005",
        "doc_id": None,
        "primary_chunk_id": None,
        "supporting_chunk_ids": [],
        "topic": "Hyderabadi Biryani origin history (Unanswerable)",
        "queries": [
            ("Q_DEV_005_NAT", "హైదరాబాదీ దమ్ బిర్యానీని మొఘలుల కాలంలో ఎలా తయారుచేసేవారు?", QueryModality.NATIVE, "Native Telugu unanswerable query on culinary history"),
            ("Q_DEV_005_ROM", "hyderabadi dum biryani ni moghalula kalam lo ela tayaruchesevaru?", QueryModality.ROMANIZED, "Phonetic Romanized unanswerable query"),
            ("Q_DEV_005_MIX", "Hyderabadi Dum Biryani authentic recipe and origin history enti?", QueryModality.CODE_MIXED, "Telugu-English code-mixed unanswerable query"),
        ],
    },
    {
        "family_id": "QF_DEV_006",
        "doc_id": None,
        "primary_chunk_id": None,
        "supporting_chunk_ids": [],
        "topic": "Amaravati Buddhist Stupa architecture (Unanswerable)",
        "queries": [
            ("Q_DEV_006_NAT", "అమరావతి బౌద్ధ స్తూపంలోని పాలరాతి శిల్పాల ప్రత్యేకత ఏమిటి?", QueryModality.NATIVE, "Native Telugu unanswerable query on Buddhist stupa art"),
            ("Q_DEV_006_ROM", "amaravati bouddha stupam loni palarathi shilpala prathyekatha emiti?", QueryModality.ROMANIZED, "Phonetic Romanized unanswerable query"),
            ("Q_DEV_006_MIX", "Amaravati Buddhist Stupa lo unna marble carvings structure ela untundi?", QueryModality.CODE_MIXED, "Telugu-English code-mixed unanswerable query"),
        ],
    },
]

EVAL_FAMILIES = [
    {
        "family_id": "QF_EVAL_001",
        "doc_id": "TE_DOC_002",
        "primary_chunk_id": "TE_DOC_002#c0001",
        "supporting_chunk_ids": ["TE_DOC_002#c0000", "TE_DOC_002#c0002"],
        "topic": "Golconda Fort acoustics clapping at entrance",
        "queries": [
            ("Q_EVAL_001_NAT", "గోల్కొండ కోట ప్రవేశ ద్వారం వద్ద చప్పట్లు కొడితే శబ్దం ఎక్కడికి వినిపిస్తుంది?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_002"),
            ("Q_EVAL_001_ROM", "golconda kota pravesha dwaram vadda chappatlu kodithe shabdam ekkadiki vinipistundi?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_EVAL_001_NAT"),
            ("Q_EVAL_001_MIX", "Golconda fort entrance daggara clap chesthe sound ekkadiki reach avtundi?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_EVAL_001_NAT"),
        ],
    },
    {
        "family_id": "QF_EVAL_002",
        "doc_id": "TE_DOC_003",
        "primary_chunk_id": "TE_DOC_003#c0002",
        "supporting_chunk_ids": ["TE_DOC_003#c0000", "TE_DOC_003#c0001"],
        "topic": "Kakatiya Toranam in Telangana official emblem",
        "queries": [
            ("Q_EVAL_002_NAT", "తెలంగాణ రాష్ట్ర అధికారిక చిహ్నంలో చేర్చబడిన కాకతీయ కట్టడం ఏది?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_003"),
            ("Q_EVAL_002_ROM", "telangana rashtra adhikarika chihnam lo cherchabadina kakatiya kattadam edi?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_EVAL_002_NAT"),
            ("Q_EVAL_002_MIX", "Telangana state official emblem lo include chesina Kakatiya monument edi?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_EVAL_002_NAT"),
        ],
    },
    {
        "family_id": "QF_EVAL_003",
        "doc_id": "TE_DOC_005",
        "primary_chunk_id": "TE_DOC_005#c0002",
        "supporting_chunk_ids": ["TE_DOC_005#c0000", "TE_DOC_005#c0001"],
        "topic": "Ramappa Temple UNESCO World Heritage recognition",
        "queries": [
            ("Q_EVAL_003_NAT", "రామప్ప దేవాలయానికి ఏ సంవత్సరంలో యునెస్కో ప్రపంచ వారసత్వ హోదా లభించింది?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_005"),
            ("Q_EVAL_003_ROM", "ramappa devalayaniki ye samvatsaram lo unesco prapancha varasathva hoda labhinchindi?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_EVAL_003_NAT"),
            ("Q_EVAL_003_MIX", "Ramappa temple ki UNESCO World Heritage site tag ye year lo vachindi?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_EVAL_003_NAT"),
        ],
    },
    {
        "family_id": "QF_EVAL_004",
        "doc_id": "TE_DOC_006",
        "primary_chunk_id": "TE_DOC_006#c0001",
        "supporting_chunk_ids": ["TE_DOC_006#c0000", "TE_DOC_006#c0002"],
        "topic": "Kalamalla inscription antiquity of Telugu",
        "queries": [
            ("Q_EVAL_004_NAT", "తొలి పూర్తి తెలుగు శిలాశాసనంగా గుర్తించబడిన కలమళ్ళ శాసనం ఏ కాలం నాటిది?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_006"),
            ("Q_EVAL_004_ROM", "tholi poorthi telugu shilashasanamga gurtinchabadina kalamalla shasanam ye kalam natidi?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_EVAL_004_NAT"),
            ("Q_EVAL_004_MIX", "First full Telugu stone inscription Kalamalla shasanam ye period ki chendindi?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_EVAL_004_NAT"),
        ],
    },
    {
        "family_id": "QF_EVAL_005",
        "doc_id": "TE_DOC_008",
        "primary_chunk_id": "TE_DOC_008#c0002",
        "supporting_chunk_ids": ["TE_DOC_008#c0000", "TE_DOC_008#c0001"],
        "topic": "Pochampally Ikat GI tag 2004",
        "queries": [
            ("Q_EVAL_005_NAT", "భూదాన్ పోచంపల్లి ఇక్కత్ చేనేత వస్త్రాలకు భౌగోళిక గుర్తింపు (జీఐ ట్యాగ్) ఎప్పుడు లభించింది?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_008"),
            ("Q_EVAL_005_ROM", "bhoodan pochampalli ikkat chenetha vastralaku bhaugolika gurtimpu gi tag eppudu labhinchindi?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_EVAL_005_NAT"),
            ("Q_EVAL_005_MIX", "Pochampally Ikat handloom fabrics ki GI tag eppudu announce chesaru?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_EVAL_005_NAT"),
        ],
    },
    {
        "family_id": "QF_EVAL_006",
        "doc_id": "TE_DOC_009",
        "primary_chunk_id": "TE_DOC_009#c0002",
        "supporting_chunk_ids": ["TE_DOC_009#c0000", "TE_DOC_009#c0001"],
        "topic": "Tirumala temple Ananda Nilayam golden gopuram",
        "queries": [
            ("Q_EVAL_006_NAT", "తిరుమల ఆలయ గర్భగుడిపై ఉన్న బంగారు విమాన గోపురాన్ని ఏమని పిలుస్తారు?", QueryModality.NATIVE, "Native Telugu query authored against TE_DOC_009"),
            ("Q_EVAL_006_ROM", "tirumala aalaya garbhagudipai unna bangaru vimana gopuranni emani pilustharu?", QueryModality.ROMANIZED, "Phonetic Romanized transliteration of Q_EVAL_006_NAT"),
            ("Q_EVAL_006_MIX", "Tirumala temple sanctum sanctorum gold tower ni em ani call chestaru?", QueryModality.CODE_MIXED, "Telugu-English colloquial code-mixed query of Q_EVAL_006_NAT"),
        ],
    },
    # Unanswerable queries (genuinely absent from corpus)
    {
        "family_id": "QF_EVAL_007",
        "doc_id": None,
        "primary_chunk_id": None,
        "supporting_chunk_ids": [],
        "topic": "Kuchipudi classical dance origin village (Unanswerable)",
        "queries": [
            ("Q_EVAL_007_NAT", "కూచిపూడి నృత్యం ఆంధ్రప్రదేశ్ లోని ఏ గ్రామంలో పుట్టింది?", QueryModality.NATIVE, "Native Telugu unanswerable query on classical dance"),
            ("Q_EVAL_007_ROM", "kuchipudi nruthyam andhra pradesh loni ye gramam lo puttindi?", QueryModality.ROMANIZED, "Phonetic Romanized unanswerable query"),
            ("Q_EVAL_007_MIX", "Kuchipudi classical dance form Andhra Pradesh lo ekkada originate aindi?", QueryModality.CODE_MIXED, "Telugu-English code-mixed unanswerable query"),
        ],
    },
    {
        "family_id": "QF_EVAL_008",
        "doc_id": None,
        "primary_chunk_id": None,
        "supporting_chunk_ids": [],
        "topic": "Kaleshwaram Lift Irrigation barrages count (Unanswerable)",
        "queries": [
            ("Q_EVAL_008_NAT", "కాళేశ్వరం ఎత్తిపోతల పథకంలో ఎన్ని బ్యారేజీలు నిర్మించారు?", QueryModality.NATIVE, "Native Telugu unanswerable query on modern irrigation"),
            ("Q_EVAL_008_ROM", "kaleshwaram etthipothala pathakam lo enni barrage lu nirmincharu?", QueryModality.ROMANIZED, "Phonetic Romanized unanswerable query"),
            ("Q_EVAL_008_MIX", "Kaleshwaram Lift Irrigation project lo total enni barrages construct chesaru?", QueryModality.CODE_MIXED, "Telugu-English code-mixed unanswerable query"),
        ],
    },
]


def generate_queries_and_qrels(
    families: list[dict],
    split_name: str,
    chunks: list[dict],
) -> tuple[list[EvaluationQuery], list[RelevanceJudgment]]:
    """Build and validate queries and exhaustive qrels for a split."""
    query_objs: list[EvaluationQuery] = []
    qrel_objs: list[RelevanceJudgment] = []

    for fam in families:
        fam_id = fam["family_id"]
        doc_id = fam["doc_id"]
        primary_chunk = fam["primary_chunk_id"]
        supporting_chunks = set(fam["supporting_chunk_ids"])
        is_answerable = doc_id is not None

        # Build variants map
        variant_map = {q[0]: q[1] for q in fam["queries"]}

        for q_id, q_text, modality, prov in fam["queries"]:
            rel_docs = [doc_id] if is_answerable else []
            rel_chunks = [primary_chunk] + list(supporting_chunks) if is_answerable else []

            query = EvaluationQuery(
                query_id=q_id,
                query_text=q_text,
                language="te",
                modality=modality,
                query_family_id=fam_id,
                query_provenance=f"{prov} (split={split_name})",
                variants=variant_map,
                relevant_document_ids=rel_docs,
                relevant_chunk_ids=rel_chunks,
                annotation_status=AnnotationStatus.PENDING,
                annotator_notes=(
                    f"Target document: {doc_id}, Primary chunk: {primary_chunk}. "
                    f"Answerable: {is_answerable}."
                ),
            )
            validate_evaluation_query(query)
            query_objs.append(query)

            # Generate exhaustive judgments against all 30 chunks
            for c in chunks:
                cid = c["chunk_id"]
                cdoc = c["document_id"]
                ctext = c["text"]

                if not is_answerable:
                    grade = RelevanceGrade.NOT_RELEVANT
                    comments = "Unanswerable query: no factual grounding in approved corpus."
                elif cid == primary_chunk:
                    grade = RelevanceGrade.FULLY_RELEVANT
                    comments = "Primary evidence chunk: directly contains the factual answer."
                elif cid in supporting_chunks:
                    grade = RelevanceGrade.PARTIALLY_RELEVANT
                    comments = "Supporting evidence chunk: provides same-document background context."
                else:
                    grade = RelevanceGrade.NOT_RELEVANT
                    comments = "Irrelevant chunk from distinct parent document."

                qrel = RelevanceJudgment(
                    query_id=q_id,
                    document_id=cdoc,
                    chunk_id=cid,
                    snippet=ctext[:100],
                    language="te",
                    script="Telugu",
                    annotator_scores=[grade.value],
                    adjudicated_score=grade,
                    annotation_status=AnnotationStatus.PENDING,
                    comments=comments,
                    provenance_notes=f"Derived benchmark judgment for {q_id} against {cid}",
                )
                validate_relevance_judgment(qrel)
                qrel_objs.append(qrel)

    return query_objs, qrel_objs


def main() -> None:
    rag_dir = Path("data/processed/rag")
    chunks_path = rag_dir / "phase2d_chunks.jsonl"
    if not chunks_path.exists():
        raise FileNotFoundError(f"Corpus chunks not found at {chunks_path}")

    chunks = [json.loads(line) for line in open(chunks_path, encoding="utf-8")]
    print(f"Loaded {len(chunks)} approved corpus chunks.")

    # Generate dev benchmark
    dev_queries, dev_qrels = generate_queries_and_qrels(DEV_FAMILIES, "dev", chunks)
    print(f"Generated {len(dev_queries)} dev queries and {len(dev_qrels)} dev qrels.")

    # Generate eval benchmark
    eval_queries, eval_qrels = generate_queries_and_qrels(EVAL_FAMILIES, "eval", chunks)
    print(f"Generated {len(eval_queries)} eval queries and {len(eval_qrels)} eval qrels.")

    # Save to disk
    dev_q_path = rag_dir / "phase2d_eval_queries_dev.jsonl"
    dev_rel_path = rag_dir / "phase2d_qrels_dev.jsonl"
    eval_q_path = rag_dir / "phase2d_eval_queries_eval.jsonl"
    eval_rel_path = rag_dir / "phase2d_qrels_eval.jsonl"

    with open(dev_q_path, "w", encoding="utf-8") as f:
        for q in dev_queries:
            f.write(json.dumps(q.to_dict(), ensure_ascii=False) + "\n")

    with open(dev_rel_path, "w", encoding="utf-8") as f:
        for r in dev_qrels:
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    with open(eval_q_path, "w", encoding="utf-8") as f:
        for q in eval_queries:
            f.write(json.dumps(q.to_dict(), ensure_ascii=False) + "\n")

    with open(eval_rel_path, "w", encoding="utf-8") as f:
        for r in eval_qrels:
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    print(f"Successfully saved dev benchmark to {dev_q_path} and {dev_rel_path}")
    print(f"Successfully saved eval benchmark to {eval_q_path} and {eval_rel_path}")


if __name__ == "__main__":
    main()
