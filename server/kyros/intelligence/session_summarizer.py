"""Session Summarizer Service.

Monitors active episodic sessions, and dynamically compresses historical raw turns
into unified, high-importance semantic summaries when a session exceeds 10 turns.
"""

from __future__ import annotations

import json
from datetime import datetime

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
from uuid import UUID, uuid4

from sqlalchemy import text

from kyros.logging import get_logger
from kyros.ml.models import call_llm
from kyros.storage.postgres import get_db_session

logger = get_logger("kyros.session_summarizer")

# Global callback for tracing (used by benchmarks)
_summarizer_trace_callback = None

def set_summarizer_trace_callback(callback):
    global _summarizer_trace_callback
    _summarizer_trace_callback = callback

SUMMARY_PROMPT = """
You are a highly capable Cognitive Summarization Engine.
Your task is to analyze the following sequence of conversation turns and compile them into a single, highly dense, unified semantic summary.
Focus on extracting concrete preferences, key decisions, active tasks, and facts while removing conversational filler and redundant pleasantries.

Conversation History to Summarize:
{history}

Generate a concise, dense, factual summary (1-3 paragraphs) representing this sequence.
Respond ONLY with the text of the summary. Do not include markdown formatting or conversational introductions.
"""


import asyncio

_MAX_SESSION_LOCKS = 10_000
_session_summarizer_locks: dict[str, asyncio.Lock] = {}


def _get_session_lock(agent_id: UUID, session_id: str) -> asyncio.Lock:
    """Get or create a per-session asyncio.Lock, evicting oldest if at capacity."""
    key = f"{agent_id}:{session_id}"
    if key not in _session_summarizer_locks:
        if len(_session_summarizer_locks) >= _MAX_SESSION_LOCKS:
            oldest_key = next(iter(_session_summarizer_locks))
            del _session_summarizer_locks[oldest_key]
        _session_summarizer_locks[key] = asyncio.Lock()
    return _session_summarizer_locks[key]


async def summarize_session_if_needed(
    agent_id: UUID,
    session_id: str,
    max_turns: int = 10,
    compress_count: int = 5,
) -> bool:
    """Analyze a session's turn count and compress historical turns if turn count > max_turns."""
    if not session_id or not session_id.strip():
        return False

    lock = _get_session_lock(agent_id, session_id)
    if lock.locked():
        return False

    async with lock:
        async with get_db_session() as session:
            # 1. Query all active turns in the session ordered by created_at ascending
            result = await session.execute(
                text("""
                SELECT id, content, role, created_at
                FROM episodic_memories
                WHERE agent_id = :agent_id
                  AND session_id = :session_id
                  AND deleted_at IS NULL
                ORDER BY created_at ASC
                """),
                {"agent_id": agent_id, "session_id": session_id},
            )
            turns = result.fetchall()

            if len(turns) <= max_turns:
                return False

            logger.info(
                "Session threshold exceeded — starting cognitive compression",
                agent_id=str(agent_id),
                session_id=session_id,
                total_turns=len(turns),
            )

            # 2. Extract the oldest N turns for compression
            # We want to compress all historical turns except for the most recent `keep_turns`.
            # This ensures we reduce the total active turns below `max_turns` in a single run.
            keep_turns = max_turns - compress_count
            actual_compress_count = max(compress_count, len(turns) - keep_turns)
            to_compress = turns[:actual_compress_count]

            # Format history string for LLM summarizer
            history_parts = []
            for turn in to_compress:
                role_label = turn.role.upper() if turn.role else "USER"
                history_parts.append(f"[{role_label} at {turn.created_at}]: {turn.content}")
            history_text = "\n".join(history_parts)

            # 3. Call LLM to summarize the turns
            prompt = SUMMARY_PROMPT.format(history=history_text)
            try:
                print(f"      [SUMMARIZE] Compressing {len(to_compress)} turns for session {session_id}...")
                summary_content = await call_llm(prompt, temperature=0.1)
                summary_text = summary_content.strip()
                if summary_text:
                    print(f"      [SUMMARIZE] Summary generated: {summary_text[:60]}...")
                    if _summarizer_trace_callback:
                        _summarizer_trace_callback("SESSION_SUMMARIZED", f"Compressed {len(to_compress)} turns", {"summary": summary_text})
            except Exception as e:
                logger.error("Failed to generate session summary using LLM", error=str(e))
                return False

            if not summary_text:
                return False

            # 4. Store the unified summary turn (direct SQL write to keep it lightweight)
            now = datetime.now(UTC).replace(tzinfo=None)
            summary_id = uuid4()

            # Compute a simple dummy embedding for the summary (using the first turn's embed or 0 vector fallback)
            embed_result = await session.execute(
                text("SELECT embedding, embedding_secondary, embedding_model, tenant_id FROM episodic_memories WHERE id = :id"),
                {"id": to_compress[0].id},
            )
            orig_row = embed_result.fetchone()
            if not orig_row:
                return False

            metadata = {
                "source": "session_summarizer_compression",
                "compressed_turns_count": len(to_compress),
                "original_turn_ids": [str(t.id) for t in to_compress],
            }

            await session.execute(
                text("""
                INSERT INTO episodic_memories
                    (id, agent_id, tenant_id, content, content_type, role,
                     session_id, embedding, embedding_secondary, embedding_model,
                     metadata, importance, freshness_score, decay_rate,
                     memory_category, created_at)
                VALUES
                    (:id, :agent_id, :tenant_id, :content, 'text', 'system',
                     :session_id, :embedding, :embedding_secondary, :embedding_model,
                     :metadata, 0.9, 1.0, 0.01,
                     'general', :now)
                """),
                {
                    "id": summary_id,
                    "agent_id": agent_id,
                    "tenant_id": orig_row.tenant_id,
                    "content": f"[SESSION SUMMARY] {summary_text}",
                    "session_id": session_id,
                    "embedding": orig_row.embedding,
                    "embedding_secondary": orig_row.embedding_secondary,
                    "embedding_model": orig_row.embedding_model,
                    "metadata": json.dumps(metadata),
                    "now": now,
                },
            )

            # 5. Soft-delete the original compressed turns and mark them as archived by summarizer
            to_compress_ids = [t.id for t in to_compress]
            await session.execute(
                text("""
                UPDATE episodic_memories
                SET deleted_at = :now,
                    metadata = jsonb_set(COALESCE(metadata, '{}'::jsonb), '{archived_by_summarizer}', 'true'::jsonb)
                WHERE id = ANY(:ids)
                """),
                {"now": now, "ids": to_compress_ids},
            )

            logger.info(
                "Session compression completed successfully",
                agent_id=str(agent_id),
                session_id=session_id,
                turns_compressed=len(to_compress_ids),
                summary_id=str(summary_id),
            )

            # Trigger Merkle root update asynchronously
            try:
                from kyros.intelligence.integrity_service import update_agent_merkle_root
                # Spawn fire-and-forget task
                asyncio.create_task(update_agent_merkle_root(agent_id, orig_row.tenant_id))
            except Exception as e:
                logger.warning(f"Failed to trigger Merkle root update after summarization: {e}")

            return True
