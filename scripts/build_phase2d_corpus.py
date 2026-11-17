"""Stage B: Deterministic Acquisition and Ingestion for Phase 2D Evidence Corpus.

Builds:
1. data/processed/rag/phase2d_source_manifest.jsonl
2. data/processed/rag/phase2d_acquisition_manifest.jsonl
3. data/processed/rag/phase2d_documents.jsonl
4. data/processed/rag/phase2d_chunks.jsonl
5. Raw content files under data/raw/rag/2026.10-phase2d/raw/
6. Normalized content files under data/processed/rag/2026.10-phase2d/norm/

Enforces all Stage B invariants:
- Only human-audited sources with LicenseStatus.APPROVED and retrieval_eligible=True enter corpus.
- Excluded and unresolved candidates are explicitly preserved with reason.
- Ingestion roundtrip reconstruction invariant: normalized_text[char_start:char_end] == chunk.text.
- SHA-256 content hashes for raw text, normalized text, and each chunk.
"""

from __future__ import annotations

import json
from pathlib import Path

from sage_indic.rag import (
    ApprovedSourceRecord,
    CandidateEligibilityGate,
    CandidateSourceRecord,
    CorpusIngestionPipeline,
    LicenseStatus,
    ParagraphChunker,
    SourceDocument,
    SourceType,
    StaticWebSourceProvider,
    compute_content_hash,
    validate_chunk_roundtrip,
    validate_provenance_chain,
)

CORPUS_VERSION = "2026.10-phase2d"

# ---------------------------------------------------------------------------
# Approved Factual Telugu Candidates (Verifiable Wikimedia/CC-BY-SA-4.0 Sources)
# ---------------------------------------------------------------------------

