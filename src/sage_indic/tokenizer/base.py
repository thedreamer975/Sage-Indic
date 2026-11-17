"""Base interface for SAGE-Indic tokenizers."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseTokenizer(ABC):
    """Minimal abstract interface shared by BPE, Unigram, and SAGE tokenizers."""

    @abstractmethod
    def train(self, corpus_path: str | Path, vocab_size: int, **kwargs: object) -> None:
        """Train the tokenizer vocabulary on a text corpus file.

        Args:
            corpus_path: Path to the training text file (one sentence per line).
            vocab_size: Target vocabulary capacity.
            **kwargs: Additional training options.
        """

    @abstractmethod
    def encode(self, text: str) -> list[str]:
        """Encode text into a list of string subword tokens.

        Args:
            text: Input string.

        Returns:
            List of subword token strings.
        """

    @abstractmethod
    def encode_ids(self, text: str) -> list[int]:
        """Encode text into a list of integer token IDs.

        Args:
            text: Input string.

        Returns:
            List of integer token IDs.
        """

    @abstractmethod
    def decode(self, tokens_or_ids: list[str] | list[int]) -> str:
        """Decode subword tokens or token IDs back into the reconstructed text.

        Args:
            tokens_or_ids: List of string subwords or integer IDs.

        Returns:
            Reconstructed string.
        """

    @abstractmethod
    def get_vocab_size(self) -> int:
        """Return the actual number of tokens in the vocabulary."""

    @abstractmethod
    def save(self, path: str | Path) -> None:
        """Save tokenizer configuration and vocabulary to disk."""

    @abstractmethod
    def load(self, path: str | Path) -> None:
        """Load trained tokenizer from disk."""
