"""Compression engine — LLM-based hierarchical memory summarisation.

Architecture:
    L0: Raw episodic memories (uncompressed)
    L1: 20 memories → 1 paragraph summary
    L2: 5 L1 paragraphs → 1 page summary
    L3: All L2 pages → 1 history card

The compression engine is model-agnostic and defaults to a local
extractive summariser. For production, configure an LLM backend
(OpenAI, Anthropic, Gemini) via KYROS_COMPRESSION_BACKEND.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from kyros.logging import get_logger

logger = get_logger("kyros.intelligence.compression")

# ─── Configuration ─────────────────────────────

BATCH_SIZE_L1 = 20        # Raw memories per L1 paragraph
BATCH_SIZE_L2 = 5         # L1 paragraphs per L2 page
MIN_MEMORIES_TO_COMPRESS = 100  # Don't compress agents with fewer
COMPRESSION_BACKEND = os.environ.get("KYROS_COMPRESSION_BACKEND", "extractive")


@dataclass
class CompressionResult:
    """Output of a compression operation."""
    summary: str
    input_count: int
    output_level: int
    compression_ratio: float
    latency_ms: float


@dataclass
class HistoryCard:
    """The final L3 summary — a complete agent history in one card."""
    agent_id: str
    summary: str
    memory_count: int
    compression_ratio: float
    levels: dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class CompressionEngine:
    """Multi-level memory compression engine.

    Compresses raw episodic memories through three levels:
    L1 (paragraph), L2 (page), L3 (history card).
    """

    def __init__(self, backend: str | None = None) -> None:
        self.backend = backend or COMPRESSION_BACKEND
        logger.info("Compression engine initialised", backend=self.backend)

    # ─── Core Compression ──────────────────────

    def compress_batch(self, memories: list[dict], target_level: int) -> CompressionResult:
        """Compress a batch of memories into a single summary.

        Args:
            memories: List of memory dicts with 'content' and 'created_at'.
            target_level: Output compression level (1, 2, or 3).

        Returns:
            CompressionResult with the generated summary.
        """
        start = time.monotonic()

        if not memories:
            return CompressionResult(
                summary="", input_count=0, output_level=target_level,
                compression_ratio=0.0, latency_ms=0.0,
            )

        if self.backend == "extractive":
            summary = self._extractive_compress(memories, target_level)
        elif self.backend == "openai":
            summary = self._llm_compress(memories, target_level, provider="openai")
        elif self.backend == "anthropic":
            summary = self._llm_compress(memories, target_level, provider="anthropic")
        else:
            summary = self._extractive_compress(memories, target_level)

        input_chars = sum(len(m.get("content", "")) for m in memories)
        output_chars = len(summary)
        ratio = input_chars / output_chars if output_chars > 0 else 0.0
        elapsed = (time.monotonic() - start) * 1000

        logger.info(
            "Compressed batch",
            level=target_level,
            input_count=len(memories),
            ratio=round(ratio, 1),
            latency_ms=round(elapsed, 2),
        )

        return CompressionResult(
            summary=summary,
            input_count=len(memories),
            output_level=target_level,
            compression_ratio=round(ratio, 1),
            latency_ms=round(elapsed, 2),
        )

    def _extractive_compress(self, memories: list[dict], level: int) -> str:
        """Fast extractive summarisation (no LLM required).

        Strategy:
        - L1: Concatenate → deduplicate → trim to key sentences
        - L2: Merge L1 paragraphs → extract themes
        - L3: Merge L2 pages → produce final card
        """
        contents = [m.get("content", "") for m in memories if m.get("content")]

        if level == 1:
            # L1: Group by theme, keep highest-importance sentences
            sentences = []
            for content in contents:
                # Split into sentences and keep unique ones
                for s in content.replace("\n", ". ").split(". "):
                    s = s.strip()
                    if s and len(s) > 10 and s not in sentences:
                        sentences.append(s)

            # Take top sentences (roughly 1 per 4 inputs)
            max_sentences = max(3, len(memories) // 4)
            selected = sentences[:max_sentences]
            return ". ".join(selected) + "." if selected else ""

        if level == 2:
            # L2: Merge paragraphs, extract key points
            all_text = " ".join(contents)
            sentences = [s.strip() for s in all_text.split(". ") if len(s.strip()) > 15]
            # Keep ~20% of sentences
            keep = max(3, len(sentences) // 5)
            return ". ".join(sentences[:keep]) + "." if sentences else ""

        # L3: Final card — extremely concise
        all_text = " ".join(contents)
        sentences = [s.strip() for s in all_text.split(". ") if len(s.strip()) > 15]
        keep = max(2, len(sentences) // 10)
        header = f"Agent history ({len(memories)} sources): "
        return header + ". ".join(sentences[:keep]) + "."

    def _llm_compress(self, memories: list[dict], level: int, provider: str) -> str:
        """LLM-based compression (production quality).

        Constructs a prompt and calls the configured LLM provider.
        The sync HTTP calls are safe here because compress_batch() is called
        from the compression scheduler (a standalone asyncio script), not from
        within a live request handler. If called from an async context, wrap
        with loop.run_in_executor(None, ...) to avoid blocking the event loop.
        Falls back to extractive if the LLM call fails.
        """
        contents = [m.get("content", "") for m in memories]
        joined = "\n- ".join(contents)

        level_instructions = {
            1: "Summarise these conversation turns into ONE paragraph. Preserve key facts, decisions, and user preferences.",
            2: "Summarise these paragraph summaries into a single page. Focus on overarching themes, important decisions, and recurring patterns.",
            3: "Create a concise history card from these summaries. This should be a brief profile capturing the most important information about the agent's interactions.",
        }

        prompt = f"""{level_instructions.get(level, level_instructions[1])}