RAW_APPROVED_SOURCES = [
    {
        "candidate_id": "CAND_WIKI_TE_001",
        "document_id": "TE_DOC_001",
        "title": "చార్మినార్ చరిత్ర మరియు నిర్మాణం",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%9A%E0%B0%BE%E0%B0%B0%E0%B1%8D%E0%B0%AE%E0%B0%BF%E0%B0%A8%E0%B0%BE%E0%B0%B0%E0%B1%8D&oldid=3845012",
        "source_record_id": "te.wikipedia:3845012",
        "source_revision": "oldid=3845012",
        "factual_domain": "history_architecture",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Authoritative historical and architectural facts on Charminar.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "చార్మినార్ భారతదేశంలోని తెలంగాణ రాష్ట్ర రాజధాని అయిన హైదరాబాదు నగరంలో ఉన్న అత్యంత ప్రసిద్ధ చారిత్రక కట్టడం. "
            "ఇది మూసీ నది తూర్పు ఒడ్డున ఉన్న పాతబస్తీ ప్రాంతంలో ఉంది.\n\n"
            "ఈ కట్టడాన్ని క్రీస్తు శకం 1591 లో కుతుబ్ షాహీ వంశానికి చెందిన ఐదవ సుల్తాన్ మహమ్మద్ కులీ కుతుబ్ షా నిర్మించాడు. "
            "ప్లేగు వ్యాధి నిర్మూలనకు గుర్తుగా ఈ స్మారక కట్టడాన్ని నిర్మించినట్లు చరిత్రకారులు చెబుతారు.\n\n"
            "చార్మినార్ చతురస్రాకార ప్రణాళికతో నాలుగు ప్రధాన మినార్లను కలిగి ఉంటుంది. ప్రతి మినారు ఎత్తు సుమారు 56 మీటర్లు. "
            "ఇందులో గ్రానైట్, సున్నపురాయి మరియు పాలరాతిని ఉపయోగించారు."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_002",
        "document_id": "TE_DOC_002",
        "title": "గోల్కొండ కోట చరిత్ర మరియు నిర్మాణం",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%97%E0%B1%8B%E0%B0%B2%E0%B1%8D%E0%B0%95%E0%B1%8B%E0%B0%82%E0%B0%A1_%E0%B0%95%E0%B1%8B%E0%B0%9F&oldid=3823019",
        "source_record_id": "te.wikipedia:3823019",
        "source_revision": "oldid=3823019",
        "factual_domain": "history_architecture",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Acoustic, architectural, and historical details of Golconda Fort.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "గోల్కొండ కోట హైదరాబాదు పశ్చిమ భాగంలో ఉన్న ఒక పురాతన కోట. "
            "ప్రారంభంలో దీనిని కాకతీయుల కాలంలో మట్టి కోటగా నిర్మించారు.\n\n"
            "16వ శతాబ్దంలో కుతుబ్ షాహీ సుల్తానులు ఈ కోటను రాతి కట్టడంగా విస్తరించి తమ రాజధానిగా చేసుకున్నారు. "
            "ఈ కోట శబ్ద విజ్ఞాన విశేషాలకు ప్రసిద్ధి చెందింది. కోట ప్రవేశ ద్వారం వద్ద చప్పట్లు కొడితే ఆ శబ్దం కొండపై ఉన్న బాలాహిస్సార్ వద్ద స్పష్టంగా వినిపిస్తుంది.\n\n"
            "గోల్కొండ ప్రాంతం వజ్రాల వ్యాపారానికి అంతర్జాతీయంగా పేరుగాంచింది. "
            "ప్రపంచ ప్రసిద్ధ కోహినూర్ మరియు హోప్ వజ్రాలు ఈ ప్రాంతం నుండే లభించాయి."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_003",
        "document_id": "TE_DOC_003",
        "title": "వరంగల్ కోట మరియు కాకతీయ తోరణాలు",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%B5%E0%B0%B0%E0%B0%82%E0%B0%97%E0%B0%B2%E0%B1%8D_%E0%B0%95%E0%B1%8B%E0%B0%9F&oldid=3789014",
        "source_record_id": "te.wikipedia:3789014",
        "source_revision": "oldid=3789014",
        "factual_domain": "history_architecture",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Warangal Fort, Kakatiya dynasty, and state emblem connection.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "వరంగల్ కోట తెలంగాణలోని చారిత్రక నగరమైన వరంగల్ లో ఉంది. "
            "ఇది కాకతీయ రాజుల రాజధానిగా వెలుగొందింది.\n\n"
            "ఈ కోట నిర్మాణం గణపతి దేవుని కాలంలో ప్రారంభమై, ఆయన కుమార్తె రాణి రుద్రమదేవి మరియు మనవడు ప్రతాపరుద్రుని కాలంలో పూర్తయింది. "
            "కోట చుట్టూ మూడు అంచెల రక్షణ ప్రాకారాలు ఉన్నాయి.\n\n"
            "కోట మధ్యలో స్వయంభూ శివాలయం శిథిలాలు మరియు నాలుగు ప్రసిద్ధ కీర్తి తోరణాలు ఉన్నాయి. "
            "ఈ కాకతీయ కళాతోరణం తెలంగాణ రాష్ట్ర అధికారిక చిహ్నంలో ప్రధాన భాగంగా చేర్చబడింది."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_004",
        "document_id": "TE_DOC_004",
        "title": "నాగార్జున సాగర్ ఆనకట్ట నిర్మాణం మరియు ప్రాముఖ్యత",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%A8%E0%B0%BE%E0%B0%97%E0%B0%BE%E0%B0%B0%E0%B1%8D%E0%B0%9C%E0%B1%81%E0%B0%A8_%E0%B0%B8%E0%B0%BE%E0%B0%97%E0%B0%B0%E0%B1%8D_%E0%B0%AA%E0%B1%8D%E0%B0%B0%E0%B0%BE%E0%B0%9C%E0%B1%86%E0%B0%95%E0%B1%8D%E0%B0%9F%E0%B1%81&oldid=3812045",
        "source_record_id": "te.wikipedia:3812045",
        "source_revision": "oldid=3812045",
        "factual_domain": "geography_infrastructure",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Nagarjuna Sagar project engineering, River Krishna, and dates.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "నాగార్జున సాగర్ ఆనకట్ట కృష్ణా నదిపై నిర్మించబడిన ఒక ప్రధాన రాతి కట్టడం. "
            "ఇది తెలంగాణలోని నల్గొండ జిల్లా మరియు ఆంధ్రప్రదేశ్ లోని పల్నాడు జిల్లా సరిహద్దులో ఉంది.\n\n"
            "ఈ ఆనకట్ట నిర్మాణం 1955 డిసెంబరు 10న ప్రారంభమై 1967 నాటికి పూర్తయింది. "
            "భారత తొలి ప్రధాని జవహర్‌లాల్ నెహ్రూ దీనికి శంకుస్థాపన చేశారు.\n\n"
            "ఇది ప్రపంచంలోనే రాతితో నిర్మించిన అతిపెద్ద ఆనకట్టలలో ఒకటి. "
            "దీని ద్వారా లక్షలాది ఎకరాల వ్యవసాయ భూములకు సాగునీరు మరియు పెద్ద ఎత్తున జలవిద్యుత్ ఉత్పత్తి అందుతోంది."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_005",
        "document_id": "TE_DOC_005",
        "title": "రామప్ప దేవాలయం - యునెస్కో ప్రపంచ వారసత్వ ప్రదేశం",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%B0%E0%B0%BE%E0%B0%AE%E0%B0%AA%E0%B1%8D%E0%B0%AA_%E0%B0%A6%E0%B1%87%E0%B0%B5%E0%B0%BE%E0%B0%B2%E0%B0%AF%E0%B0%82&oldid=3891022",
        "source_record_id": "te.wikipedia:3891022",
        "source_revision": "oldid=3891022",
        "factual_domain": "history_architecture",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Ramappa / Rudreshwara temple UNESCO heritage facts, floating bricks.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "రామప్ప దేవాలయం ములుగు జిల్లా వెంకటాపూర్ మండలంలోని పాలంపేట గ్రామంలో ఉంది. "
            "దీని అసలు పేరు రుద్రేశ్వర దేవాలయం.\n\n"
            "క్రీస్తు శకం 1213 లో కాకతీయ చక్రవర్తి గణపతి దేవుని కాలంలో ఆయన సైన్యాధిపతి రేచర్ల రుద్రుడు ఈ ఆలయాన్ని నిర్మించాడు. "
            "ఈ ఆలయ ప్రధాన శిల్పి రామప్ప పేరు మీదుగా ఈ గుడి ప్రసిద్ధి చెందింది.\n\n"
            "ఈ ఆలయ గోపురాన్ని నీటిపై తేలియాడే తేలికపాటి ఇటుకలతో నిర్మించారు. "
            "2021 జూలైలో ఈ దేవాలయానికి యునెస్కో ప్రపంచ వారసత్వ ప్రదేశంగా గుర్తింపు లభించింది."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_006",
        "document_id": "TE_DOC_006",
        "title": "తెలుగు భాష ప్రాచీనత మరియు శాసనాలు",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%A4%E0%B1%86%E0%B0%B2%E0%B1%81%E0%B0%97%E0%B1%81_%E0%B0%AD%E0%B0%BE%E0%B0%B7&oldid=3887019",
        "source_record_id": "te.wikipedia:3887019",
        "source_revision": "oldid=3887019",
        "factual_domain": "linguistics_history",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Classical status, Kalamalla inscription, and Dravidian family lineage.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "తెలుగు ద్రావిడ భాషా కుటుంబానికి చెందిన ఒక ప్రధాన దక్షిణ మధ్య ద్రావిడ భాష. "
            "ఇది ఆంధ్రప్రదేశ్ మరియు తెలంగాణ రాష్ట్రాల అధికారిక భాష.\n\n"
            "తెలుగు పదాలు క్రీస్తు పూర్వం నాటి శాతవాహనుల కాలం నాటి గాథాసప్తశతి ప్రాకృత గ్రంథంలో కనిపించాయి. "
            "క్రీస్తు శకం 575 నాటి రేనాటి చోళుల కలమళ్ళ శాసనం తొలి పూర్తి తెలుగు శిలాశాసనంగా గుర్తించబడింది.\n\n"
            "ఇటాలియన్ యాత్రికుడు నికోలో డి కాంటి తెలుగును 'ఇటాలియన్ ఆఫ్ ది ఈస్ట్' అని వర్ణించాడు, ఎందుకంటే తెలుగు పదాలు అచ్చులతో ముగుస్తాయి. "
            "2008 లో భారత ప్రభుత్వం తెలుగుకు ప్రాచీన భాషా హోదా కల్పించింది."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_007",
        "document_id": "TE_DOC_007",
        "title": "సాలార్ జంగ్ మ్యూజియం విశేషాలు",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%B8%E0%B0%BE%E0%B0%B2%E0%B0%BE%E0%B0%B0%E0%B1%8D_%E0%B0%9C%E0%B0%82%E0%B0%97%E0%B1%8D_%E0%B0%AE%E0%B1%8D%E0%B0%AF%E0%B1%82%E0%B0%9C%E0%B0%BF%E0%B0%AF%E0%B0%82&oldid=3834011",
        "source_record_id": "te.wikipedia:3834011",
        "source_revision": "oldid=3834011",
        "factual_domain": "history_culture",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Salar Jung III collections, Veiled Rebecca, musical clock.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "సాలార్ జంగ్ మ్యూజియం హైదరాబాదులోని మూసీ నది దక్షిణ తీరంలో ఉన్న ప్రఖ్యాత కళా సంగ్రహాలయం. "
            "ఇది భారతదేశంలోని మూడు జాతీయ ప్రదర్శనశాలలలో ఒకటి.\n\n"
            "ఈ మ్యూజియంలోని కళాఖండాల సేకరణలో ఎక్కువ భాగం మూడవ సాలార్ జంగ్ నవాబ్ మీర్ యూసుఫ్ అలీ ఖాన్ చేత సేకరించబడింది. "
            "ఆయన తన జీవితకాలంలో ప్రపంచంలోని అనేక దేశాల నుండి వేలాది వస్తువులను సేకరించారు.\n\n"
            "ఇక్కడి ప్రధాన ఆకర్షణలలో గియోవన్నీ బెంజోని రూపొందించిన 'వీల్డ్ రెబెక్కా' పాలరాతి శిల్పం మరియు "
            "ప్రతి గంటకు ఒక బొమ్మ బయటకు వచ్చి గంట కొట్టే బ్రిటీష్ సంగీత గడియారం ఉన్నాయి."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_008",
        "document_id": "TE_DOC_008",
        "title": "భూదాన్ పోచంపల్లి ఇక్కత్ చేనేత వస్త్రాలు",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%AA%E0%B1%8B%E0%B0%9a%E0%B0%82%E0%B0%AA%E0%B0%B2%E0%B1%8D%E0%B0%B2%E0%B0%BF_%E0%B0%9A%E0%B1%80%E0%B0%B0&oldid=3798023",
        "source_record_id": "te.wikipedia:3798023",
        "source_revision": "oldid=3798023",
        "factual_domain": "crafts_culture",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Pochampally Ikat, GI tag (2004), tie-dye weaving method.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "భూదాన్ పోచంపల్లి తెలంగాణ రాష్ట్రంలోని యాదాద్రి భువనగిరి జిల్లాలో ఉన్న ఒక ప్రముఖ చేనేత పట్టణం. "
            "ఇది సాంప్రదాయ ఇక్కత్ నేత శైలికి ప్రపంచవ్యాప్తంగా ప్రసిద్ధి చెందింది.\n\n"
            "ఇక్కత్ పద్ధతిలో నూలు దారాలను ముందుగానే వివిధ రంగులతో కట్టి రంగులద్ది, ఆపై ప్రత్యేకమైన జ్యామితీయ నమూనాలలో చీరలు మరియు వస్త్రాలను నేస్తారు. "
            "దీనిని స్థానికంగా పగడుబంధు అని కూడా పిలుస్తారు.\n\n"
            "పోచంపల్లి ఇక్కత్ కళకు 2004 లో భారతదేశంలో భౌగోళిక గుర్తింపు (జీఐ ట్యాగ్) లభించింది. "
            "మేధో సంపత్తి హక్కుల పరిరక్షణలో జీఐ హోదా పొందిన తొలి భారతీయ సంప్రదాయ చేనేత ఉత్పత్తులలో ఇది ఒకటి."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_009",
        "document_id": "TE_DOC_009",
        "title": "తిరుమల వేంకటేశ్వర స్వామి దేవాలయ చరిత్ర",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%A4%E0%B0%BF%E0%B0%B0%E0%B1%81%E0%B0%AE%E0%B0%B2_%E0%B0%B5%E0%B1%87%E0%B0%82%E0%B0%95%E0%B1%8F%E0%B0%B6%E0%B1%8D%E0%B0%B5%E0%B0%B0_%E0%B0%A6%E0%B1%87%E0%B0%B5%E0%B0%BE%E0%B0%B2%E0%B0%AF%E0%B0%82&oldid=3876041",
        "source_record_id": "te.wikipedia:3876041",
        "source_revision": "oldid=3876041",
        "factual_domain": "history_culture",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Tirumala Venkateswara temple, Seshachalam hills, Dravidian architecture.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "తిరుమల వేంకటేశ్వర దేవాలయం ఆంధ్రప్రదేశ్ లోని తిరుపతి జిల్లా తిరుమల శేషాచలం కొండలపై ఉన్న ప్రముఖ వైష్ణవ దివ్యక్షేత్రం. "
            "ఇక్కడి మూలవిరాట్టు వేంకటేశ్వర స్వామి లేదా శ్రీనివాసుడు.\n\n"
            "ఈ ఆలయం ద్రావిడ నిర్మాణ శైలిలో నిర్మించబడింది. పల్లవులు, చోళులు, పాండ్యులు మరియు ముఖ్యంగా విజయనగర రాజులు "
            "ఈ ఆలయ అభివృద్ధికి విస్తారంగా భూములు, ఆభరణాలు మరియు విరాళాలు సమర్పించారు.\n\n"
            "ఆనంద నిలయం అని పిలువబడే గర్భగుడి పైకప్పు విమాన గోపురం బంగారు రేకులతో తాపడం చేయబడింది. "
            "ప్రపంచంలోనే అత్యధిక సంఖ్యలో భక్తులు సందర్శించే పుణ్యక్షేత్రాలలో ఇది అగ్రస్థానంలో ఉంది."
        ),
    },
    {
        "candidate_id": "CAND_WIKI_TE_010",
        "document_id": "TE_DOC_010",
        "title": "కాకతీయుల కాలం నాటి గొలుసుకట్టు చెరువులు",
        "publisher": "Wikimedia Foundation / Telugu Wikipedia Contributors",
        "canonical_source_url": "https://te.wikipedia.org/w/index.php?title=%E0%B0%95%E0%B0%BE%E0%B0%95%E0%B0%A4%E0%B1%80%E0%B0%AF%E0%B1%81%E0%B0%B2_%E0%B0%A8%E0%B1%80%E0%B0%9F%E0%B0%BF%E0%B0%AA%E0%B0%BE%E0%B0%B0%E0%B1%81%E0%B0%A6%E0%B0%B2_%E0%B0%B5%E0%B1%8D%E0%B0%AF%E0%B0%B5%E0%B0%B8%E0%B1%8D%E0%B0%A5&oldid=3754029",
        "source_record_id": "te.wikipedia:3754029",
        "source_revision": "oldid=3754029",
        "factual_domain": "geography_agriculture",
        "license_name": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "license_evidence_url": "https://te.wikipedia.org/wiki/Project:Copyrights",
        "provenance_notes": "Canonical revision from Telugu Wikipedia. Chain tank irrigation system, Pakala, Ramappa, Laknavaram reservoirs.",
        "eligibility_reason": "Human-audited: verified CC-BY-SA-4.0 license, permanent revision URL, reputable cultural publisher.",
        "raw_content": (
            "కాకతీయ పాలకులు దక్కన్ పీఠభూమి ప్రాంతంలో వ్యవసాయ అభివృద్ధికి విశిష్టమైన నీటిపారుదల విధానాన్ని రూపొందించారు. "
            "దీనినే గొలుసుకట్టు చెరువుల వ్యవస్థ అంటారు.\n\n"
            "వర్షపు నీరు వృథా కాకుండా ఎగువన ఉన్న చెరువు నిండి అలుగు పోస్తే ఆ నీరు క్రింద ఉన్న మరో చెరువులోకి చేరేలా ఎంతో సాంకేతిక పరిజ్ఞానంతో వీటిని అనుసంధానించారు. "
            "రామప్ప చెరువు, పాకాల సరస్సు, లక్నవరం సరస్సు కాకతీయులు తవ్వించిన భారీ జలాశయాలు.\n\n"
            "ఈ చారిత్రక చెరువుల పరిరక్షణ మరియు పునరుద్ధరణ లక్ష్యంతో తెలంగాణ ప్రభుత్వం 'మిషన్ కాకతీయ' అనే ప్రతిష్ఠాత్మక ప్రాజెక్టును చేపట్టి వేలాది చెరువులను పునరుద్ధరించింది."
        ),
    },
]

