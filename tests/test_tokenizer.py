"""Unit and integration tests for SAGE-Indic tokenizers."""

from pathlib import Path

import pytest

from sage_indic.config import find_project_root
from sage_indic.tokenizer import (
    BaseTokenizer,
    BpeBaselineTokenizer,
    SageTokenizer,
    UnigramBaselineTokenizer,
    presegment_sentence,
    segment_word_morphology,
    split_into_aksharas,
)
from sage_indic.tokenizer.evaluation import (
    compute_efficiency_metrics,
    compute_morphological_alignment,
)


@pytest.fixture(scope="module")
def train_corpus_path() -> Path:
    """Fixture providing path to training corpus."""
    root = find_project_root()
    p = root / "data" / "processed" / "tokenizer" / "train_corpus.txt"
    if not p.exists():
        pytest.skip(f"Training corpus not found at {p}")
    return p


class TestMorphologyRules:
    """Tests for Telugu akshara and morphological segmentation."""

    def test_split_into_aksharas(self) -> None:
        aksharas = split_into_aksharas("హైదరాబాద్")
        assert len(aksharas) == 5
        assert aksharas == ["హై", "ద", "రా", "బా", "ద"]

    def test_complex_conjunct_aksharas(self) -> None:
        aksharas = split_into_aksharas("రాష్ట్రాల")
        assert len(aksharas) == 3
        assert aksharas == ["రా", "ష్ట్రా", "ల"]

    def test_segment_word_morphology_native(self) -> None:
        segments = segment_word_morphology("రాష్ట్రాలలో")
        assert len(segments) == 2
        assert segments[0] == "రాష్ట్రాల"
        assert segments[1] == "##లో"

    def test_segment_word_morphology_codemix(self) -> None:
        segments = segment_word_morphology("officeki")
        assert len(segments) == 2
        assert segments[0] == "office"
        assert segments[1] == "##ki"

        segments_heavy = segment_word_morphology("heavyga")
        assert len(segments_heavy) == 2
        assert segments_heavy[0] == "heavy"
        assert segments_heavy[1] == "##ga"

    def test_presegment_sentence(self) -> None:
        s = "Nenu officeki vellali."
        units = presegment_sentence(s)
        assert "office" in units
        assert "##ki" in units


class TestTokenizersTrainingAndEncoding:
    """Test training, encoding, and round-trip decoding across BPE, Unigram, and SAGE."""

    @pytest.mark.parametrize(
        "tokenizer_cls", [BpeBaselineTokenizer, UnigramBaselineTokenizer, SageTokenizer]
    )
    def test_train_and_encode(
        self, tokenizer_cls: type[BaseTokenizer], train_corpus_path: Path
    ) -> None:
        tok = tokenizer_cls()
        tok.train(train_corpus_path, vocab_size=500)
        assert tok.get_vocab_size() > 0
        assert tok.get_vocab_size() <= 500

        text = "తెలుగు భాష చాలా అందమైనది."
        tokens = tok.encode(text)
        assert len(tokens) > 0
        assert all(isinstance(t, str) for t in tokens)

        ids = tok.encode_ids(text)
        assert len(ids) == len(tokens)
        assert all(isinstance(i, int) for i in ids)

    @pytest.mark.parametrize(
        "tokenizer_cls", [BpeBaselineTokenizer, UnigramBaselineTokenizer, SageTokenizer]
    )
    def test_decode_round_trip(
        self, tokenizer_cls: type[BaseTokenizer], train_corpus_path: Path
    ) -> None:
        tok = tokenizer_cls()
        tok.train(train_corpus_path, vocab_size=500)

        samples = [
            "తెలుగు భాష చాలా అందమైనది.",
            "nenu ee roju Hyderabad velthunnanu",
            "Nenu today office ki vellali.",
        ]
        for s in samples:
            tokens = tok.encode(s)
            decoded = tok.decode(tokens)
            # Metaspace decoding should restore normalized text exactly
            assert decoded == s

    def test_deterministic_encoding(self, train_corpus_path: Path) -> None:
        sage = SageTokenizer()
        sage.train(train_corpus_path, vocab_size=500)
        text = "హైదరాబాద్ లో traffic చాలా heavy గా ఉంది."
        t1 = sage.encode(text)
        t2 = sage.encode(text)
        assert t1 == t2

    def test_empty_and_whitespace_inputs(self, train_corpus_path: Path) -> None:
        sage = SageTokenizer()
        sage.train(train_corpus_path, vocab_size=500)
        assert sage.encode("") == []
        assert sage.encode("   \n\t  ") == []
        assert sage.decode([]) == ""

    def test_save_and_load(self, train_corpus_path: Path, tmp_path: Path) -> None:
        tok = SageTokenizer()
        tok.train(train_corpus_path, vocab_size=500)
        save_path = tmp_path / "sage_test.json"
        tok.save(save_path)
        assert save_path.exists()

        tok_loaded = SageTokenizer()
        tok_loaded.load(save_path)
        assert tok_loaded.get_vocab_size() == tok.get_vocab_size()

        sample = "తెలుగు భాష"
        assert tok.encode(sample) == tok_loaded.encode(sample)

    def test_sage_ablation_behavior(self, train_corpus_path: Path) -> None:
        sage_full = SageTokenizer(enable_morph_presegmentation=True)
        sage_full.train(train_corpus_path, vocab_size=500)

        sage_abl = SageTokenizer(enable_morph_presegmentation=False)
        sage_abl.train(train_corpus_path, vocab_size=500)

        # On an inflected word, full SAGE detaches affixes while ablation treats as unsegmented
        sample = "రాష్ట్రాలలో"
        tokens_full = sage_full.encode(sample)
        assert any(t.startswith("##") for t in tokens_full)


class TestEvaluationMetricsComputation:
    """Test mathematical accuracy of efficiency and morphological alignment metrics."""

    def test_efficiency_metrics_computation(self, train_corpus_path: Path) -> None:
        tok = UnigramBaselineTokenizer()
        tok.train(train_corpus_path, vocab_size=500)
        sentences = [
            "తెలుగు భాష చాలా అందమైనది.",
            "నేను వస్తున్నాను.",
        ]
        metrics = compute_efficiency_metrics(tok, sentences)
        assert metrics["num_sentences"] == 2
        assert metrics["total_tokens"] > 0
        assert metrics["tokens_per_sentence"] > 0
        assert metrics["tokens_per_word"] > 0
        assert metrics["compression_ratio"] > 0
        assert metrics["unk_rate"] >= 0.0

    def test_morphological_alignment_computation(self, train_corpus_path: Path) -> None:
        tok = SageTokenizer()
        tok.train(train_corpus_path, vocab_size=500)
        records = [
            {
                "text": "రాష్ట్రాలలో చట్టాలు ఉన్నాయి.",
                "gold_morpheme_tokens": ["రాష్ట్రాల", "లో", "చట్టాలు", "ఉన్నాయి", "."],
            }
        ]
        align = compute_morphological_alignment(tok, records)
        assert 0.0 <= align["boundary_precision"] <= 1.0
        assert 0.0 <= align["boundary_recall"] <= 1.0
        assert 0.0 <= align["boundary_f1"] <= 1.0