Memories:
- {joined}

Summary:"""

        try:
            if provider == "openai":
                return self._call_openai(prompt)
            if provider == "anthropic":
                return self._call_anthropic(prompt)
            logger.warning(
                "Unknown LLM provider, falling back to extractive", provider=provider
            )
            return self._extractive_compress(memories, level)
        except Exception as e:
            logger.error("LLM compression failed, falling back to extractive", error=str(e))
            return self._extractive_compress(memories, level)

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API for compression.

        Uses a synchronous httpx client — must be called via
        asyncio.get_event_loop().run_in_executor() to avoid blocking
        the async event loop in production.
        """
        import httpx

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": os.environ.get("KYROS_OPENAI_MODEL", "gpt-4o-mini"),
                    "messages": [
                        {"role": "system", "content": "You are a concise summariser. Output only the summary, no preamble."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3,
                },
            )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API for compression.

        Uses a synchronous httpx client — must be called via
        asyncio.get_event_loop().run_in_executor() to avoid blocking
        the async event loop in production.
        """
        import httpx

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": os.environ.get("KYROS_ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()

    # ─── Hierarchical Compression Pipeline ─────

    def compress_agent_memories(
        self, raw_memories: list[dict]
    ) -> HistoryCard:
        """Run the full L1→L2→L3 compression pipeline.

        Args:
            raw_memories: All uncompressed (L0) memories for an agent,
                          sorted by created_at ascending.

        Returns:
            HistoryCard with the final summary and stats.
        """
        if not raw_memories:
            return HistoryCard(
                agent_id="",
                summary="No memories to compress.",
                memory_count=0,
                compression_ratio=0.0,
            )

        total_input = len(raw_memories)

        # L1: Batch raw memories into paragraphs
        l1_results = []
        for i in range(0, len(raw_memories), BATCH_SIZE_L1):
            batch = raw_memories[i : i + BATCH_SIZE_L1]
            result = self.compress_batch(batch, target_level=1)
            l1_results.append({"content": result.summary, "level": 1})

        logger.info("L1 compression complete", paragraphs=len(l1_results))

        # L2: Batch L1 paragraphs into pages
        l2_results = []
        for i in range(0, len(l1_results), BATCH_SIZE_L2):
            batch = l1_results[i : i + BATCH_SIZE_L2]
            result = self.compress_batch(batch, target_level=2)
            l2_results.append({"content": result.summary, "level": 2})

        logger.info("L2 compression complete", pages=len(l2_results))

        # L3: Merge all pages into one history card
        l3_result = self.compress_batch(l2_results, target_level=3)

        total_input_chars = sum(len(m.get("content", "")) for m in raw_memories)
        total_output_chars = len(l3_result.summary)
        overall_ratio = total_input_chars / total_output_chars if total_output_chars > 0 else 0.0

        logger.info(
            "Full compression complete",
            input_memories=total_input,
            l1_paragraphs=len(l1_results),
            l2_pages=len(l2_results),
            overall_ratio=round(overall_ratio, 1),
        )

        return HistoryCard(
            agent_id="",
            summary=l3_result.summary,
            memory_count=total_input,
            compression_ratio=round(overall_ratio, 1),
            levels={
                "l0_memories": total_input,
                "l1_paragraphs": len(l1_results),
                "l2_pages": len(l2_results),
                "l3_card": 1,
            },
        )
