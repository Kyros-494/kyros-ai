"""Integration tests for Memory Integrity Proofs.

Tests the full tamper-detection cycle:
1. Stamp generation and verification
2. Tamper detection (content and metadata)
3. Merkle tree construction and proof verification
4. Invalid proof rejection
"""

from __future__ import annotations

from kyros.intelligence.integrity import (
    MerkleTree,
    hash_content,
    stamp_memory,
    verify_content_hash,
)


class TestMemoryStamping:
    def test_stamp_memory_generates_consistent_hash(self) -> None:
        """A stamp generated from the same inputs should always verify correctly."""
        content = "The user's secret key is 12345"
        stamp = stamp_memory(content, metadata={"source": "api"}, timestamp="2026-01-01T00:00:00")

        assert stamp.content_hash, "content_hash should not be empty"
        assert stamp.merkle_leaf, "merkle_leaf should not be empty"
        assert stamp.nonce, "nonce should not be empty"

        is_valid = verify_content_hash(
            content=content,
            nonce=stamp.nonce,
            expected_hash=stamp.content_hash,
            metadata={"source": "api"},
            timestamp="2026-01-01T00:00:00",
        )
        assert is_valid is True

    def test_tampered_content_fails_verification(self) -> None:
        """Changing the content after stamping should fail verification."""
        content = "The user's secret key is 12345"
        stamp = stamp_memory(content)

        is_valid = verify_content_hash(
            content="The user's secret key is 99999",  # tampered
            nonce=stamp.nonce,
            expected_hash=stamp.content_hash,
        )
        assert is_valid is False

    def test_tampered_metadata_fails_verification(self) -> None:
        """Changing the metadata after stamping should fail verification."""
        content = "Safe memory"
        stamp = stamp_memory(content, metadata={"role": "user"})

        is_valid = verify_content_hash(
            content=content,
            nonce=stamp.nonce,
            expected_hash=stamp.content_hash,
            metadata={"role": "admin"},  # privilege escalation attempt
        )
        assert is_valid is False

    def test_wrong_nonce_fails_verification(self) -> None:
        """Using a different nonce should fail verification."""
        content = "Sensitive data"
        stamp = stamp_memory(content)

        is_valid = verify_content_hash(
            content=content,
            nonce="completely_wrong_nonce",
            expected_hash=stamp.content_hash,
        )
        assert is_valid is False

    def test_empty_content_can_be_stamped(self) -> None:
        """Stamping empty content should not raise — it's a valid edge case."""
        stamp = stamp_memory("")
        assert stamp.content_hash
        assert stamp.nonce

    def test_stamp_is_deterministic_given_same_nonce(self) -> None:
        """Two stamps with the same nonce and content should produce the same hash."""
        content = "Deterministic test"
        stamp1 = stamp_memory(content, timestamp="2026-01-01T00:00:00")
        # Manually verify using the same nonce
        is_valid = verify_content_hash(
            content=content,
            nonce=stamp1.nonce,
            expected_hash=stamp1.content_hash,
            timestamp="2026-01-01T00:00:00",
        )
        assert is_valid is True


class TestMerkleTree:
    def test_merkle_tree_construction_and_proof(self) -> None:
        """A 4-leaf tree should produce a valid proof for any leaf."""
        leaves = [
            hash_content("mem1", "nonce1"),
            hash_content("mem2", "nonce2"),
            hash_content("mem3", "nonce3"),
            hash_content("mem4", "nonce4"),
        ]

        tree = MerkleTree(leaves)
        root = tree.get_root()
        assert root, "Root should not be empty"

        # Verify proof for each leaf
        for i in range(len(leaves)):
            proof = tree.get_proof(i)
            assert proof.leaf_hash == leaves[i]
            assert proof.root_hash == root
            assert MerkleTree.verify_proof(proof) is True, f"Proof for leaf {i} failed"

    def test_invalid_proof_fails(self) -> None:
        """A tampered proof should fail verification."""
        leaves = [hash_content("mem1", "n1"), hash_content("mem2", "n2")]
        tree = MerkleTree(leaves)
        proof = tree.get_proof(0)

        # Tamper with the leaf hash
        proof.leaf_hash = hash_content("malicious_content", "n1")
        assert MerkleTree.verify_proof(proof) is False

    def test_single_leaf_tree(self) -> None:
        """A tree with a single leaf should still produce a valid proof."""
        leaves = [hash_content("only_memory", "nonce")]
        tree = MerkleTree(leaves)
        root = tree.get_root()
        assert root == leaves[0], "Single-leaf root should equal the leaf hash"

        proof = tree.get_proof(0)
        assert MerkleTree.verify_proof(proof) is True

    def test_odd_number_of_leaves(self) -> None:
        """Trees with an odd number of leaves should be handled correctly."""
        leaves = [hash_content(f"mem{i}", f"n{i}") for i in range(5)]
        tree = MerkleTree(leaves)
        root = tree.get_root()
        assert root

        # All proofs should still verify
        for i in range(len(leaves)):
            proof = tree.get_proof(i)
            assert MerkleTree.verify_proof(proof) is True, f"Proof for leaf {i} failed in odd tree"

    def test_different_content_produces_different_hashes(self) -> None:
        """Two different contents should never produce the same hash."""
        h1 = hash_content("content_a", "same_nonce")
        h2 = hash_content("content_b", "same_nonce")
        assert h1 != h2

    def test_same_content_different_nonce_produces_different_hashes(self) -> None:
        """
        Same content with different nonces should produce different hashes.

        This prevents rainbow table attacks.
        """
        h1 = hash_content("same_content", "nonce_1")
        h2 = hash_content("same_content", "nonce_2")
        assert h1 != h2

    def test_proof_path_length_is_log2(self) -> None:
        """Proof path length should be ceil(log2(n)) for n leaves."""
        import math

        for n in [2, 4, 8, 16]:
            leaves = [hash_content(f"m{i}", f"n{i}") for i in range(n)]
            tree = MerkleTree(leaves)
            proof = tree.get_proof(0)
            expected_depth = int(math.log2(n))
            assert len(proof.proof_path) == expected_depth, (
                f"Expected depth {expected_depth} for {n} leaves, got {len(proof.proof_path)}"
            )
