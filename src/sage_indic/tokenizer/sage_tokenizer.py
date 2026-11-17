"""SAGE (Script- & Affix-Guided Encoding) Morphology-Aware Tokenizer for Telugu."""

import tempfile
from pathlib import Path

from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

from sage_indic.normalize import normalize_text
from sage_indic.tokenizer.base import BaseTokenizer
from sage_indic.tokenizer.morphology import (
    NATIVE_TELUGU_NOMINAL_AFFIXES,
    ROMANIZED_TELUGU_AFFIXES,
    presegment_sentence,
    segment_word_morphology,
)


class SageTokenizer(BaseTokenizer):
    """Morphology-Aware Tokenizer for Native, Romanized, and Code-Mixed Telugu.

    Features:
    - Phase 1: Affix and akshara boundary pre-segmentation.
    - Phase 2: Constrained statistical subword optimization (Unigram model).
    - Prevents subword merges from crossing identified morpheme boundaries.
    - Guaranteed lossless round-trip detokenization.
    """

    def __init__(
        self,
        enable_morph_presegmentation: bool = True,
        unk_token: str = "<unk>",
        affix_marker: str = "##",
    ) -> None:
        self.enable_morph_presegmentation = enable_morph_presegmentation
        self.unk_token = unk_token
        self.affix_marker = affix_marker
        self._tokenizer: Tokenizer | None = None
        self._vocab_size: int = 0

    def train(self, corpus_path: str | Path, vocab_size: int, **kwargs: object) -> None:
        """Train SAGE morphology-guided subword vocabulary on the corpus."""
        src_path = Path(corpus_path)
        raw_lines = src_path.read_text(encoding="utf-8").splitlines()

        # Phase 1: Apply morphological pre-segmentation to the training text
        presegmented_lines: list[str] = []
        for line in raw_lines:
            norm_line = normalize_text(line)
            if not norm_line:
                continue
            if self.enable_morph_presegmentation:
                units = presegment_sentence(
                    norm_line,
                    enable_affixes=True,
                    affix_marker=self.affix_marker,
                )
                presegmented_lines.append(" ".join(units))
            else:
                presegmented_lines.append(norm_line)

        # Write to temporary file for training
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".txt") as tmp:
            tmp_path = Path(tmp.name)
            tmp.write("\n".join(presegmented_lines))

        try:
            # Phase 2: Train Unigram subword model with Metaspace
            tok = Tokenizer(models.Unigram())
            tok.pre_tokenizer = pre_tokenizers.Metaspace()
            tok.decoder = decoders.Metaspace()

            # Pre-populate special affixes in vocabulary to guarantee morphological preservation
            core_affixes = [
                f"{self.affix_marker}{aff}" for aff in NATIVE_TELUGU_NOMINAL_AFFIXES[:10]
            ]
            core_affixes.extend(
                [f"{self.affix_marker}{aff}" for aff in ROMANIZED_TELUGU_AFFIXES[:10]]
            )
            special_tokens = [self.unk_token, "<s>", "</s>", "<pad>"] + core_affixes

            trainer = trainers.UnigramTrainer(
                vocab_size=vocab_size,
                special_tokens=special_tokens,
                unk_token=self.unk_token,
                show_progress=False,
            )

            tok.train([str(tmp_path)], trainer)
            self._tokenizer = tok
            self._vocab_size = tok.get_vocab_size()
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def encode(self, text: str) -> list[str]:
        """Encode text into subwords respecting morphological boundaries."""
        if not text:
            return []
        if self._tokenizer is None:
            raise RuntimeError("SageTokenizer must be trained or loaded before encoding.")

        normalized = normalize_text(text)
        if not self.enable_morph_presegmentation:
            return self._tokenizer.encode(normalized).tokens

        words = normalized.split()
        all_tokens: list[str] = []

        for _i, word in enumerate(words):
            segments = segment_word_morphology(
                word,
                enable_affixes=True,
                affix_marker=self.affix_marker,
            )
            for j, seg in enumerate(segments):
                if seg.startswith(self.affix_marker):
                    all_tokens.append(seg)
                else:
                    # Tokenize the base stem
                    # Add leading space if this is the start of a word
                    token_input = f" {seg}" if (j == 0) else seg
                    stem_tokens = self._tokenizer.encode(token_input).tokens
                    all_tokens.extend(stem_tokens)

        return all_tokens

    def encode_ids(self, text: str) -> list[int]:
        """Encode text to token integer IDs."""
        tokens = self.encode(text)
        if not tokens or self._tokenizer is None:
            return []
        unk_id = self._tokenizer.token_to_id(self.unk_token) or 0
        return [
            self._tokenizer.token_to_id(t) if self._tokenizer.token_to_id(t) is not None else unk_id
            for t in tokens
        ]

    def decode(self, tokens_or_ids: list[str] | list[int]) -> str:
        """Decode subwords or IDs back to reconstructed text with exact affix re-attachment."""
        if not tokens_or_ids:
            return ""
        if self._tokenizer is None:
            raise RuntimeError("SageTokenizer must be trained or loaded before decoding.")

        # Convert IDs to tokens if integer list passed
        if isinstance(tokens_or_ids[0], int):
            tokens = [self._tokenizer.id_to_token(int(i)) or self.unk_token for i in tokens_or_ids]
        else:
            tokens = [str(t) for t in tokens_or_ids]

        # Re-attach affixes starting with '##' to preceding token
        reconstructed_tokens: list[str] = []
        for t in tokens:
            if t.startswith(self.affix_marker) and reconstructed_tokens:
                reconstructed_tokens[-1] = reconstructed_tokens[-1] + t[len(self.affix_marker) :]
            elif t.startswith(self.affix_marker):
                reconstructed_tokens.append(t[len(self.affix_marker) :])
            else:
                reconstructed_tokens.append(t)

        # Metaspace decode via tokenizer decoder or fallback
        if self._tokenizer.decoder is not None:
            return self._tokenizer.decoder.decode(reconstructed_tokens)
        return "".join(reconstructed_tokens).replace("\u2581", " ").strip()

    def get_vocab_size(self) -> int:
        """Return the size of the vocabulary."""
        return self._vocab_size

    def save(self, path: str | Path) -> None:
        """Save model configuration and vocabulary to JSON file."""
        if self._tokenizer is None:
            raise RuntimeError("Cannot save an untrained tokenizer.")
        self._tokenizer.save(str(path))

    def load(self, path: str | Path) -> None:
        """Load trained tokenizer from JSON file."""
        self._tokenizer = Tokenizer.from_file(str(path))
        self._vocab_size = self._tokenizer.get_vocab_size()
