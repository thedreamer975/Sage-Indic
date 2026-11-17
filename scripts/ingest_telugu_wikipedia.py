"""Medium-scale Telugu Wikipedia corpus ingestion for SAGE-Indic.

Fetches ~500 curated Telugu Wikipedia articles via the MediaWiki API,
processes them through the existing CorpusIngestionPipeline, and outputs
phase2d_documents.jsonl and phase2d_chunks.jsonl.

All articles are CC-BY-SA-4.0 licensed via Wikimedia Foundation.
Permanent revision IDs are stored for reproducibility.

Usage:
    python scripts/ingest_telugu_wikipedia.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Curated article titles organized by domain
# ---------------------------------------------------------------------------

ARTICLE_TITLES: dict[str, list[str]] = {
    "history_dynasties": [
        "శ్రీకృష్ణదేవరాయలు",
        "విజయనగర సామ్రాజ్యము",
        "కాకతీయులు",
        "శాతవాహనులు",
        "కుతుబ్ షాహీ వంశము",
        "గజపతి రాజవంశం",
        "రెడ్డి రాజ్యము",
        "ముసునూరి నాయకులు",
        "ఆంధ్ర ఇక్ష్వాకులు",
        "పల్లవులు",
        "చాళుక్యులు",
        "రాష్ట్రకూటులు",
        "తెలంగాణ చరిత్ర",
        "ఆంధ్రప్రదేశ్ చరిత్ర",
        "హైదరాబాదు చరిత్ర",
        "నిజాం",
        "అసఫ్ జాహీ వంశం",
        "మహాత్మా గాంధీ",
        "జవహర్‌లాల్ నెహ్రూ",
        "సుభాష్ చంద్ర బోస్",
        "భారత స్వాతంత్ర్యోద్యమం",
        "హైదరాబాదు రాజ్యం",
        "భారత విభజన",
        "మొఘల్ సామ్రాజ్యం",
        "మౌర్య సామ్రాజ్యం",
        "గుప్త సామ్రాజ్యం",
        "చోళ సామ్రాజ్యం",
        "పాండ్య రాజ్యం",
        "సింధు నాగరికత",
        "అశోకుడు",
        "చాణక్యుడు",
        "టిప్పు సుల్తాన్",
        "రాణి లక్ష్మీబాయి",
        "శివాజీ",
        "అక్బర్",
        "షేర్ షా సూరి",
        "బాబర్",
        "పృథ్వీరాజ్ చౌహాన్",
        "రామాయణం",
        "మహాభారతం",
        "కురుక్షేత్ర యుద్ధం",
        "పానిపట్ యుద్ధం",
        "తరైన్ యుద్ధం",
        "ప్లాసీ యుద్ధం",
        "కళింగ యుద్ధం",
    ],
    "culture_arts_literature": [
        "అన్నమయ్య",
        "త్యాగరాజు",
        "రామదాసు",
        "పోతన",
        "నన్నయ్య",
        "తిక్కన",
        "ఎఱ్ఱన",
        "శ్రీనాథుడు",
        "వేమన",
        "గురజాడ అప్పారావు",
        "కందుకూరి వీరేశలింగం",
        "విశ్వనాథ సత్యనారాయణ",
        "శ్రీశ్రీ",
        "జాషువా",
        "సి.నారాయణ రెడ్డి",
        "దాశరథి కృష్ణమాచార్య",
        "కూచిపూడి",
        "భరతనాట్యం",
        "కర్ణాటక సంగీతం",
        "తెలుగు సినిమా",
        "సంక్రాంతి",
        "ఉగాది",
        "దసరా",
        "దీపావళి",
        "బతుకమ్మ",
        "బోనాలు",
        "తెలుగు భాష",
        "తెలుగు లిపి",
        "తెలుగు వ్యాకరణం",
        "ఆంధ్ర మహాభారతము",
        "అముక్తమాల్యద",
        "మనుచరిత్ర",
        "పండితారాధ్య చరిత్ర",
        "శతకం",
        "ద్విపద",
        "పదకవితా పితామహుడు",
        "తెలుగు నాటకం",
        "ఎన్.టి.రామారావు",
        "అక్కినేని నాగేశ్వరరావు",
        "ఘంటసాల వెంకటేశ్వరరావు",
        "సావిత్రి",
        "బాలు",
        "ఇళయరాజా",
        "ఏ.ఆర్.రహమాన్",
        "చిరంజీవి",
    ],
    "geography_heritage": [
        "తిరుమల వేంకటేశ్వర దేవాలయం",
        "అమరావతి",
        "నాగార్జునకొండ",
        "భద్రాచలం",
        "లేపాక్షి",
        "శ్రీశైలం",
        "యాదగిరిగుట్ట",
        "అహోబిలం",
        "సింహాచలం",
        "అన్నవరం",
        "విశాఖపట్నం",
        "విజయవాడ",
        "గుంటూరు",
        "కర్నూలు",
        "నెల్లూరు",
        "కాకినాడ",
        "రాజమహేంద్రవరం",
        "తిరుపతి",
        "కడప",
        "ఆదిలాబాద్",
        "వరంగల్",
        "నిజామాబాద్",
        "కరీంనగర్",
        "మహబూబ్‌నగర్",
        "నాగార్జున సాగర్",
        "శ్రీసైలం ఆనకట్ట",
        "గోదావరి నది",
        "కృష్ణా నది",
        "పెన్నా నది",
        "తుంగభద్ర నది",
        "మంజీరా నది",
        "కొల్లేరు సరస్సు",
        "పులికాట్ సరస్సు",
        "హుస్సేన్ సాగర్",
        "హిమాలయ పర్వతాలు",
        "తూర్పు కనుమలు",
        "నల్లమల కొండలు",
        "అరకు లోయ",
        "ఏలూరు",
        "అనంతపురము",
        "శ్రీకాకుళం",
        "ప్రకాశం జిల్లా",
        "పశ్చిమ గోదావరి జిల్లా",
        "తెలంగాణ",
        "ఆంధ్రప్రదేశ్",
    ],
    "science_health_medicine": [
        "ఆయుర్వేదం",
        "యోగా",
        "పాము కాటు",
        "మలేరియా",
        "డెంగ్యూ జ్వరం",
        "కరోనావైరస్",
        "క్షయ",
        "మధుమేహం",
        "గుండె జబ్బులు",
        "రక్తపోటు",
        "కంటి వ్యాధులు",
        "టీకా",
        "ఔషధ మొక్కలు",
        "పసుపు",
        "వేప",
        "తులసి",
        "ఉసిరి",
        "భౌతిక శాస్త్రం",
        "రసాయన శాస్త్రం",
        "జీవ శాస్త్రం",
        "గణిత శాస్త్రం",
        "ఖగోళ శాస్త్రం",
        "సూర్యుడు",
        "చంద్రుడు",
        "భూమి",
        "అంగారకుడు",
        "గురుత్వాకర్షణ",
        "పరమాణువు",
        "విద్యుత్తు",
        "ఎలక్ట్రానిక్స్",
        "కంప్యూటర్",
        "ఇంటర్నెట్",
        "కృత్రిమ మేధస్సు",
        "రోబోటిక్స్",
        "నానో టెక్నాలజీ",
        "జన్యు శాస్త్రం",
        "కణం",
        "డి.ఎన్.ఎ.",
        "ప్రోటీన్",
        "విటమిన్లు",
        "ప్రాథమిక చికిత్స",
        "ఆసుపత్రి",
        "వైద్యం",
        "సర్జరీ",
        "మానసిక ఆరోగ్యం",
    ],
    "biographies_modern": [
        "సర్వేపల్లి రాధాకృష్ణన్",
        "ఏ.పి.జె.అబ్దుల్ కలాం",
        "సి.వి.రామన్",
        "సత్యేంద్రనాథ్ బోస్",
        "హోమి జహంగీర్ భాభా",
        "విక్రమ్ సారాభాయ్",
        "రామానుజన్",
        "ఆర్యభట్ట",
        "జగదీశ్ చంద్ర బోస్",
        "పొట్టి శ్రీరాములు",
        "అల్లూరి సీతారామరాజు",
        "కొమరం భీమ్",
        "తెలంగాణ సాయుధ పోరాటం",
        "భారత రాజ్యాంగం",
        "భారత ఎన్నికలు",
        "భారత రిజర్వు బ్యాంకు",
        "ఇస్రో",
        "భారత రైల్వే",
        "భారత సైన్యం",
        "భారత వాయుసేన",
        "భారత నౌకాదళం",
        "క్రికెట్",
        "సచిన్ టెండూల్కర్",
        "ఒలింపిక్ క్రీడలు",
        "భారత క్రీడలు",
        "కబడ్డీ",
        "హాకీ",
        "బ్యాడ్మింటన్",
        "సైనా నెహ్వాల్",
        "పి.వి.సింధు",
        "భారతదేశ ఆర్థిక వ్యవస్థ",
        "భారతదేశ జనాభా",
        "సమాచార హక్కు చట్టం",
        "పంచాయతీ రాజ్",
        "భారతదేశంలో విద్య",
        "భారత సాంకేతిక సంస్థలు",
        "ఐ.ఐ.టి.",
        "అంతరిక్ష పరిశోధన",
        "చంద్రయాన్",
        "మంగళయాన్",
    ],
    "agriculture_nature": [
        "వ్యవసాయం",
        "వరి",
        "గోధుమ",
        "మొక్కజొన్న",
        "పత్తి",
        "చెరకు",
        "పొగాకు",
        "మిరప",
        "పసుపు",
        "ఆవు",
        "గేదె",
        "మేక",
        "కోడి",
        "మామిడి",
        "అరటి",
        "కొబ్బరి చెట్టు",
        "వేప చెట్టు",
        "మర్రి చెట్టు",
        "రావి చెట్టు",
        "పులి",
        "ఏనుగు",
        "నెమలి",
        "హంస",
        "కోకిల",
        "కాకి",
        "సింహం",
        "జింక",
        "ఎలుగుబంటి",
        "మొసలి",
        "పాము",
        "తాబేలు",
        "బాతు",
        "పావురం",
        "గ్రహాలు",
        "నక్షత్రాలు",
    ],
}

# Total target: flatten all titles
ALL_TITLES = []
for domain_titles in ARTICLE_TITLES.values():
    ALL_TITLES.extend(domain_titles)

CORPUS_VERSION = "2026.11-phase2g"
USER_AGENT = "SAGE-Indic/1.0 (research; Telugu NLP project; contact: sageindic@research.org)"
API_BASE = "https://te.wikipedia.org/w/api.php"
PUBLISHER = "Wikimedia Foundation / Telugu Wikipedia Contributors"
LICENSE_NAME = "CC-BY-SA-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
LICENSE_EVIDENCE_URL = "https://te.wikipedia.org/wiki/Project:Copyrights"
MIN_ARTICLE_CHARS = 200


def fetch_wikipedia_article(title: str) -> dict | None:
    """Fetch an individual article from Telugu Wikipedia API."""
    params = {
        "action": "query",
        "prop": "extracts|revisions",
        "explaintext": "1",
        "exsectionformat": "plain",
        "redirects": "1",
        "titles": title,
        "rvprop": "ids|timestamp",
        "format": "json",
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    data = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except Exception:
            time.sleep(0.5 * (attempt + 1))

    if not data:
        return None

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return None
    page = next(iter(pages.values()))
    pageid_val = page.get("pageid", -1)
    if pageid_val == -1 or "missing" in page:
        return None

    extract = page.get("extract", "")
    # Fallback to exintro if full extract is empty
    if len(extract.strip()) < MIN_ARTICLE_CHARS:
        params["exintro"] = "1"
        url_intro = f"{API_BASE}?{urllib.parse.urlencode(params)}"
        req_intro = urllib.request.Request(url_intro, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req_intro, timeout=10) as resp:
                data_intro = json.loads(resp.read().decode("utf-8"))
            page_intro = next(iter(data_intro.get("query", {}).get("pages", {}).values()))
            extract = page_intro.get("extract", "")
        except Exception:
            pass

    if len(extract.strip()) < MIN_ARTICLE_CHARS:
        return None

    revisions = page.get("revisions", [{}])
    rev = revisions[0] if revisions else {}
    return {
        "title": page.get("title", title),
        "pageid": int(pageid_val),
        "revid": rev.get("revid", 0),
        "timestamp": rev.get("timestamp", ""),
        "extract": extract,
    }


def fetch_all_articles(titles: list[str]) -> list[dict]:
    """Fetch articles from Telugu Wikipedia API individually."""
    results = []
    total = len(titles)
    for i, t in enumerate(titles, 1):
        res = fetch_wikipedia_article(t)
        if res:
            results.append(res)
            print(f"  [{i}/{total}] OK: {res['title']} ({len(res['extract'])} chars)")
        else:
            print(f"  [{i}/{total}] SKIP/MISSING: {t}")
        # Polite rate limit
        time.sleep(0.15)
    return results


def clean_wikipedia_text(text: str) -> str:
    """Clean Wikipedia extract text: remove navigation artifacts, normalize whitespace."""
    # Remove common Wikipedia artifacts
    text = re.sub(r"=+\s*[^=]+\s*=+", "\n", text)  # Remove section headings
    text = re.sub(r"\[\d+\]", "", text)  # Remove citation references
    text = re.sub(r"\{[^}]*\}", "", text)  # Remove template artifacts
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "src"))

    from sage_indic.rag.chunking import ParagraphChunker
    from sage_indic.rag.ingestion import CorpusIngestionPipeline
    from sage_indic.rag.types import LicenseStatus, SourceType
    from sage_indic.rag.validation import validate_chunk_roundtrip, validate_provenance_chain

    rag_dir = root / "data" / "processed" / "rag"
    rag_dir.mkdir(parents=True, exist_ok=True)

    raw_store_dir = root / "data" / "raw" / "rag" / CORPUS_VERSION / "raw"
    raw_store_dir.mkdir(parents=True, exist_ok=True)
    norm_store_dir = root / "data" / "processed" / "rag" / CORPUS_VERSION / "norm"
    norm_store_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Fetch articles ---
    print(f"\n{'='*60}")
    print(f"SAGE-Indic Wikipedia Corpus Ingestion")
    print(f"Target: {len(ALL_TITLES)} articles across {len(ARTICLE_TITLES)} domains")
    print(f"Corpus Version: {CORPUS_VERSION}")
    print(f"{'='*60}\n")

    print("Phase 1: Fetching articles from Telugu Wikipedia API...")
    articles = fetch_all_articles(ALL_TITLES)
    print(f"\nFetched {len(articles)} articles total.\n")

    if not articles:
        print("ERROR: No articles fetched. Aborting.")
        sys.exit(1)

    # --- Step 2: Ingest through pipeline ---
    print("Phase 2: Ingesting through CorpusIngestionPipeline...")
    pipeline = CorpusIngestionPipeline(default_chunker=ParagraphChunker())

    all_documents = []
    all_chunks = []
    documents_dict = {}
    norm_texts_dict = {}
    domain_stats: dict[str, int] = {}

    # Also preserve the original 10 Phase 2D documents
    old_docs_path = rag_dir / "phase2d_documents.jsonl"
    old_chunks_path = rag_dir / "phase2d_chunks.jsonl"
    old_doc_ids: set[str] = set()

    if old_docs_path.is_file():
        print(f"  Preserving original Phase 2D corpus (TE_DOC_001..010)...")
        for line in old_docs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            if raw["document_id"].startswith("TE_DOC_0"):
                old_doc_ids.add(raw["document_id"])
                all_documents.append(raw)

    if old_chunks_path.is_file():
        for line in old_chunks_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            if raw["document_id"].startswith("TE_DOC_0"):
                all_chunks.append(raw)

    print(f"  Preserved {len(old_doc_ids)} existing documents and {len(all_chunks)} existing chunks.")

    # Determine domain for each article by matching against ARTICLE_TITLES
    title_to_domain: dict[str, str] = {}
    for domain, titles in ARTICLE_TITLES.items():
        for t in titles:
            title_to_domain[t] = domain

    ingested = 0
    skipped = 0

    for idx, article in enumerate(articles):
        title = article["title"]
        pageid = article["pageid"]
        revid = article["revid"]
        extract = clean_wikipedia_text(article["extract"])

        if len(extract.strip()) < MIN_ARTICLE_CHARS:
            skipped += 1
            continue

        doc_id = f"TE_DOC_WIKI_{pageid}"

        # Skip if we already have this doc from the old corpus
        if doc_id in old_doc_ids:
            skipped += 1
            continue

        # Determine domain
        domain = "general"
        for orig_title, d in title_to_domain.items():
            if orig_title in title or title in orig_title:
                domain = d
                break

        source_url = f"https://te.wikipedia.org/w/index.php?title={urllib.parse.quote(title)}&oldid={revid}"
        r_ref = f"data/raw/rag/{CORPUS_VERSION}/raw/{doc_id}.txt"
        n_ref = f"data/processed/rag/{CORPUS_VERSION}/norm/{doc_id}.txt"

        try:
            res = pipeline.ingest_document(
                raw_text=extract,
                document_id=doc_id,
                corpus_version=CORPUS_VERSION,
                source_name=f"te.wikipedia:{pageid}",
                publisher=PUBLISHER,
                title=title,
                language="te",
                script="Telugu",
                source_type=SourceType.ENCYCLOPEDIC,
                license_name=LICENSE_NAME,
                license_status=LicenseStatus.APPROVED,
                raw_text_ref=r_ref,
                normalized_text_ref=n_ref,
                provenance_notes=f"Fetched via MediaWiki API. Permanent revision oldid={revid}.",
                source_url=source_url,
                source_record_id=f"te.wikipedia:{revid}",
                source_revision=f"oldid={revid}",
                license_url=LICENSE_URL,
                license_evidence_url=LICENSE_EVIDENCE_URL,
                retrieval_eligible=True,
                eligibility_reason=(
                    "Automated ingestion: CC-BY-SA-4.0 Wikimedia article with permanent revision URL."
                ),
                metadata={"domain": domain, "pageid": pageid},
            )

            # Store raw and normalized text
            (root / r_ref).parent.mkdir(parents=True, exist_ok=True)
            (root / r_ref).write_text(res.raw_text, encoding="utf-8")
            (root / n_ref).parent.mkdir(parents=True, exist_ok=True)
            (root / n_ref).write_text(res.normalized_text, encoding="utf-8")

            # Validate chunks
            for chunk in res.chunks:
                validate_chunk_roundtrip(chunk, res.normalized_text)

            all_documents.append(res.document.to_dict())
            for chunk in res.chunks:
                all_chunks.append(chunk.to_dict())
            documents_dict[doc_id] = res.document
            norm_texts_dict[doc_id] = res.normalized_text

            domain_stats[domain] = domain_stats.get(domain, 0) + 1
            ingested += 1

        except Exception as e:
            print(f"  ERROR ingesting '{title}': {e}")
            skipped += 1
            continue

        if (idx + 1) % 25 == 0:
            print(f"  Processed {idx + 1}/{len(articles)} articles ({ingested} ingested, {skipped} skipped)")

    # --- Step 3: Write output files ---
    print(f"\nPhase 3: Writing output files...")

    docs_path = rag_dir / "phase2d_documents.jsonl"
    chunks_path = rag_dir / "phase2d_chunks.jsonl"

    with open(docs_path, "w", encoding="utf-8") as f:
        for doc in all_documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    with open(chunks_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"INGESTION COMPLETE")
    print(f"{'='*60}")
    print(f"Total documents:     {len(all_documents)}")
    print(f"  Preserved (old):   {len(old_doc_ids)}")
    print(f"  New (Wikipedia):   {ingested}")
    print(f"  Skipped/Failed:    {skipped}")
    print(f"Total chunks:        {len(all_chunks)}")
    print(f"\nDomain distribution:")
    for domain, count in sorted(domain_stats.items()):
        print(f"  {domain:30s}: {count}")
    print(f"\nOutput files:")
    print(f"  {docs_path}")
    print(f"  {chunks_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
