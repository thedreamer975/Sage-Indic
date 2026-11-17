"""Unigram Language Model Baseline Tokenizer for SAGE-Indic."""

from pathlib import Path

from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

from sage_indic.normalize import normalize_text
from sage_indic.tokenizer.base import BaseTokenizer


class UnigramBaselineTokenizer(BaseTokenizer):
    """Standard Unigram subword baseline using Metaspace whitespace handling."""

    def __init__(self, unk_token: str = "<unk>") -> None:
        self.unk_token = unk_token
        self._tokenizer: Tokenizer | None = None
        self._vocab_size: int = 0

    def train(self, corpus_path: str | Path, vocab_size: int, **kwargs: object) -> None:
        """Train Unigram model vocabulary on the given corpus."""
        path_str = str(corpus_path)

        tok = Tokenizer(models.Unigram())
        tok.pre_tokenizer = pre_tokenizers.Metaspace()
        tok.decoder = decoders.Metaspace()

        special_tokens = [self.unk_token, "<s>", "</s>", "<pad>"]
        trainer = trainers.UnigramTrainer(
            vocab_size=vocab_size,
            special_tokens=special_tokens,
            unk_token=self.unk_token,
            show_progress=False,
        )

        tok.train([path_str], trainer)
        self._tokenizer = tok
        self._vocab_size = tok.get_vocab_size()

    def encode(self, text: str) -> list[str]:
        """Encode text to subword strings."""
        if not text:
            return []
        if self._tokenizer is None:
            raise RuntimeError(
                "UnigramBaselineTokenizer must be trained or loaded before encoding."
            )
        normalized = normalize_text(text)
        return self._tokenizer.encode(normalized).tokens

    def encode_ids(self, text: str) -> list[int]:
        """Encode text to token integer IDs."""
        if not text:
            return []
        if self._tokenizer is None:
            raise RuntimeError(
                "UnigramBaselineTokenizer must be trained or loaded before encoding."
            )
        normalized = normalize_text(text)
        return self._tokenizer.encode(normalized).ids

    def decode(self, tokens_or_ids: list[str] | list[int]) -> str:
        """Decode subword tokens or token IDs back to text."""
        if not tokens_or_ids:
            return ""
        if self._tokenizer is None:
            raise RuntimeError(
                "UnigramBaselineTokenizer must be trained or loaded before decoding."
            )

        if isinstance(tokens_or_ids[0], int):
            int_ids = [int(i) for i in tokens_or_ids]
            return self._tokenizer.decode(int_ids)

        # List of string tokens: map to IDs and decode
        str_tokens = [str(t) for t in tokens_or_ids]
        ids = [self._tokenizer.token_to_id(t) for t in str_tokens]
        valid_ids = [i for i in ids if i is not None]
        return self._tokenizer.decode(valid_ids)

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