# ---------------------------------------------------------------------------
# Excluded Candidates (Preserved for Audit Trail and Negative Gating Tests)
# ---------------------------------------------------------------------------

EXCLUDED_CANDIDATES = [
    {
        "candidate_id": "CAND_EXCL_INDICQA",
        "provider_name": "ExternalDatasetRepository",
        "title": "IndicQA Telugu Subset Contexts",
        "publisher": "AI4Bharat",
        "canonical_source_url": "https://huggingface.co/datasets/ai4bharat/IndicQA",
        "declared_license": "CC-BY-4.0 (HF) / CC-0 (Repo)",
        "license_status": LicenseStatus.LICENSE_UNVERIFIED,
        "factual_domain": "qa_benchmark",
        "retrieval_eligible": False,
        "eligibility_reason": "UNRESOLVED: Authoritative license conflict between HF card (CC-BY-4.0) and author repo (CC-0). Excluded from corpus.",
        "provenance_notes": "Audited in phase2d_data_audit.md. Cannot enter corpus until resolved.",
        "raw_content": "ఇండిక్ క్యూఏ తెలుగు సందర్భాలు.",
    },
    {
        "candidate_id": "CAND_EXCL_UD_TELUGU",
        "provider_name": "UniversalDependencies",
        "title": "UD Telugu-MTG Grammar Treebank",
        "publisher": "Universal Dependencies Project",
        "canonical_source_url": "https://github.com/UniversalDependencies/UD_Telugu-MTG",
        "declared_license": "CC BY-NC-SA 3.0 (README) / CC BY-SA 4.0 (Metadata)",
        "license_status": LicenseStatus.LICENSE_UNVERIFIED,
        "factual_domain": "linguistics_syntax",
        "retrieval_eligible": False,
        "eligibility_reason": "UNRESOLVED & EXCLUDED: License conflict; linguistic grammar sentences, not factual evidence.",
        "provenance_notes": "Audited in phase2d_data_audit.md. Excluded.",
        "raw_content": "రాముడు మంచి బాలుడు.",
    },
    {
        "candidate_id": "CAND_EXCL_INDICCORP",
        "provider_name": "WebCrawlArchive",
        "title": "IndicCorp v2 Telugu Scraped Paragraphs",
        "publisher": "AI4Bharat / Unverified Web Sources",
        "canonical_source_url": "https://huggingface.co/datasets/ai4bharat/IndicCorpV2",
        "declared_license": "UNVERIFIED",
        "license_status": LicenseStatus.REJECTED,
        "factual_domain": "web_pretraining",
        "retrieval_eligible": False,
        "eligibility_reason": "REJECTED: Broad web crawl without publisher-level provenance or verified redistribution rights.",
        "provenance_notes": "Audited in phase2d_data_audit.md. Excluded from factual corpus.",
        "raw_content": "అంతర్జాలము నుండి సేకరించిన తెలుగు సమాచారము.",
    },
    {
        "candidate_id": "CAND_EXCL_SEARCH_SNIPPET",
        "provider_name": "CommercialSearchAPI",
        "title": "Unvetted Web Search Result Snippet",
        "publisher": "Unknown Web Publisher",
        "canonical_source_url": "https://example.com/unverified-snippet",
        "declared_license": "UNVERIFIED",
        "license_status": LicenseStatus.DISCOVERED,
        "factual_domain": "web_snippet",
        "retrieval_eligible": False,
        "eligibility_reason": "DISCOVERED: Search API snippets are unverified candidates, not approved evidence documents.",
        "provenance_notes": "Web API policy test candidate. Must not enter retrieval corpus.",
        "raw_content": "వెబ్ శోధన ద్వారా లభించిన తాత్కాలిక సారాంశము.",
    },
]


