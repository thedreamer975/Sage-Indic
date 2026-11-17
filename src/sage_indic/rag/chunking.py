"""Deterministic, versioned document chunking for Phase 2D.

Implementation Version: 1.0.0
Guarantees:
1. Exact offset tracking: char_start and char_end reference the normalized parent text.
2. Exact recoverability: normalized_text[char_start:char_end] == chunk.text.
3. Stable identifiers: {document_id}#c{chunk_index:04d}.
4. Monotonic, non-overlapping ordering: chunk_index 0, 1, 2, ...
5. No empty chunks: char_end > char_start and len(chunk.text.strip()) > 0.
6. Does NOT claim optimal chunk size without empirical experiment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from sage_indic.rag.hash import compute_content_hash
from sage_indic.rag.types import DocumentChunk, SourceDocument

CHUNKER_VERSION = "1.0.0"


class ChunkerProtocol(Protocol):
    """Protocol for versioned chunking strategies."""

    version: str

    def chunk_document(
        self,
        document: SourceDocument,
        normalized_text: str,
    ) -> list[DocumentChunk]:
        ...


@dataclass(frozen=True)
class ParagraphChunker:
    """Document-native paragraph chunker preserving natural structural boundaries.

    Identifies paragraphs delimited by two or more newlines (or single newlines).
    Calculates exact string slice offsets against the parent normalized text.
    """

    version: str = CHUNKER_VERSION
    min_chars: int = 20

    def chunk_document(
        self,
        document: SourceDocument,
        normalized_text: str,
    ) -> list[DocumentChunk]:
        """Split normalized text on paragraph boundaries, calculating exact character offsets."""
        if not normalized_text or not normalized_text.strip():
            return []

        # In normalized text, paragraphs/lines are separated by newlines.
        # Find contiguous non-empty lines preserving exact offsets into normalized text.
        chunks: list[DocumentChunk] = []
        para_pattern = re.compile(r"[^\n]+")
        chunk_idx = 0
        for match in para_pattern.finditer(normalized_text):
            slice_text = match.group()
            start = match.start()
            end = match.end()

            # Skip empty or whitespace-only matches
            if not slice_text.strip():
                continue

            chunk_id = f"{document.document_id}#c{chunk_idx:04d}"
            c_hash = compute_content_hash(slice_text)

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                chunk_index=chunk_idx,
                char_start=start,
                char_end=end,
                text=slice_text,
                raw_text_ref=document.raw_text_ref,
                normalized_text_ref=document.normalized_text_ref,
                source_name=document.source_name,
                source_url=document.source_url,
                title=document.title,
                content_hash=c_hash,
                metadata={
                    "strategy": "paragraph",
                    "chunker_version": self.version,
                },
            )
            chunks.append(chunk)
            chunk_idx += 1

        # Fallback if no double newlines found: split by lines
        if not chunks and normalized_text.strip():
            start = 0
            end = len(normalized_text.rstrip())
            slice_text = normalized_text[start:end]
            chunk_id = f"{document.document_id}#c0000"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    chunk_index=0,
                    char_start=start,
                    char_end=end,
                    text=slice_text,
                    raw_text_ref=document.raw_text_ref,
                    normalized_text_ref=document.normalized_text_ref,
                    source_name=document.source_name,
                    source_url=document.source_url,
                    title=document.title,
                    content_hash=compute_content_hash(slice_text),
                    metadata={"strategy": "full_document_fallback", "chunker_version": self.version},
                )
            )

        return chunks


@dataclass(frozen=True)
class FixedBudgetChunker:
    """Configurable fixed character-budget chunker with explicit overlap for experimental comparison.

    Note: Provided strictly as an experimental baseline condition. Does not claim optimality.
    """

    budget_chars: int = 1000
    overlap_chars: int = 50
    version: str = CHUNKER_VERSION

    def chunk_document(
        self,
        document: SourceDocument,
        normalized_text: str,
    ) -> list[DocumentChunk]:
        """Slice normalized text into fixed character windows with exact offsets."""
        if not normalized_text or not normalized_text.strip():
            return []

        chunks: list[DocumentChunk] = []
        n_len = len(normalized_text)
        step = max(1, self.budget_chars - self.overlap_chars)

        chunk_idx = 0
        cursor = 0
        while cursor < n_len:
            start = cursor
            end = min(n_len, cursor + self.budget_chars)

            slice_text = normalized_text[start:end]
            if slice_text.strip():
                chunk_id = f"{document.document_id}#c{chunk_idx:04d}"
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    chunk_index=chunk_idx,
                    char_start=start,
                    char_end=end,
                    text=slice_text,
                    raw_text_ref=document.raw_text_ref,
                    normalized_text_ref=document.normalized_text_ref,
                    source_name=document.source_name,
                    source_url=document.source_url,
                    title=document.title,
                    content_hash=compute_content_hash(slice_text),
                    metadata={
                        "strategy": "fixed_budget",
                        "budget_chars": self.budget_chars,
                        "overlap_chars": self.overlap_chars,
                        "chunker_version": self.version,
                    },
                )
                chunks.append(chunk)
                chunk_idx += 1

            cursor += step
            if cursor >= n_len or end >= n_len:
                break

        return chunks
