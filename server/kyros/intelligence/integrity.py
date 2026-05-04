"""C05 — Memory Integrity Proofs Engine.

Implements cryptographic tamper-detection for AI agent memories using:
1. SHA-256 content hashing at write time
2. Random nonce generation (prevents hash collision attacks)
3. Merkle tree construction and verification

The system ensures that once a memory is stored, any modification —
accidental or malicious — is mathematically detectable.

Architecture:
    Memory → SHA-256(nonce + content + metadata) → content_hash
    content_hash → Merkle leaf
    All leaves → Merkle tree → merkle_root
    merkle_root → append-only audit log (immutable)
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass

# ─── C05: SHA-256 Content Hashing ─────────────


def generate_nonce(length: int = 16) -> str:
    """Generate a cryptographically secure random nonce.

    The nonce is combined with content before hashing to prevent
    chosen-plaintext attacks and hash collisions.

    Args:
        length: Number of random bytes (output is 2×length hex chars).

    Returns:
        Hex-encoded random string (e.g., "a3f2b8c1e5d9..." — 32 chars for 16 bytes).
    """
    return secrets.token_hex(length)


def hash_content(
    content: str,
    nonce: str,
    metadata: dict | None = None,
    timestamp: str | None = None,
) -> str:
    """Compute SHA-256 hash of memory content.

    Deterministic: same inputs always produce the same hash.
    The nonce ensures uniqueness even for identical content.

    Args:
        content: The memory text content.
        nonce: Random nonce generated at write time.
        metadata: Optional metadata dict (JSON-serialized for hashing).
        timestamp: Optional creation timestamp string.

    Returns:
        64-character lowercase hex SHA-256 digest.
    """
    # Build canonical hash input (sorted JSON for determinism)
    hash_input = {
        "nonce": nonce,
        "content": content,
    }
    if metadata:
        hash_input["metadata"] = json.dumps(metadata, sort_keys=True)
    if timestamp:
        hash_input["timestamp"] = timestamp

    # Canonical serialization: sorted keys, no whitespace
    canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_content_hash(
    content: str,
    nonce: str,
    expected_hash: str,
    metadata: dict | None = None,
    timestamp: str | None = None,
) -> bool:
    """Verify that a memory's content matches its stored hash.

    This is the tamper-detection check. If the content has been
    modified in any way, the hash will not match.

    Args:
        content: Current content to verify.
        nonce: The nonce that was stored with the memory.
        expected_hash: The content_hash stored at write time.
        metadata: Optional metadata (must match what was hashed).
        timestamp: Optional timestamp (must match what was hashed).

    Returns:
        True if content is untampered, False if modified.
    """
    computed = hash_content(content, nonce, metadata, timestamp)
    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(computed, expected_hash)


# ─── Merkle Tree ──────────────────────────────


def _hash_pair(left: str, right: str) -> str:
    """Hash two nodes together to form a parent node."""
    combined = left + right
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


@dataclass
class MerkleProof:
    """A proof that a specific leaf exists in a Merkle tree.

    To verify: start with the leaf hash, apply each sibling hash
    in order (left/right as indicated), and compare the final
    result with the known root.
    """

    leaf_hash: str
    root_hash: str
    proof_path: list[dict]  # [{"hash": "abc...", "position": "left|right"}, ...]
    leaf_index: int
    tree_size: int


class MerkleTree:
    """Merkle tree for cryptographic integrity of memory batches.

    Builds a binary hash tree from memory content hashes.
    Provides proof generation and verification for individual leaves.
    """

    def __init__(self, leaf_hashes: list[str]) -> None:
        """Build a Merkle tree from a list of content hashes.

        Args:
            leaf_hashes: List of SHA-256 hex digests (one per memory).
        """
        if not leaf_hashes:
            self.root = ""
            self.leaves = []
            self._levels = []
            return

        self.leaves = list(leaf_hashes)
        self._levels = [self.leaves[:]]

        # Build tree bottom-up
        current_level = self.leaves[:]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # If odd number of nodes, duplicate the last one
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(_hash_pair(left, right))
            self._levels.append(next_level)
            current_level = next_level

        self.root = current_level[0] if current_level else ""

    def get_root(self) -> str:
        """Return the Merkle root hash."""
        return self.root

    def get_proof(self, leaf_index: int) -> MerkleProof:
        """Generate a Merkle proof for a specific leaf.

        The proof contains the sibling hashes needed to reconstruct
        the root from the leaf. This allows verifying a single memory
        without downloading the entire tree.

        Args:
            leaf_index: Index of the leaf in the original list.

        Returns:
            MerkleProof with the path from leaf to root.

        Raises:
            IndexError: If leaf_index is out of range.
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise IndexError(f"Leaf index {leaf_index} out of range (0..{len(self.leaves) - 1})")

        proof_path = []
        index = leaf_index

        for level in self._levels[:-1]:  # Skip root level
            if len(level) <= 1:
                break

            # Determine sibling
            if index % 2 == 0:
                # We are left child, sibling is right
                sibling_index = index + 1
                if sibling_index < len(level):
                    proof_path.append(
                        {
                            "hash": level[sibling_index],
                            "position": "right",
                        }
                    )
                else:
                    # Odd number — sibling is self (duplicated)
                    proof_path.append(
                        {
                            "hash": level[index],
                            "position": "right",
                        }
                    )
            else:
                # We are right child, sibling is left
                proof_path.append(
                    {
                        "hash": level[index - 1],
                        "position": "left",
                    }
                )

            index = index // 2

        return MerkleProof(
            leaf_hash=self.leaves[leaf_index],
            root_hash=self.root,
            proof_path=proof_path,
            leaf_index=leaf_index,
            tree_size=len(self.leaves),
        )

    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """Verify a Merkle proof against a known root.

        Reconstructs the path from the leaf to the root using
        the sibling hashes in the proof. If the final hash matches
        the known root, the leaf is verified as authentic.

        Args:
            proof: The MerkleProof to verify.

        Returns:
            True if the proof is valid (leaf is in the tree).
        """
        current_hash = proof.leaf_hash

        for step in proof.proof_path:
            sibling = step["hash"]
            if step["position"] == "right":
                current_hash = _hash_pair(current_hash, sibling)
            else:
                current_hash = _hash_pair(sibling, current_hash)

        return secrets.compare_digest(current_hash, proof.root_hash)


# ─── Write-Time Integration ───────────────────


@dataclass
class IntegrityStamp:
    """Generated at memory write time. Stored alongside the memory."""

    content_hash: str
    nonce: str
    merkle_leaf: str  # Same as content_hash for now; separating for future flexibility


def stamp_memory(
    content: str,
    metadata: dict | None = None,
    timestamp: str | None = None,
) -> IntegrityStamp:
    """Generate cryptographic integrity stamp for a new memory.

    Called at write time to produce the hash, nonce, and leaf
    that are stored alongside the memory content.

    Args:
        content: The memory content text.
        metadata: Optional metadata dict.
        timestamp: Optional creation timestamp string.

    Returns:
        IntegrityStamp with all fields ready for DB storage.
    """
    nonce = generate_nonce()
    content_hash = hash_content(content, nonce, metadata, timestamp)

    return IntegrityStamp(
        content_hash=content_hash,
        nonce=nonce,
        merkle_leaf=content_hash,  # Leaf = content hash
    )