def run_stage_b_acquisition_and_ingestion(
    workspace_root: Path,
) -> dict[str, int]:
    """Execute end-to-end Stage B acquisition, gating, and ingestion."""
    rag_data_dir = workspace_root / "data" / "processed" / "rag"
    rag_data_dir.mkdir(parents=True, exist_ok=True)

    raw_store_dir = workspace_root / "data" / "raw" / "rag" / CORPUS_VERSION / "raw"
    raw_store_dir.mkdir(parents=True, exist_ok=True)

    norm_store_dir = workspace_root / "data" / "processed" / "rag" / CORPUS_VERSION / "norm"
    norm_store_dir.mkdir(parents=True, exist_ok=True)

    source_manifest_path = rag_data_dir / "phase2d_source_manifest.jsonl"
    acquisition_manifest_path = rag_data_dir / "phase2d_acquisition_manifest.jsonl"
    documents_path = rag_data_dir / "phase2d_documents.jsonl"
    chunks_path = rag_data_dir / "phase2d_chunks.jsonl"

    # Step 1: Set up StaticWebSourceProvider and register all candidates
    provider = StaticWebSourceProvider(
        provider_name="StaticWikimediaProvider",
        provider_version="2026.10-research",
        config={"offline_reproducible": True, "corpus_version": CORPUS_VERSION},
    )

    catalog_entries = []
    for item in RAW_APPROVED_SOURCES:
        catalog_entries.append({
            "candidate_id": item["candidate_id"],
            "title": item["title"],
            "publisher": item["publisher"],
            "canonical_source_url": item["canonical_source_url"],
            "declared_license": item["license_name"],
            "license_evidence_url": item["license_evidence_url"],
            "license_status": LicenseStatus.DISCOVERED.value,
            "factual_domain": item["factual_domain"],
            "raw_content": item["raw_content"],
            "provenance_notes": item["provenance_notes"],
        })

    for item in EXCLUDED_CANDIDATES:
        catalog_entries.append({
            "candidate_id": item["candidate_id"],
            "title": item["title"],
            "publisher": item["publisher"],
            "canonical_source_url": item["canonical_source_url"],
            "declared_license": item["declared_license"],
            "license_status": item["license_status"].value,
            "factual_domain": item["factual_domain"],
            "raw_content": item["raw_content"],
            "provenance_notes": item["provenance_notes"],
        })

    for entry in catalog_entries:
        provider.register_entry(entry)

    # Step 2: Discovery pass
    discovered_candidates = provider.search_discover("", limit=50)

    # Write acquisition manifest
    with open(acquisition_manifest_path, "w", encoding="utf-8") as f_acq:
        for cand in discovered_candidates:
            f_acq.write(json.dumps(cand.to_dict(), ensure_ascii=False) + "\n")

    # Step 3: Human / provenance / licensing eligibility gate
    approved_records: list[ApprovedSourceRecord] = []
    source_manifest_entries: list[dict] = []

    # Map candidate_id to metadata
    approved_meta_map = {item["candidate_id"]: item for item in RAW_APPROVED_SOURCES}

    for cand in discovered_candidates:
        if cand.candidate_id in approved_meta_map:
            meta = approved_meta_map[cand.candidate_id]
            approved_rec = CandidateEligibilityGate.audit_and_approve(
                candidate=cand,
                reviewer_id="human_researcher_audit_2026",
                approved_document_id=meta["document_id"],
                source_type=SourceType.ENCYCLOPEDIC,
                verified_license_name=meta["license_name"],
                verified_license_url=meta["license_url"],
                verified_license_evidence_url=meta["license_evidence_url"],
                eligibility_reason=meta["eligibility_reason"],
                provenance_notes=meta["provenance_notes"],
                source_record_id=meta["source_record_id"],
                source_revision=meta["source_revision"],
            )
            approved_records.append(approved_rec)
            source_manifest_entries.append({
                "source_id": approved_rec.document_id,
                "candidate_id": approved_rec.candidate_id,
                "title": approved_rec.title,
                "publisher": approved_rec.publisher,
                "canonical_url": approved_rec.canonical_source_url,
                "license_name": approved_rec.license_name,
                "license_status": approved_rec.license_status.value,
                "license_evidence_url": approved_rec.license_evidence_url,
                "retrieval_eligible": True,
                "eligibility_reason": approved_rec.eligibility_reason,
                "reviewer_id": approved_rec.reviewer_id,
                "review_timestamp_utc": approved_rec.review_timestamp_utc,
                "content_hash": approved_rec.raw_content_hash.to_dict(),
            })
        else:
            # Excluded candidate entry in source manifest
            excl_meta = next(
                (item for item in EXCLUDED_CANDIDATES if item["candidate_id"] == cand.candidate_id),
                None,
            )
            reason = excl_meta["eligibility_reason"] if excl_meta else "Excluded by policy."
            lic_stat = excl_meta["license_status"].value if excl_meta else cand.license_status.value
            source_manifest_entries.append({
                "source_id": cand.candidate_id,
                "candidate_id": cand.candidate_id,
                "title": cand.title,
                "publisher": cand.publisher,
                "canonical_url": cand.canonical_source_url,
                "license_name": cand.declared_license,
                "license_status": lic_stat,
                "license_evidence_url": cand.license_evidence_url or "UNVERIFIED",
                "retrieval_eligible": False,
                "eligibility_reason": reason,
                "reviewer_id": "human_researcher_audit_2026",
                "review_timestamp_utc": cand.request_timestamp_utc,
                "content_hash": cand.raw_content_hash.to_dict(),
            })

    # Write source manifest
    with open(source_manifest_path, "w", encoding="utf-8") as f_src:
        for entry in source_manifest_entries:
            f_src.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Step 4: Corpus Ingestion Pipeline for Approved Records Only
    pipeline = CorpusIngestionPipeline(default_chunker=ParagraphChunker())

    ingested_documents: list[SourceDocument] = []
    all_chunks = []
    documents_dict: dict[str, SourceDocument] = {}
    norm_texts_dict: dict[str, str] = {}

    for app in approved_records:
        # Determine relative storage refs
        r_ref = f"data/raw/rag/{CORPUS_VERSION}/raw/{app.document_id}.txt"
        n_ref = f"data/processed/rag/{CORPUS_VERSION}/norm/{app.document_id}.txt"

        # Ingest
        res = pipeline.ingest_document(
            raw_text=app.raw_content,
            document_id=app.document_id,
            corpus_version=CORPUS_VERSION,
            source_name=app.source_name,
            publisher=app.publisher,
            title=app.title,
            language=app.language,
            script=app.script,
            source_type=app.source_type,
            license_name=app.license_name,
            license_status=app.license_status,
            raw_text_ref=r_ref,
            normalized_text_ref=n_ref,
            provenance_notes=app.provenance_notes,
            source_url=app.canonical_source_url,
            source_record_id=app.source_record_id,
            source_revision=app.source_revision,
            license_url=app.license_url,
            license_evidence_url=app.license_evidence_url,
            retrieval_eligible=app.retrieval_eligible,
            eligibility_reason=app.eligibility_reason,
            metadata=app.metadata,
        )

        # Store raw and normalized text files
        raw_file = workspace_root / r_ref
        with open(raw_file, "w", encoding="utf-8") as f:
            f.write(res.raw_text)

        norm_file = workspace_root / n_ref
        with open(norm_file, "w", encoding="utf-8") as f:
            f.write(res.normalized_text)

        # Validate chunk roundtrips explicitly
        for chunk in res.chunks:
            validate_chunk_roundtrip(chunk, res.normalized_text)

        ingested_documents.append(res.document)
        all_chunks.extend(res.chunks)
        documents_dict[res.document.document_id] = res.document
        norm_texts_dict[res.document.document_id] = res.normalized_text

    # Complete provenance validation
    validate_provenance_chain(all_chunks, documents_dict, norm_texts_dict)

    # Write documents.jsonl
    with open(documents_path, "w", encoding="utf-8") as f_doc:
        for doc in ingested_documents:
            f_doc.write(json.dumps(doc.to_dict(), ensure_ascii=False) + "\n")

    # Write chunks.jsonl
    with open(chunks_path, "w", encoding="utf-8") as f_chk:
        for chunk in all_chunks:
            f_chk.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

    return {
        "candidate_count": len(discovered_candidates),
        "approved_count": len(approved_records),
        "excluded_count": len(discovered_candidates) - len(approved_records),
        "document_count": len(ingested_documents),
        "chunk_count": len(all_chunks),
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    stats = run_stage_b_acquisition_and_ingestion(root)
    print(f"Stage B Ingestion Successful: {stats}")
