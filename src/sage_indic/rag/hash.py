"""Deterministic content hashing for Phase 2D evidence documents and chunks.

Adheres to:
- Standard cryptographic SHA-256 hashing.
- Explicit recording of algorithm and hexadecimal digest.
- Verification of content integrity across raw, normalized, and chunk layers.
"""

from __future__ import annotations

import hashlib

from sage_indic.rag.types import ContentHash

SUPPORTED_ALGORITHMS: set[str] = {"sha256", "sha384", "sha512"}


def compute_content_hash(
    content: str | bytes,
    algorithm: str = "sha256",
) -> ContentHash:
    """Compute a deterministic cryptographic hash for text or byte content.

    Args:
        content: Raw or normalized text string (UTF-8 encoded) or raw bytes.
        algorithm: Standard hashing algorithm name (default 'sha256').

    Returns:
        ContentHash containing the algorithm name and hex digest.
    """
    algo_lower = algorithm.lower()
    if algo_lower not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported hash algorithm '{algorithm}'. Must be one of {sorted(SUPPORTED_ALGORITHMS)}"
        )

    hasher = hashlib.new(algo_lower)
    if isinstance(content, str):
        hasher.update(content.encode("utf-8"))
    elif isinstance(content, bytes):
        hasher.update(content)
    else:
        raise TypeError(f"Content must be str or bytes, got {type(content).__name__}")

    return ContentHash(algorithm=algo_lower, digest=hasher.hexdigest())


def verify_content_hash(
    content: str | bytes,
    expected_hash: ContentHash,
) -> bool:
    """Verify that the provided content exactly matches an expected ContentHash.

    Args:
        content: Content string or bytes.
        expected_hash: ContentHash instance to check against.

    Returns:
        True if the computed digest matches expected_hash.digest.
    """
    computed = compute_content_hash(content, algorithm=expected_hash.algorithm)
    return computed.digest.lower() == expected_hash.digest.lower()
