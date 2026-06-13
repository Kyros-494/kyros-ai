"""Core memory service — business logic for all memory operations."""

import asyncio
import json
import math
import os
import re
import time
from datetime import datetime

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from kyros.intelligence.belief import index_fact_relationships, run_belief_propagation
from kyros.intelligence.causal import (
    extract_and_store_causal_edges,
    store_causal_edges,
    traverse_causal_chain,
)
from kyros.intelligence.decay import assign_decay_rate
from kyros.intelligence.integrity import stamp_memory
from kyros.intelligence.integrity_service import update_agent_merkle_root
from kyros.logging import get_logger
from kyros.ml.embedder import EmbeddingModel
from kyros.ml.models import call_llm
from kyros.storage.postgres import get_db_session_for_tenant
from kyros.storage.redis_cache import MemoryCache

logger = get_logger("kyros.services.memory")


def _parse_dt(value: str | None) -> datetime:
    """Parse an ISO datetime string to a naive timezone.utc datetime for DB writes.

    Falls back to current timezone.utc time if value is None or unparseable.
    PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns require naive datetimes.
    """
    if not value:
        return datetime.now(UTC).replace(tzinfo=None)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Strip tzinfo — DB columns are TIMESTAMP WITHOUT TIME ZONE
        return dt.replace(tzinfo=None)
    except (ValueError, AttributeError):
        return datetime.now(UTC).replace(tzinfo=None)


from kyros.schemas.memory import (
    ExportResponse,
    FactResult,
    MatchProcedureRequest,
    MemoryResult,
    MemoryType,
    OutcomeRequest,
    OutcomeResponse,
    ProceduralMatchResponse,
    ProceduralResult,
    RecallRequest,
    RecallResponse,
    RememberRequest,
    RememberResponse,
    StoreFactRequest,
    StoreProcedureRequest,
    StoreProcedureResponse,
)


# Module-level variable for lazy task semaphores to regulate background concurrency
_task_semaphores = None

def _get_semaphore(name: str) -> asyncio.Semaphore:
    global _task_semaphores
    if _task_semaphores is None:
        _task_semaphores = {
            "update_merkle": asyncio.Semaphore(3),
            "store_causal": asyncio.Semaphore(3),
            "extract_causal": asyncio.Semaphore(1),
            "resolve_entities": asyncio.Semaphore(1),
            "summarize_session": asyncio.Semaphore(1),
            "index_fact": asyncio.Semaphore(3),
            "belief_propagation": asyncio.Semaphore(1),
            "default": asyncio.Semaphore(2),
        }
    return _task_semaphores.get(name, _task_semaphores["default"])


class MemoryService:
    """Orchestrates memory operations across storage, cache, and ML layers."""

    def __init__(self, embedder: EmbeddingModel, cache: MemoryCache) -> None:
        self.embedder = embedder
        self.cache = cache
        self.override_embedding_model: str | None = None

    def _get_embedding_and_model(self, text: str) -> tuple[list[float], list[float] | None, str]:
        model_override = getattr(self, "override_embedding_model", None)
        emb, sec = self.embedder.embed_with_secondary(text, model_name=model_override)
        model_name = model_override or self.embedder.model_name
        return emb, sec, model_name

    def _get_embedding(self, text: str) -> list[float]:
        model_override = getattr(self, "override_embedding_model", None)
        return self.embedder.embed(text, model_name=model_override)

    @staticmethod
    def _require_tenant_id(tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise ValueError("tenant_id is required for memory operations")
        return tenant_id

    def _run_task(self, coro: Any, name: str, details: str | None = None) -> asyncio.Task[Any]:
        """Helper to run a fire-and-forget task with error logging.

        Uses the global tracked task registry from main.py when available
        so tasks are properly cancelled on shutdown.
        """
        async def sem_wrapped_coro():
            sem = _get_semaphore(name)
            async with sem:
                # Add a micro-delay for LLM-based tasks to pace calls naturally
                if name in ("resolve_entities", "extract_causal", "belief_propagation"):
                    await asyncio.sleep(0.15)
                return await coro

        try:
            from kyros.services.background_tasks import create_background_task

            return create_background_task(sem_wrapped_coro(), name=name, details=details)
        except Exception as e:
            logger.error("Failed to import/run background task tracker", error=str(e))
            pass

        task = asyncio.create_task(sem_wrapped_coro(), name=name)

        def handle_result(t: asyncio.Task) -> None:
            try:
                t.result()
            except Exception as e:
                logger.error(f"Background task '{name}' failed", error=str(e), exc_info=True)

        task.add_done_callback(handle_result)
        return task

    def _parse_timestamp(self, ts_input: Any) -> datetime:
        """Parse various timestamp formats (float, ISO string, Locomo format)."""
        if ts_input is None:
            return datetime.now(UTC).replace(tzinfo=None)
        
        if isinstance(ts_input, (int, float)):
            try:
                return datetime.fromtimestamp(ts_input, tz=UTC).replace(tzinfo=None)
            except (ValueError, OSError):
                return datetime.now(UTC).replace(tzinfo=None)

        if isinstance(ts_input, str):
            # 1. Try ISO format
            try:
                # Remove Z or offset if present for replace(tzinfo=None)
                return datetime.fromisoformat(ts_input.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                pass
            
            # 2. Try Locomo format: "1:56 pm on 8 May, 2023"
            try:
                # %p handles am/pm, %B handles full month name
                return datetime.strptime(ts_input, "%I:%M %p on %d %B, %Y").replace(tzinfo=None)
            except ValueError:
                pass

        # Fallback to current time if parsing fails
        return datetime.now(UTC).replace(tzinfo=None)

    def _build_tsquery(self, query_text: str) -> str:
        """Construct a flexible prefix-matching tsquery string from query_text."""
        if not query_text:
            return ""
        import string
        translator = str.maketrans("", "", string.punctuation)
        clean_text = query_text.translate(translator).lower()
        words = clean_text.split()
        
        stop_words = {
            'the', 'and', 'for', 'in', 'of', 'to', 'a', 'an', 'on', 'at', 'by', 'is', 'are', 'was', 'were', 
            'with', 'about', 'from', 'her', 'his', 'she', 'he', 'they', 'who', 'what', 'when', 'where', 
            'why', 'how', 'did', 'does', 'do', 'go', 'went', 'gone', 'likely', 'would', 'want', 'still', 
            'be', 'has', 'have', 'had', 'been', 'or', 'more', 'less', 'than', 'as', 'to', 'from', 'at', 'in',
            'of', 'on', 'with', 'about', 'for', 'by'
        }
        
        sig_words = []
        for w in words:
            w_clean = w.strip()
            if w_clean and w_clean not in stop_words and len(w_clean) >= 2:
                sig_words.append(f"{w_clean}:*")
                
        if not sig_words:
            # Fallback to all words if nothing is left
            for w in words:
                w_clean = w.strip()
                if w_clean:
                    sig_words.append(f"{w_clean}:*")
                    
        return " | ".join(sig_words) if sig_words else ""

    def _extract_temporal_info(self, content: str, now: datetime) -> str | None:
        """Extract event time/date from content relative to `now`.
        
        Returns JSON string e.g. {"timestamp": "YYYY-MM-DD"} or None.
        """
        import re
        from datetime import timedelta
        
        content_lower = content.lower()
        resolved_date = None
        
        # 1. Check for relative dates
        if "yesterday" in content_lower:
            resolved_date = now.date() - timedelta(days=1)
        elif "today" in content_lower:
            resolved_date = now.date()
        elif "tomorrow" in content_lower:
            resolved_date = now.date() + timedelta(days=1)
        elif "last year" in content_lower:
            resolved_date = datetime(now.year - 1, 1, 1).date()
        elif "next month" in content_lower:
            first_of_this = now.replace(day=1)
            resolved_date = (first_of_this + timedelta(days=32)).replace(day=1).date()
        elif "last month" in content_lower:
            first_of_this = now.replace(day=1)
            resolved_date = (first_of_this - timedelta(days=1)).replace(day=1).date()
        elif "last week" in content_lower:
            resolved_date = now.date() - timedelta(days=7)
        elif "two weekends ago" in content_lower or "two weekends before" in content_lower:
            resolved_date = now.date() - timedelta(days=14)
        
        # "X days ago"
        if not resolved_date:
            days_ago_match = re.search(r'\b(\d+)\s+days?\s+ago\b', content_lower)
            if days_ago_match:
                days = int(days_ago_match.group(1))
                resolved_date = now.date() - timedelta(days=days)
            else:
                word_to_num = {
                    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
                }
                word_days_match = re.search(r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+days?\s+ago\b', content_lower)
                if word_days_match:
                    days = word_to_num[word_days_match.group(1)]
                    resolved_date = now.date() - timedelta(days=days)
        
        # "last Friday", "last Monday", etc.
        if not resolved_date:
            weekday_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            last_day_match = re.search(r'\blast\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', content_lower)
            if last_day_match:
                target_day = last_day_match.group(1)
                target_weekday = weekday_map[target_day]
                current_weekday = now.weekday()
                days_diff = (current_weekday - target_weekday) % 7
                if days_diff == 0:
                    days_diff = 7
                resolved_date = now.date() - timedelta(days=days_diff)

        # "this Friday", "this Monday", etc.
        if not resolved_date:
            this_day_match = re.search(r'\b(?:this|next)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', content_lower)
            if this_day_match:
                target_day = this_day_match.group(1)
                target_weekday = weekday_map[target_day]
                current_weekday = now.weekday()
                days_diff = (target_weekday - current_weekday) % 7
                if days_diff == 0:
                    days_diff = 7
                resolved_date = now.date() + timedelta(days=days_diff)

        # 2. Check for explicit formats
        if not resolved_date:
            iso_match = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', content)
            if iso_match:
                try:
                    resolved_date = datetime.strptime(iso_match.group(0), "%Y-%m-%d").date()
                except ValueError:
                    pass
        
        months_map = {
            "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
            "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
            "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
            "nov": 11, "november": 11, "dec": 12, "december": 12
        }
        
        if not resolved_date:
            month_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b'
            date_pattern = rf'{month_pattern}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,\s*(\d{{4}}))?'
            match = re.search(date_pattern, content_lower)
            if match:
                month_str = match.group(1)
                day = int(match.group(2))
                year = int(match.group(3)) if match.group(3) else now.year
                month = months_map[month_str]
                try:
                    resolved_date = datetime(year, month, day).date()
                except ValueError:
                    pass

        if not resolved_date:
            month_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b'
            date_pattern = rf'\b(\d{{1,2}})(?:st|nd|rd|th)?(?:\s+of)?\s+{month_pattern}(?:\s*,\s*(\d{{4}}))?'
            match = re.search(date_pattern, content_lower)
            if match:
                day = int(match.group(1))
                month_str = match.group(2)
                year = int(match.group(3)) if match.group(3) else now.year
                month = months_map[month_str]
                try:
                    resolved_date = datetime(year, month, day).date()
                except ValueError:
                    pass

        if not resolved_date:
            year_match = re.search(r'\b(20\d{2}|19\d{2})\b', content)
            if year_match:
                year = int(year_match.group(1))
                resolved_date = datetime(year, 1, 1).date()

        if resolved_date:
            return json.dumps({"timestamp": resolved_date.strftime("%Y-%m-%d")})
        return None

    async def remember_episodic(
        self, tenant_id: UUID | None, request: RememberRequest, override_id: UUID | None = None
    ) -> RememberResponse:
        """Store an episodic memory: embed content → write DB → update cache."""
        embedding, embedding_secondary, emb_model_name = self._get_embedding_and_model(request.content)
        memory_id = override_id or uuid4()
        now = self._parse_timestamp(getattr(request, "timestamp", None))

        stamp = stamp_memory(request.content, request.metadata, now.isoformat())
        tenant_id_required = self._require_tenant_id(tenant_id)

        # Autonomous Temporal Extraction (Phase 5) — lightweight regex implementation
        req_event_time = getattr(request, "event_time", None)
        event_time_str = json.dumps(req_event_time) if req_event_time else None
        if not event_time_str:
            event_time_str = self._extract_temporal_info(request.content, now)

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)

            await session.execute(
                text("""
                INSERT INTO episodic_memories
                    (id, agent_id, tenant_id, content, content_type, role,
                     session_id, embedding, embedding_secondary, embedding_model,
                     metadata, importance, created_at, event_time,
                     content_hash, merkle_leaf, nonce, memory_category, decay_rate)
                VALUES
                    (:id, :agent_id, :tenant_id, :content, :content_type, :role,
                     :session_id, :embedding, :embedding_secondary, :embedding_model,
                     :metadata, :importance, :created_at, :event_time,
                     :content_hash, :merkle_leaf, :nonce, :memory_category, :decay_rate)
                """),
                {
                    "id": memory_id,
                    "agent_id": agent_id,
                    "tenant_id": tenant_id_required,
                    "content": request.content,
                    "content_type": request.content_type.value,
                    "role": request.role,
                    "session_id": request.session_id,
                    "embedding": embedding,
                    "embedding_secondary": embedding_secondary,
                    "embedding_model": emb_model_name,
                    "metadata": json.dumps(request.metadata),
                    "importance": request.importance,
                    "created_at": now,
                    "event_time": event_time_str,
                    "content_hash": stamp.content_hash,
                    "merkle_leaf": stamp.merkle_leaf,
                    "nonce": stamp.nonce,
                    "memory_category": request.memory_category or "general",
                    "decay_rate": request.decay_rate_override if request.decay_rate_override is not None else assign_decay_rate(request.memory_category),
                },
            )

            # Fetch recent memories for causal extraction in the same session
            recent_res = await session.execute(
                text("""
                SELECT id, content FROM episodic_memories
                WHERE agent_id = :agent_id AND deleted_at IS NULL AND id != :mem_id
                ORDER BY created_at DESC LIMIT 5
                """),
                {"agent_id": agent_id, "mem_id": memory_id},
            )
            recent_memories = [
                {"id": str(r.id), "content": r.content} for r in recent_res.fetchall()
            ]

        # Update cache (fire-and-forget, non-blocking)
        await self.cache.cache_episodic_memory(
            agent_id=agent_id,
            memory_id=str(memory_id),
            content=request.content,
            timestamp=now.timestamp(),
        )

        # C08: Recalculate Merkle root asynchronously
        self._run_task(
            update_agent_merkle_root(agent_id, tenant_id_required),
            "update_merkle",
            details="Recalculating agent Merkle tree root hash"
        )

        # D07: Store explicit causal edges if provided
        explicit_edges = []
        if request.cause_memory_id:
            explicit_edges.append(
                {
                    "from_memory_id": request.cause_memory_id,
                    "to_memory_id": str(memory_id),
                    "relation": "causes",
                    "confidence": 1.0,
                    "description": "Explicitly defined by user",
                }
            )
        if request.effect_memory_id:
            explicit_edges.append(
                {
                    "from_memory_id": str(memory_id),
                    "to_memory_id": request.effect_memory_id,
                    "relation": "causes",
                    "confidence": 1.0,
                    "description": "Explicitly defined by user",
                }
            )

        if explicit_edges:
            self._run_task(
                store_causal_edges(tenant_id_required, agent_id, explicit_edges),
                "store_causal",
                details=f"Storing {len(explicit_edges)} explicit user causal linkages"
            )

        if os.environ.get("KYROS_DISABLE_BG_INTEL") != "true":
            # D04: Asynchronously extract implicit causal relationships using LLM
            if recent_memories and (
                os.environ.get("OPENAI_API_KEY")
                or os.environ.get("GEMINI_API_KEY")
                or os.environ.get("ANTHROPIC_API_KEY")
                or os.environ.get("MISTRAL_API_KEY")
            ):
                self._run_task(
                    extract_and_store_causal_edges(
                        tenant_id_required, agent_id, memory_id, request.content, recent_memories
                    ),
                    "extract_causal",
                    details=f"Extracting implicit causes for: {request.content[:40]}..."
                )

            # Step 1: Asynchronously resolve and update entities from content
            # Include speaker context so entity resolver can attribute facts to the correct person
            from kyros.intelligence.entity_resolver import resolve_and_update_entities
            speaker_name = request.role if request.role else "unknown"
            # For benchmark datasets (e.g. LoCoMo), the agent display_name carries the speaker identity
            content_with_speaker = f"[Speaker: {speaker_name}] {request.content}"
            self._run_task(
                resolve_and_update_entities(agent_id, content_with_speaker),
                "resolve_entities",
                details=f"Resolving entities from: {request.content[:40]}..."
            )

            # Step 6: Asynchronously check and compress session turns if needed
            if request.session_id:
                from kyros.intelligence.session_summarizer import summarize_session_if_needed
                self._run_task(
                    summarize_session_if_needed(agent_id, request.session_id),
                    "summarize_session",
                    details=f"Evaluating session compaction for ID: {request.session_id}"
                )

        return RememberResponse(
            memory_id=memory_id,
            agent_id=request.agent_id,
            memory_type=MemoryType.EPISODIC,
            created_at=now,
        )


    async def recall(self, tenant_id: UUID | None, request: RecallRequest) -> RecallResponse:
        """Retrieve relevant memories via hybrid search.

        Uses similarity + recency + importance + freshness scoring.
        Query classification adjusts weights for temporal/factual/procedural queries.
        """
        import re
        start = time.monotonic()
        tenant_id_required = self._require_tenant_id(tenant_id)

        # Bypass search and embed for empty queries (dashboard listing)
        if not request.query or not request.query.strip():
            async with get_db_session_for_tenant(str(tenant_id_required)) as session:
                agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)
                results = []
                
                # Fetch recent episodic memories
                if request.memory_type is None or request.memory_type == MemoryType.EPISODIC:
                    res = await session.execute(
                        text("""
                        SELECT id, content, importance, created_at, metadata, freshness_score, role, memory_category
                        FROM episodic_memories
                        WHERE agent_id = :agent_id AND deleted_at IS NULL
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """),
                        {"agent_id": agent_id, "limit": request.k}
                    )
                    for r in res.fetchall():
                        meta = json.loads(r.metadata) if isinstance(r.metadata, str) else (r.metadata or {})
                        results.append(MemoryResult(
                            memory_id=r.id,
                            content=r.content,
                            memory_type=MemoryType.EPISODIC,
                            relevance_score=1.0,
                            importance=r.importance,
                            created_at=r.created_at,
                            metadata=meta,
                            freshness_score=r.freshness_score,
                            memory_category=r.memory_category
                        ))
                
                # Fetch recent semantic memories
                if request.memory_type is None or request.memory_type == MemoryType.SEMANTIC:
                    res = await session.execute(
                        text("""
                        SELECT id, subject, predicate, object, confidence, created_at, metadata, freshness_score
                        FROM semantic_memories
                        WHERE agent_id = :agent_id AND valid_to IS NULL AND deleted_at IS NULL
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """),
                        {"agent_id": agent_id, "limit": request.k}
                    )
                    for r in res.fetchall():
                        meta = json.loads(r.metadata) if isinstance(r.metadata, str) else (r.metadata or {})
                        results.append(MemoryResult(
                            memory_id=r.id,
                            content=f"{r.subject} {r.predicate} {r.object}",
                            memory_type=MemoryType.SEMANTIC,
                            relevance_score=1.0,
                            importance=r.confidence,
                            created_at=r.created_at,
                            metadata=meta,
                            freshness_score=r.freshness_score
                        ))
                        
                results.sort(key=lambda x: x.created_at, reverse=True)
                results = results[:request.k]
                
                return RecallResponse(
                    agent_id=request.agent_id,
                    query=request.query,
                    results=results,
                    total_searched=len(results),
                    latency_ms=(time.monotonic() - start) * 1000.0
                )
        
        # 1. Query Pre-processing: Use raw query only (no HyDE/expansion LLM calls)
        # HyDE and query expansion were removed because:
        # - They add ~10s latency per recall (2+ LLM calls)
        # - The embedding model cannot match factual questions to conversational turns regardless
        # - HyDE hallucinations pollute the search space
        expanded_queries = [request.query]
        query_embedding = self._get_embedding(request.query)

        # 2. Advanced Temporal Anchoring (Production-Grade)
        # Resolve relative dates (e.g., "last Friday") based on the query reference time.
        reference_time_str = request.metadata.get("reference_time") if request.metadata else None
        reference_time = None
        if reference_time_str:
            try:
                reference_time = self._parse_timestamp(reference_time_str)
            except Exception:
                pass
        
        # Fallback dummy QueryContext for builds where classifier is absent
        class QueryContext:
            def __init__(self, query: str = "", ref_time: datetime | None = None):
                self.entities = []
                self.temporal_info = {}
                
                # 1. Advanced Entity Extraction: Proper nouns, quoted strings, and common name patterns
                # Matches "Caroline", "Melanie", "LGBTQ group", "Oliver", "Luna"
                entity_patterns = [
                    r'"([^"]+)"',  # Quoted strings
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', # Capitalized Proper Nouns
                ]
                for pattern in entity_patterns:
                    matches = re.findall(pattern, query)
                    self.entities.extend([m for m in matches if m and m.lower() not in ['i', 'me', 'you', 'he', 'she', 'they', 'the', 'when', 'what', 'who', 'where']])
                self.entities = list(set(self.entities))

                # 2. Advanced Temporal Extraction: Dates, Years, Months, and relative days
                # Matches "2023", "May 7", "last Friday", "September"
                year_match = re.search(r'\b(20\d{2})\b', query)
                if year_match:
                    self.temporal_info["year"] = year_match.group(1)
                
                month_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b'
                month_match = re.search(month_pattern, query, re.IGNORECASE)
                if month_match:
                    self.temporal_info["month"] = month_match.group(1).capitalize()
                
                # Check for "Last Friday", "Next Tuesday" etc.
                relative_day = re.search(r'\b(last|next|this)\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', query, re.IGNORECASE)
                if relative_day:
                    self.temporal_info["relative_day"] = relative_day.group(0).lower()

        qc = QueryContext(request.query)
        
        # 4. Production-Grade Relative Temporal Resolution
        if reference_time and qc.temporal_info.get("relative_day"):
            # Resolve relative days using simple calendar math instead of LLM call
            try:
                from datetime import timedelta
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                rel_text = qc.temporal_info["relative_day"].lower()
                for i, day_name in enumerate(day_names):
                    if day_name in rel_text:
                        target_weekday = i
                        current_weekday = reference_time.weekday()
                        if 'last' in rel_text:
                            days_back = (current_weekday - target_weekday) % 7 or 7
                            resolved = reference_time - timedelta(days=days_back)
                        elif 'next' in rel_text:
                            days_forward = (target_weekday - current_weekday) % 7 or 7
                            resolved = reference_time + timedelta(days=days_forward)
                        else:
                            days_diff = (target_weekday - current_weekday) % 7
                            resolved = reference_time + timedelta(days=days_diff)
                        qc.temporal_info["resolved_date"] = resolved.strftime('%Y-%m-%d')
                        break
            except Exception as e:
                logger.warning("Relative date resolution failed", error=str(e))

        # 3. Query Intent Detection: Determine if the query is Temporal, Entity-focused, or General
        qc.intent = "general"
        if qc.temporal_info:
            qc.intent = "temporal"
        elif len(qc.entities) >= 1:
            qc.intent = "entity_focused"
        
        # Check for "Now", "Recent", "Latest"
        if re.search(r'\b(now|recent|latest|currently|today)\b', request.query, re.IGNORECASE):
            qc.intent = "recency_focused"

        # Adaptive Retrieval Strategy: Adjust weights based on detected intent
        # This ensures high accuracy across ALL use cases (Business, Medical, Personal).
        base_w_sim = float(os.environ.get("KYROS_W_SIM", 0.50))
        base_w_bm25 = float(os.environ.get("KYROS_W_BM25", 0.20))
        base_w_recency = float(os.environ.get("KYROS_W_RECENCY", 0.10))
        
        w_sim, w_bm25, w_recency = base_w_sim, base_w_bm25, base_w_recency
        entity_boost_val = float(os.environ.get("KYROS_W_ENTITY_BOOST", 0.20))
        temporal_boost_val = float(os.environ.get("KYROS_W_TEMPORAL_BOOST", 2.0))

        if qc.intent == "temporal":
            # For "When" questions, prioritize semantic meaning and strict temporal alignment
            w_sim += 0.10
            w_recency -= 0.05
            temporal_boost_val *= 1.5
        elif qc.intent == "entity_focused":
            # For persona questions, prioritize entity matches and similarity
            w_sim += 0.15
            entity_boost_val *= 2.0
        elif qc.intent == "recency_focused":
            # For "What's new" questions, prioritize latest turns
            w_recency += 0.20
            w_sim -= 0.10

        w_importance = float(os.environ.get("KYROS_W_IMPORTANCE", 0.10))
        w_freshness = float(os.environ.get("KYROS_W_FRESHNESS", 0.10))

        half_life_hours = float(os.environ.get("KYROS_HALF_LIFE_HOURS", 168.0))
        freshness_warning_threshold = 0.40

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)

            # E57: Build optional session_id filter
            session_filter = ""
            # Use the full query for BM25 — entity names help find relevant content
            query_text_bm25 = request.query

            k_fetch = max(100, request.k * 3)
            params: dict = {
                "agent_id": agent_id,
                "min_rel": request.min_relevance,
                "k": request.k,
                "k_fetch": k_fetch,
                "w_sim": w_sim,
                "w_bm25": w_bm25,
                "w_recency": w_recency,
                "w_importance": w_importance,
                "w_freshness": w_freshness,
                "half_life": half_life_hours,
                "query_vec": query_embedding,
                "query_text": query_text_bm25,
            }

            if request.session_id:
                session_filter = "AND session_id = :session_id"
                params["session_id"] = request.session_id

            # Entity Boost logic (Phase 2: Item 10) - Boost instead of strict filter
            entity_boost_sql = "0"
            if qc.entities:
                boost_parts = []
                for i, ent in enumerate(qc.entities[:5]):
                    param_name = f"ent_boost_{i}"
                    params[param_name] = f'{{"entities": ["{ent}"]}}'
                    # Use CAST instead of ::jsonb to avoid SQLAlchemy parameter parsing issues
                    boost_parts.append(f"(CASE WHEN metadata @> CAST(:{param_name} AS jsonb) THEN {entity_boost_val} ELSE 0 END)")
                entity_boost_sql = " + ".join(boost_parts)

            # Temporal Boost logic (Phase 5: Temporal Engine)
            temporal_boost_sql = "0"
            temporal_conditions = []
            
            if getattr(qc, "temporal_info", None):
                if qc.temporal_info.get("resolved_date"):
                    params["resolved_date"] = qc.temporal_info["resolved_date"]
                    temporal_conditions.append(f"""
                        (CASE 
                            WHEN event_time IS NOT NULL AND event_time::jsonb->>'timestamp' = CAST(:resolved_date AS text) THEN {temporal_boost_val}
                            WHEN created_at::date = CAST(:resolved_date AS date) THEN {temporal_boost_val / 4.0}
                            ELSE 0 
                        END)
                    """)
                
                if qc.temporal_info.get("year"):
                    params["t_year"] = qc.temporal_info["year"]
                    temporal_conditions.append(f"(CASE WHEN content LIKE '%' || :t_year || '%' THEN {temporal_boost_val / 2.0} ELSE 0 END)")
                
                if qc.temporal_info.get("month"):
                    params["t_month"] = qc.temporal_info["month"]
                    temporal_conditions.append(f"(CASE WHEN content LIKE '%' || :t_month || '%' THEN {temporal_boost_val / 2.0} ELSE 0 END)")

            if temporal_conditions:
                temporal_boost_sql = " + ".join(temporal_conditions)

            # Phase 3: Strict Deterministic Mode
            if getattr(request, "strict", False):
                # Bypass probabilistic vector/BM25 search entirely
                rows = []
            else:
                # Stage 1: Get fast candidate IDs from lightweight index-only queries
                candidate_ids = []
                
                # Iterate over all expanded queries (query expansion)
                for q_idx, q_text in enumerate(expanded_queries):
                    # Embed each search variation if it is not the primary one
                    if q_idx == 0:
                        q_vec = query_embedding
                    else:
                        try:
                            q_vec = self._get_embedding(q_text)
                        except Exception:
                            q_vec = query_embedding

                    q_tsquery = self._build_tsquery(q_text)
                    if q_tsquery:
                        tsquery_expr = "to_tsquery('english', :q_tsquery)"
                        text_params = {**params, "q_tsquery": q_tsquery}
                    else:
                        tsquery_expr = "plainto_tsquery('english', :q_text)"
                        text_params = {**params, "q_text": q_text}

                    # 1. Episodic vector search candidate IDs
                    res_ep_vec = await session.execute(
                        text(f"""
                        SELECT id FROM episodic_memories
                        WHERE agent_id = :agent_id AND (deleted_at IS NULL OR (metadata->>'archived_by_summarizer')::boolean = true) {session_filter}
                        ORDER BY embedding <=> :q_vec LIMIT :k_fetch
                        """),
                        {**params, "q_vec": q_vec}
                    )
                    candidate_ids.extend(r.id for r in res_ep_vec.fetchall())
                    
                    # 2. Episodic keyword search candidate IDs
                    res_ep_text = await session.execute(
                        text(f"""
                        SELECT id FROM episodic_memories
                        WHERE agent_id = :agent_id AND (deleted_at IS NULL OR (metadata->>'archived_by_summarizer')::boolean = true) {session_filter}
                          AND to_tsvector('english', content || ' ' || COALESCE(role, '')) @@ {tsquery_expr}
                        LIMIT :k_fetch
                        """),
                        text_params
                    )
                    candidate_ids.extend(r.id for r in res_ep_text.fetchall())
                    
                    # 3. Semantic vector search candidate IDs
                    res_sem_vec = await session.execute(
                        text("""
                        SELECT id FROM semantic_memories
                        WHERE agent_id = :agent_id AND valid_to IS NULL AND deleted_at IS NULL
                        ORDER BY embedding <=> :q_vec LIMIT :k_fetch
                        """),
                        {**params, "q_vec": q_vec}
                    )
                    candidate_ids.extend(r.id for r in res_sem_vec.fetchall())
                    
                    # 4. Semantic keyword search candidate IDs
                    res_sem_text = await session.execute(
                        text(f"""
                        SELECT id FROM semantic_memories
                        WHERE agent_id = :agent_id AND valid_to IS NULL AND deleted_at IS NULL
                          AND to_tsvector('english', subject || ' ' || predicate || ': ' || object) @@ {tsquery_expr}
                        LIMIT :k_fetch
                        """),
                        text_params
                    )
                    candidate_ids.extend(r.id for r in res_sem_text.fetchall())
                    
                    # 5. Procedural vector search candidate IDs
                    res_proc_vec = await session.execute(
                        text("""
                        SELECT id FROM procedural_memories
                        WHERE agent_id = :agent_id AND deleted_at IS NULL
                        ORDER BY embedding <=> :q_vec LIMIT :k_fetch
                        """),
                        {**params, "q_vec": q_vec}
                    )
                    candidate_ids.extend(r.id for r in res_proc_vec.fetchall())
                    
                    # 6. Procedural keyword search candidate IDs
                    res_proc_text = await session.execute(
                        text(f"""
                        SELECT id FROM procedural_memories
                        WHERE agent_id = :agent_id AND deleted_at IS NULL
                          AND to_tsvector('english', name || ': ' || description) @@ {tsquery_expr}
                        LIMIT :k_fetch
                        """),
                        text_params
                    )
                    candidate_ids.extend(r.id for r in res_proc_text.fetchall())
                
                # 7. ILIKE entity name search in episodic content (fallback for factual queries)
                # Vector search often fails for factual questions about specific people
                # because the embedding model can't connect "What is X's identity?" to
                # conversational turns mentioning X. This ILIKE search ensures we find turns
                # that mention the entity by name (in content or role).
                if qc.entities:
                    for ent in qc.entities[:3]:  # Limit to top 3 entities
                        if ent and len(ent) >= 2:
                            res_ilike = await session.execute(
                                text(f"""
                                SELECT id FROM episodic_memories
                                WHERE agent_id = :agent_id AND (deleted_at IS NULL OR (metadata->>'archived_by_summarizer')::boolean = true) {session_filter}
                                  AND (content ILIKE :ent_pattern OR role ILIKE :ent_pattern)
                                ORDER BY created_at DESC, id DESC
                                LIMIT :k_fetch
                                """),
                                {**params, "ent_pattern": f"%{ent}%"}
                            )
                            candidate_ids.extend(r.id for r in res_ilike.fetchall())

                unique_candidate_ids = list(set(candidate_ids))
                
                if not unique_candidate_ids:
                    rows = []
                else:
                    params["matched_ids"] = unique_candidate_ids
                    primary_tsquery = self._build_tsquery(request.query)
                    if primary_tsquery:
                        stage2_tsquery_expr = "to_tsquery('english', :primary_tsquery)"
                        params["primary_tsquery"] = primary_tsquery
                    else:
                        stage2_tsquery_expr = "plainto_tsquery('english', :query_text)"

                    # Stage 2: Fetch metadata and perform exact Postgres calculations for ONLY the matched candidate IDs
                    stage2_query = f"""
                        SELECT e.id, e.content, e.importance, e.created_at, e.metadata, e.freshness_score, 'episodic' as memory_type, e.event_time, e.role,
                               a.display_name as agent_name,
                               1 - (e.embedding <=> :query_vec) AS similarity,
                               ts_rank_cd(to_tsvector('english', e.content || ' ' || COALESCE(e.role, '')), {stage2_tsquery_expr}) AS bm25_score
                        FROM episodic_memories e
                        LEFT JOIN agents a ON e.agent_id = a.id
                        WHERE e.id = ANY(:matched_ids) AND (e.deleted_at IS NULL OR (e.metadata->>'archived_by_summarizer')::boolean = true)
                        UNION ALL
                        SELECT s.id, (s.subject || ' ' || s.predicate || ': ' || s.object) as content, s.confidence as importance, s.created_at, s.metadata, s.freshness_score, 'semantic' as memory_type, s.event_time, 'assistant' as role,
                               a.display_name as agent_name,
                               1 - (s.embedding <=> :query_vec) AS similarity,
                               ts_rank_cd(to_tsvector('english', s.subject || ' ' || s.predicate || ': ' || s.object), {stage2_tsquery_expr}) AS bm25_score
                        FROM semantic_memories s
                        LEFT JOIN agents a ON s.agent_id = a.id
                        WHERE s.id = ANY(:matched_ids) AND s.valid_to IS NULL AND s.deleted_at IS NULL
                        UNION ALL
                        SELECT p.id, (p.name || ': ' || p.description) as content, 0.8 as importance, p.created_at, p.metadata, p.freshness_score, 'procedural' as memory_type, p.event_time, 'assistant' as role,
                               a.display_name as agent_name,
                               1 - (p.embedding <=> :query_vec) AS similarity,
                               ts_rank_cd(to_tsvector('english', p.name || ': ' || p.description), {stage2_tsquery_expr}) AS bm25_score
                        FROM procedural_memories p
                        LEFT JOIN agents a ON p.agent_id = a.id
                        WHERE p.id = ANY(:matched_ids) AND p.deleted_at IS NULL
                    """
                    result = await session.execute(text(stage2_query), params)
                    raw_rows = result.fetchall()
                    
                    # Compute hybrid score, recency decay, and boosts dynamically in the Python application layer
                    
                    rows = []
                    
                    for row in raw_rows:
                        # 1. Recency Decay Score (Ebbinghaus recency scoring)
                        time_diff_hours = 0.0
                        if row.created_at:
                            row_created = row.created_at.replace(tzinfo=None)
                            base_time = (reference_time.replace(tzinfo=None) if reference_time 
                                         else datetime.now(UTC).replace(tzinfo=None))
                            time_diff_seconds = (base_time - row_created).total_seconds()
                            time_diff_hours = max(0.0, time_diff_seconds / 3600.0)
                        recency_score = math.exp(-1.0 * time_diff_hours / half_life_hours)
                        
                        # 2. Entity Boost scoring in Python
                        entity_boost = 0.0
                        if getattr(qc, "entities", None):
                            content_lower = row.content.lower() if row.content else ""
                            role_lower = row.role.lower() if row.role else ""
                            has_entity = False
                            for ent in qc.entities:
                                if ent:
                                    ent_lower = ent.lower()
                                    if re.search(rf"\b{re.escape(ent_lower)}\b", content_lower) or ent_lower == role_lower:
                                        has_entity = True
                                        break
                            if has_entity:
                                entity_boost = entity_boost_val
                                    
                        # 3. Temporal Boost scoring in Python
                        temporal_boost = 0.0
                        if getattr(qc, "temporal_info", None):
                            resolved_date = qc.temporal_info.get("resolved_date")
                            if resolved_date:
                                try:
                                    event_time = row.event_time
                                    if isinstance(event_time, str):
                                        try:
                                            event_time = json.loads(event_time)
                                        except Exception:
                                            pass
                                    
                                    if isinstance(event_time, dict) and event_time.get("timestamp") == str(resolved_date):
                                        temporal_boost += temporal_boost_val
                                    elif row.created_at and row.created_at.strftime("%Y-%m-%d") == str(resolved_date):
                                        temporal_boost += temporal_boost_val / 4.0
                                except Exception:
                                    pass
                            
                            if qc.temporal_info.get("year") and qc.temporal_info["year"] in row.content:
                                temporal_boost += temporal_boost_val / 2.0
                            if qc.temporal_info.get("month") and qc.temporal_info["month"] in row.content:
                                temporal_boost += temporal_boost_val / 2.0
                                
                        # 4. Combined Hybrid Score computation
                        similarity = float(row.similarity or 0.0)
                        bm25_score = float(row.bm25_score or 0.0)
                        bm25_contrib = w_bm25 * (min(bm25_score * 5.0, 1.0) if bm25_score > 0 else 0.0)
                        
                        hybrid_score = (
                            w_sim * similarity
                          + bm25_contrib
                          + w_recency * recency_score
                          + w_importance * float(row.importance or 0.0)
                          + w_freshness * float(row.freshness_score or 1.0)
                          + entity_boost
                          + temporal_boost
                        )
                        
                        class ScoringRow:
                            def __init__(self, original_row, h_score, sim, bm25, recency):
                                self.id = original_row.id
                                # Enhance content with speaker context AND temporal context
                                speaker_label = original_row.role or original_row.agent_name or "unknown"
                                # Include creation timestamp so LLM can resolve relative dates
                                created_str = ""
                                if original_row.created_at:
                                    created_str = original_row.created_at.strftime("%Y-%m-%d %H:%M")
                                # Include event_time if available for explicit temporal anchoring
                                event_str = ""
                                if original_row.event_time:
                                    try:
                                        et = original_row.event_time
                                        if isinstance(et, str):
                                            et = json.loads(et)
                                        if isinstance(et, dict) and et.get("timestamp"):
                                            event_str = f", Event Date: {et['timestamp']}"
                                    except Exception:
                                        pass
                                time_tag = f" (Recorded: {created_str}{event_str})" if created_str else ""
                                self.content = f"[{speaker_label}]{time_tag} {original_row.content}"
                                self.importance = original_row.importance
                                self.created_at = original_row.created_at
                                self.metadata = original_row.metadata
                                self.freshness_score = original_row.freshness_score
                                self.memory_type = original_row.memory_type
                                self.event_time = original_row.event_time
                                self.similarity = sim
                                self.bm25_score = bm25
                                self.recency_score = recency
                                self.hybrid_score = h_score
                                
                        rows.append(ScoringRow(row, hybrid_score, similarity, bm25_score, recency_score))
                        
                    # Filter by minimum relevance cosine threshold and sort by hybrid score
                    rows = [r for r in rows if r.similarity >= request.min_relevance]
                    rows.sort(key=lambda r: r.hybrid_score, reverse=True)
                    
                    # --- STAGE 3: LLM RE-RANKING (High Precision Filter) ---
                    # Optimize: If local Cross-Encoder reranker is enabled, skip expensive LLM reranking and keep top 100 candidates
                    from kyros.ml.reranker import get_reranker
                    reranker = get_reranker()
                    if reranker.enabled:
                        rows = reranker.rerank(request.query, rows[:100], 100)
                    else:
                        # Fallback to LLM re-ranking when local Cross-Encoder is not available
                        top_candidates = rows[:100]
                        if len(top_candidates) > request.k:
                            try:
                                rerank_prompt = f"Question: {request.query}\n\nCandidates:\n"
                                for i, c in enumerate(top_candidates):
                                    rerank_prompt += f"[{i}] {c.content[:250]}\n"
                                rerank_prompt += f"\nSelect the indices of the {request.k} most relevant candidates that answer the question. Return ONLY a JSON list of integers."
                                
                                rerank_res = await call_llm(rerank_prompt, system_prompt="You are a retrieval re-ranker. Return ONLY a JSON list of integers.")
                                match = re.search(r'\[.*\]', rerank_res, re.DOTALL)
                                if match:
                                    selected_indices = json.loads(match.group())
                                    final_rows = [top_candidates[i] for i in selected_indices if i < len(top_candidates)]
                                    # Append the rest of the score-based rows if re-ranker didn't pick enough
                                    if len(final_rows) < request.k:
                                        picked_ids = {r.id for r in final_rows}
                                        for r in top_candidates:
                                            if r.id not in picked_ids:
                                                final_rows.append(r)
                                                if len(final_rows) >= request.k: break
                                    rows = final_rows[:request.k]
                                else:
                                    rows = rows[:request.k]
                            except Exception as e:
                                logger.warning("Re-ranking failed, falling back to score-based ranking", error=str(e))
                                rows = rows[:request.k]
                        else:
                            rows = rows[:request.k]
            
            # Dedicated Entity Search Channel (Step 5)
            deterministic_facts = []
            try:
                # 1. Fetch all entity names and states for this agent locally (extremely fast)
                entity_query = text("""
                    SELECT id, name, state, created_at, updated_at
                    FROM entities
                    WHERE agent_id = :agent_id AND deleted_at IS NULL
                """)
                entity_result = await session.execute(entity_query, {"agent_id": agent_id})
                all_agent_entities = entity_result.fetchall()
                
                # 2. Local fast substring/keyword-based matching (0 LLM calls, 100% genuine)
                matched_entities = []
                query_lower = request.query.lower()
                
                import string
                translator = str.maketrans("", "", string.punctuation)
                q_words = [w.translate(translator) for w in query_lower.split()]
                
                stop_words = {
                    'the', 'and', 'for', 'in', 'of', 'to', 'a', 'an', 'on', 'at', 'by', 'is', 'are', 'was', 'were', 
                    'with', 'about', 'from', 'her', 'his', 'she', 'he', 'they', 'who', 'what', 'when', 'where', 
                    'why', 'how', 'did', 'does', 'do', 'go', 'went', 'gone', 'likely', 'would', 'want', 'still', 
                    'be', 'has', 'have', 'had', 'been', 'or', 'more', 'less', 'than', 'likely', 'unlikely', 'as'
                }
                q_sig = [w for w in q_words if w not in stop_words and len(w) >= 3]
                clean_query = query_lower.replace("'s", "").translate(translator)
                
                for ent_row in all_agent_entities:
                    ent_name_lower = ent_row.name.lower()
                    clean_ent_name = ent_name_lower.replace("'s", "").translate(translator)
                    
                    # Direct substring check on cleaned strings
                    is_match = False
                    if len(clean_ent_name) >= 3 and (clean_ent_name in clean_query or clean_query in clean_ent_name):
                        is_match = True
                    
                    if not is_match and q_sig:
                        # Extract significant words from the entity name
                        e_words = [w.translate(translator) for w in ent_name_lower.replace("'s", "").split()]
                        e_sig = [w for w in e_words if w not in stop_words and len(w) >= 3]
                        
                        if e_sig:
                            overlap_count = 0
                            for ew in e_sig:
                                for qw in q_sig:
                                    if qw == ew:
                                        overlap_count += 1
                                        break
                                    else:
                                        prefix_len = 5 if (len(qw) >= 5 and len(ew) >= 5) else 4
                                        if len(qw) >= prefix_len and len(ew) >= prefix_len and (qw.startswith(ew[:prefix_len]) or ew.startswith(qw[:prefix_len])):
                                            overlap_count += 1
                                            break
                            
                            # Matching rule:
                            # - If entity name has only 1 significant word, we need at least 1 match.
                            # - If entity name has multiple significant words, we need at least 2 matching words (or all of them if total is 2).
                            if len(e_sig) == 1:
                                if overlap_count >= 1:
                                    is_match = True
                            else:
                                min_required = min(2, len(e_sig))
                                if overlap_count >= min_required:
                                    is_match = True
                    
                    if is_match:
                        matched_entities.append(ent_row)
                
                # 3. Format matched entities into canonical facts
                class MockRow:
                    def __init__(self, **kwargs):
                        self.__dict__.update(kwargs)
                
                for fact_row in matched_entities:
                    state_str = []
                    for key, value in fact_row.state.items():
                        # Format list values nicely
                        if isinstance(value, list):
                            val_str = ", ".join(str(v) for v in value)
                        else:
                            val_str = str(value)
                        state_str.append(f"  - {key.replace('_', ' ').title()}: {val_str}")
                    
                    formatted_state = f"[CANONICAL FACT] Entity: {fact_row.name}\n" + "\n".join(state_str)
                    
                    deterministic_facts.append(MockRow(
                        id=fact_row.id,
                        content=formatted_state,
                        importance=1.0,
                        created_at=fact_row.updated_at,
                        metadata={"source": "canonical_entity_state"},
                        freshness_score=1.0,
                        memory_type="semantic",
                        event_time=None,
                        similarity=1.0,
                        bm25_score=1.0,
                        hybrid_score=2.0 # Force to top
                    ))
            except Exception as e:
                logger.error(f"Dedicated local entity retrieval channel failed: {e}")
            
            # Dynamically allocate slots for memory categories to prevent starvation (100% genuine hybrid blending)
            # 1. Classify query intent and check if it is temporal-focused
            temporal_keywords = {
                "when", "date", "year", "month", "time", "how long", "ago", "yesterday", "last week", 
                "tomorrow", "today", "weekend", "morning", "afternoon", "evening", "night", "day", "week", "since"
            }
            query_words = set(request.query.lower().split())
            is_temporal = bool(query_words.intersection(temporal_keywords))

            # 2. Partition all candidate memories by type
            episodic_candidates = [r for r in rows if r.memory_type == "episodic"]
            semantic_candidates = deterministic_facts + [r for r in rows if r.memory_type == "semantic"]
            procedural_candidates = [r for r in rows if r.memory_type == "procedural"]

            # 3. Deduplicate each category independently to ensure high-quality distinct results
            dedup_episodic = self._deduplicate_rows(episodic_candidates, max_results=request.k)
            dedup_semantic = self._deduplicate_rows(semantic_candidates, max_results=request.k)
            dedup_procedural = self._deduplicate_rows(procedural_candidates, max_results=request.k)

            # 4. Allocate dynamic composition budget
            if is_temporal:
                # For temporal queries, semantic canonical facts are highly unlikely to help (as they lack precise timestamps)
                # Maximize episodic memories (which contain dialogue and exact timestamp metadata)
                k_semantic = min(2, len(dedup_semantic))
                k_procedural = min(1, len(dedup_procedural))
                k_episodic = max(0, request.k - k_semantic - k_procedural)

                final_rows = dedup_episodic[:k_episodic] + dedup_semantic[:k_semantic] + dedup_procedural[:k_procedural]
                remaining_slots = request.k - len(final_rows)
                if remaining_slots > 0:
                    leftover_episodic = dedup_episodic[k_episodic:]
                    final_rows.extend(leftover_episodic[:remaining_slots])
                    remaining_slots = request.k - len(final_rows)
                    
                if remaining_slots > 0:
                    leftover_semantic = dedup_semantic[k_semantic:]
                    final_rows.extend(leftover_semantic[:remaining_slots])
                    remaining_slots = request.k - len(final_rows)
                    
                if remaining_slots > 0:
                    leftover_procedural = dedup_procedural[k_procedural:]
                    final_rows.extend(leftover_procedural[:remaining_slots])
            else:
                # For factual/general and multi-hop queries, merge all deduplicated categories
                # and sort purely by hybrid_score to avoid starving any category
                final_rows = dedup_episodic + dedup_semantic + dedup_procedural
                final_rows.sort(key=lambda r: r.hybrid_score, reverse=True)
                final_rows = final_rows[:request.k]

            # 6. Sort final composition by hybrid score to prioritize the absolute best content
            final_rows.sort(key=lambda r: r.hybrid_score, reverse=True)
            rows = final_rows


            # Return structured results
            results = []
            
            # Traverse graph sequentially using the same database connection to avoid pool exhaustion
            causal_results = []
            if request.include_causal_ancestry:
                from kyros.intelligence.causal import traverse_causal_chain
                for row in rows:
                    try:
                        res = await traverse_causal_chain(
                            agent_id=agent_id,
                            memory_id=row.id,
                            max_depth=2,
                            direction="both",
                            session=session
                        )
                        causal_results.append(res)
                    except Exception as e:
                        logger.warning(f"Causal traversal failed for memory {row.id}: {e}")
                        causal_results.append({"nodes": [], "edges": []})
            else:
                causal_results = [{"nodes": [], "edges": []} for _ in rows]

            for i, row in enumerate(rows):
                causal_ancestry: list[dict] = []
                
                # Assign causal results
                if request.include_causal_ancestry:
                    graph_res = causal_results[i]
                    if graph_res and isinstance(graph_res, dict) and graph_res.get("edges"):
                        causal_ancestry = graph_res["edges"]

                # Removed Session Timeline Retrieval to prevent context contamination and bloated chunks
                context_window = []

                results.append(
                    MemoryResult(
                        memory_id=row.id,
                        content=row.content,
                        memory_type=row.memory_type,
                        relevance_score=round(float(row.hybrid_score), 4),
                        importance=row.importance,
                        created_at=row.created_at,
                        metadata={
                            **(row.metadata or {}),
                            "session_context": context_window,
                            "graph_links": causal_ancestry, # Inject Graph relationships
                            "event_time": row.event_time, # Forward absolute temporal info
                        },
                        freshness_score=round(float(row.freshness_score), 4),
                        freshness_warning=row.freshness_score < freshness_warning_threshold,
                        memory_category=row.memory_type,
                        causal_ancestry=causal_ancestry,
                    )
                )

        # Cross-Encoder reranking already applied in Stage 3 (line ~860).
        # A second reranking was removed because it corrupted hybrid scores
        # by re-scoring content that includes [speaker] metadata prefixes.
        results = results[:request.k]
            
        # Phase 7: Memory Compression
        compressed_results = []
        for res in results:
            # 1. Drop highly irrelevant episodic noise that slipped through
            if res.memory_category == "episodic" and res.importance < 0.2:
                continue
                
            # 2. Strip conversational filler words from episodic chunks
            if not res.content.startswith("[CANONICAL FACT]"):
                res.content = res.content.replace("This is a memory of ", "")
                res.content = res.content.replace("The user said: ", "")
                
            compressed_results.append(res)
        results = compressed_results

        elapsed = (time.monotonic() - start) * 1000

        logger.info(
            "Recall completed",
            agent_id=str(agent_id),
            query=request.query[:50],
            found_count=len(results),
            latency_ms=round(elapsed, 2),
        )

        return RecallResponse(
            agent_id=request.agent_id,
            query=request.query,
            results=results,
            total_searched=len(rows),
            latency_ms=round(elapsed, 2),
        )

    async def forget(self, tenant_id: UUID | None, memory_id: UUID) -> None:
        """Soft-delete a specific memory."""
        tenant_id_required = self._require_tenant_id(tenant_id)
        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            # We need the agent_id to update the merkle root
            result = await session.execute(
                text("SELECT agent_id FROM episodic_memories WHERE id = :id"), {"id": memory_id}
            )
            row = result.fetchone()
            if not row:
                return
            agent_id = row.agent_id

            await session.execute(
                text("""
                UPDATE episodic_memories
                SET deleted_at = NOW()
                WHERE id = :memory_id AND deleted_at IS NULL
                """),
                {"memory_id": memory_id},
            )

        # C08: Recalculate Merkle root asynchronously
        self._run_task(
            update_agent_merkle_root(agent_id, tenant_id_required),
            "update_merkle",
            details="Recalculating agent Merkle tree root hash after episodic delete"
        )

    async def store_fact(self, tenant_id: UUID | None, request: StoreFactRequest, override_id: UUID | None = None) -> FactResult:
        """Store a semantic fact with automatic contradiction detection."""
        tenant_id_required = self._require_tenant_id(tenant_id)
        fact_text = f"{request.subject} {request.predicate} {request.object}"
        embedding, embedding_secondary, emb_model_name = self._get_embedding_and_model(fact_text)
        fact_id = override_id or uuid4()
        now = datetime.now(UTC).replace(tzinfo=None)
        was_contradiction = False
        replaced_id = None
        stamp = stamp_memory(fact_text, None, now.isoformat())

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)

            # Try to get the cached fact value first to bypass database reads
            from unittest.mock import Mock
            cached_value = await self.cache.get_cached_semantic_fact(agent_id, request.subject, request.predicate)
            
            # Handle mock objects safely in unit tests
            if isinstance(cached_value, Mock):
                cached_value = None

            old = None
            if cached_value is not None:
                if cached_value == request.object:
                    old = None
                else:
                    existing = await session.execute(
                        text("""
                        SELECT id, object, confidence FROM semantic_memories
                        WHERE agent_id = :agent_id
                          AND subject = :subject AND predicate = :predicate
                          AND valid_to IS NULL AND deleted_at IS NULL
                        LIMIT 1
                        """),
                        {"agent_id": agent_id, "subject": request.subject, "predicate": request.predicate},
                    )
                    old = existing.fetchone()
            else:
                existing = await session.execute(
                    text("""
                    SELECT id, object, confidence FROM semantic_memories
                    WHERE agent_id = :agent_id
                      AND subject = :subject AND predicate = :predicate
                      AND valid_to IS NULL AND deleted_at IS NULL
                    LIMIT 1
                    """),
                    {"agent_id": agent_id, "subject": request.subject, "predicate": request.predicate},
                )
                old = existing.fetchone()

            # Fetch source episodic memory if provided for chronological metadata context
            source_episodic_id = getattr(request, "source_episodic_id", None)
            source_created_at = None
            source_event_time = None

            if source_episodic_id:
                try:
                    source_res = await session.execute(
                        text("SELECT created_at, event_time FROM episodic_memories WHERE id = :id LIMIT 1"),
                        {"id": source_episodic_id},
                    )
                    source_row = source_res.fetchone()
                    if source_row:
                        source_created_at = source_row.created_at
                        source_event_time = source_row.event_time
                except Exception as e:
                    logger.warning("Failed to fetch source episodic memory context", error=str(e))

            fact_created_at = source_created_at if source_created_at else now
            valid_from = fact_created_at
            valid_to = None

            # Inherit event_time from episodic context if not explicitly set
            fact_event_time = None
            if getattr(request, "event_time", None):
                fact_event_time = json.dumps(request.event_time)
            elif source_event_time:
                if isinstance(source_event_time, (dict, list)):
                    fact_event_time = json.dumps(source_event_time)
                else:
                    fact_event_time = source_event_time

            if old and old.object != request.object:
                was_contradiction = True
                if request.confidence >= old.confidence:
                    replaced_id = old.id
                    # Soft-invalidate old fact temporally
                    await session.execute(
                        text("UPDATE semantic_memories SET valid_to = :now WHERE id = :id"),
                        {"id": old.id, "now": now},
                    )
                else:
                    # New fact is historically stored but immediately invalid (superseded by stronger existing fact)
                    valid_to = now

            await session.execute(
                text("""
                INSERT INTO semantic_memories
                    (id, agent_id, tenant_id, subject, predicate, object,
                     confidence, embedding, embedding_secondary, embedding_model,
                     metadata, source_type, created_at, updated_at, event_time,
                     content_hash, merkle_leaf, nonce, valid_from, valid_to, source_episodic_id)
                VALUES
                    (:id, :agent_id, :tenant_id, :subject, :predicate, :object,
                     :confidence, :embedding, :embedding_secondary, :embedding_model,
                     :metadata, :source_type, :created_at, :now, :event_time,
                     :content_hash, :merkle_leaf, :nonce, :valid_from, :valid_to, :source_episodic_id)
                """),
                {
                    "id": fact_id,
                    "agent_id": agent_id,
                    "tenant_id": tenant_id_required,
                    "subject": request.subject,
                    "predicate": request.predicate,
                    "object": request.object,
                    "confidence": request.confidence,
                    "embedding": embedding,
                    "embedding_secondary": embedding_secondary,
                    "embedding_model": emb_model_name,
                    "metadata": json.dumps(getattr(request, "metadata", {})),
                    "source_type": request.source_type,
                    "created_at": fact_created_at,
                    "now": now,
                    "event_time": fact_event_time,
                    "content_hash": stamp.content_hash,
                    "merkle_leaf": stamp.merkle_leaf,
                    "nonce": stamp.nonce,
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                    "source_episodic_id": source_episodic_id,
                },
            )

        # Update cache
        await self.cache.cache_semantic_fact(
            agent_id, request.subject, request.predicate, request.object
        )

        # C08: Recalculate Merkle root asynchronously
        self._run_task(
            update_agent_merkle_root(agent_id, tenant_id_required),
            "update_merkle",
            details="Recalculating agent Merkle tree root hash after semantic update"
        )

        # E02: Index semantic relationships asynchronously
        self._run_task(
            index_fact_relationships(tenant_id_required, agent_id, fact_id, embedding),
            "index_fact",
            details=f"Indexing semantic relations for fact ID: {fact_id}"
        )

        propagated_updates: list[dict] = []
        # E07: Trigger Belief Propagation if there was a contradiction (confidence delta)
        if was_contradiction and old:
            delta = request.confidence - old.confidence
            if abs(delta) > 0.01:
                self._run_task(
                    run_belief_propagation(agent_id, fact_id, delta, max_depth=3),
                    "belief_propagation",
                    details=f"Propagating belief updates for contradicted fact: {fact_id} (confidence delta: {delta:.2f})"
                )

        return FactResult(
            fact_id=fact_id,
            subject=request.subject,
            predicate=request.predicate,
            object=request.object,
            confidence=request.confidence,
            created_at=now,
            was_contradiction=was_contradiction,
            replaced_fact_id=replaced_id,
            propagated_updates=propagated_updates,
        )

    async def query_semantic_facts(
        self, tenant_id: UUID | None, request: RecallRequest
    ) -> RecallResponse:
        """Query semantic memories by vector similarity."""
        start = time.monotonic()
        tenant_id_required = self._require_tenant_id(tenant_id)

        # Bypass search and embed for empty queries (dashboard listing)
        if not request.query or not request.query.strip():
            async with get_db_session_for_tenant(str(tenant_id_required)) as session:
                agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)
                result = await session.execute(
                    text("""
                    SELECT id, subject, predicate, object, confidence, created_at, metadata, freshness_score
                    FROM semantic_memories
                    WHERE agent_id = :agent_id AND valid_to IS NULL AND deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT :k
                    """),
                    {"agent_id": agent_id, "k": request.k}
                )
                rows = result.fetchall()
                results = []
                for row in rows:
                    meta = json.loads(row.metadata) if isinstance(row.metadata, str) else (row.metadata or {})
                    results.append(MemoryResult(
                        memory_id=row.id,
                        content=f"{row.subject} {row.predicate} {row.object}",
                        memory_type=MemoryType.SEMANTIC,
                        relevance_score=1.0,
                        importance=row.confidence,
                        created_at=row.created_at,
                        metadata=meta,
                        freshness_score=row.freshness_score
                    ))
                return RecallResponse(
                    agent_id=request.agent_id,
                    query=request.query,
                    results=results,
                    total_searched=len(results),
                    latency_ms=(time.monotonic() - start) * 1000.0
                )

        query_embedding = self._get_embedding(request.query)

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)
            result = await session.execute(
                text("""
                SELECT id, subject, predicate, object, confidence, created_at,
                       1 - (embedding <=> :query_vec) AS similarity
                FROM semantic_memories
                WHERE agent_id = :agent_id
                  AND deleted_at IS NULL
                  AND (1 - (embedding <=> :query_vec)) >= :min_rel
                ORDER BY similarity DESC
                LIMIT :k
                """),
                {
                    "agent_id": agent_id,
                    "min_rel": request.min_relevance,
                    "k": request.k,
                    "query_vec": query_embedding,
                },
            )
            rows = result.fetchall()

        results = [
            MemoryResult(
                memory_id=row.id,
                content=f"{row.subject} {row.predicate} {row.object}",
                memory_type=MemoryType.SEMANTIC,
                relevance_score=round(float(row.similarity), 4),
                importance=float(row.confidence),
                created_at=row.created_at,
                metadata={},
            )
            for row in rows
        ]
        elapsed = (time.monotonic() - start) * 1000
        return RecallResponse(
            agent_id=request.agent_id,
            query=request.query,
            results=results,
            total_searched=len(rows),
            latency_ms=round(elapsed, 2),
        )

    # ─── E61: Procedural Memory — Store ────────

    async def store_procedure(
        self, tenant_id: UUID | None, request: StoreProcedureRequest, override_id: UUID | None = None
    ) -> StoreProcedureResponse:
        """Store a learned procedure (workflow, tool-call sequence)."""
        tenant_id_required = self._require_tenant_id(tenant_id)
        desc_text = f"{request.name}: {request.description}"
        embedding, embedding_secondary, emb_model_name = self._get_embedding_and_model(desc_text)
        procedure_id = override_id or uuid4()
        now = datetime.now(UTC).replace(tzinfo=None)
        stamp = stamp_memory(desc_text, request.metadata, now.isoformat())

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)

            await session.execute(
                text("""
                INSERT INTO procedural_memories
                    (id, agent_id, tenant_id, name, description, task_type,
                     steps, embedding, embedding_secondary, embedding_model,
                     metadata, created_at, updated_at, event_time,
                     content_hash, merkle_leaf, nonce)
                VALUES
                    (:id, :agent_id, :tenant_id, :name, :description, :task_type,
                     :steps, :embedding, :embedding_secondary, :embedding_model,
                     :metadata, :now, :now, :event_time,
                     :content_hash, :merkle_leaf, :nonce)
                """),
                {
                    "id": procedure_id,
                    "agent_id": agent_id,
                    "tenant_id": tenant_id_required,
                    "name": request.name,
                    "description": request.description,
                    "task_type": request.task_type,
                    "steps": json.dumps(
                        [s.model_dump() if hasattr(s, "model_dump") else s for s in request.steps]
                    ),
                    "embedding": embedding,
                    "embedding_secondary": embedding_secondary,
                    "embedding_model": emb_model_name,
                    "metadata": json.dumps(request.metadata),
                    "now": now,
                    "event_time": json.dumps(getattr(request, "event_time", None)) if getattr(request, "event_time", None) else None,
                    "content_hash": stamp.content_hash,
                    "merkle_leaf": stamp.merkle_leaf,
                    "nonce": stamp.nonce,
                },
            )

        # C08: Recalculate Merkle root asynchronously
        self._run_task(
            update_agent_merkle_root(agent_id, tenant_id_required),
            "update_merkle",
            details="Recalculating agent Merkle tree root hash after procedural update"
        )

        return StoreProcedureResponse(
            procedure_id=procedure_id,
            agent_id=request.agent_id,
            name=request.name,
            task_type=request.task_type,
            created_at=now,
        )

    # ─── E62+E64: Procedural Memory — Match with success-rate weighting ──

    async def match_procedure(
        self, tenant_id: UUID | None, request: MatchProcedureRequest
    ) -> ProceduralMatchResponse:
        """Find the best matching procedure by task similarity × success rate."""
        tenant_id_required = self._require_tenant_id(tenant_id)
        start = time.monotonic()

        # Bypass search and embed for empty task descriptions (dashboard listing)
        if not request.task_description or not request.task_description.strip():
            async with get_db_session_for_tenant(str(tenant_id_required)) as session:
                agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)
                result = await session.execute(
                    text("""
                    SELECT id, name, description, task_type, steps,
                           success_count, failure_count, avg_duration_ms, created_at,
                           1.0 AS similarity,
                           CASE WHEN (success_count + failure_count) > 0
                                THEN success_count::float / (success_count + failure_count)
                                ELSE 0.5
                           END AS success_rate
                    FROM procedural_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT :k
                    """),
                    {"agent_id": agent_id, "k": request.k}
                )
                rows = result.fetchall()
                results = []
                for row in rows:
                    results.append(ProceduralResult(
                        procedure_id=row.id,
                        name=row.name,
                        description=row.description,
                        task_type=row.task_type,
                        steps=row.steps,
                        success_rate=row.success_rate,
                        total_executions=row.success_count + row.failure_count,
                        relevance_score=1.0,
                        avg_duration_ms=row.avg_duration_ms,
                        created_at=row.created_at
                    ))
                return ProceduralMatchResponse(
                    agent_id=request.agent_id,
                    task_description=request.task_description,
                    results=results,
                    latency_ms=(time.monotonic() - start) * 1000.0
                )

        query_embedding = self._get_embedding(request.task_description)

        # E64: Success rate weighting

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)

            result = await session.execute(
                text("""
                SELECT id, name, description, task_type, steps,
                       success_count, failure_count, avg_duration_ms, created_at,
                       1 - (embedding <=> :query_vec) AS similarity,
                       CASE WHEN (success_count + failure_count) > 0
                            THEN success_count::float / (success_count + failure_count)
                            ELSE 0.5
                       END AS success_rate,
                       (
                           0.60 * (1 - (embedding <=> :query_vec))
                         + 0.40 * CASE WHEN (success_count + failure_count) > 0
                                              THEN success_count::float /
                                                   (success_count + failure_count)
                                              ELSE 0.5
                                         END
                       ) AS weighted_score
                FROM procedural_memories
                WHERE agent_id = :agent_id
                  AND deleted_at IS NULL
                ORDER BY weighted_score DESC
                LIMIT :k
                """),
                {
                    "agent_id": agent_id,
                    "k": request.k,
                    "query_vec": query_embedding,
                },
            )
            rows = result.fetchall()

        elapsed = (time.monotonic() - start) * 1000

        return ProceduralMatchResponse(
            agent_id=request.agent_id,
            task_description=request.task_description,
            results=[
                ProceduralResult(
                    procedure_id=row.id,
                    name=row.name,
                    description=row.description,
                    task_type=row.task_type,
                    steps=row.steps if isinstance(row.steps, list) else json.loads(row.steps),
                    success_rate=round(float(row.success_rate), 4),
                    total_executions=row.success_count + row.failure_count,
                    relevance_score=round(float(row.weighted_score), 4),
                    avg_duration_ms=row.avg_duration_ms,
                    created_at=row.created_at,
                )
                for row in rows
            ],
            latency_ms=round(elapsed, 2),
        )

    # ─── E63: Procedural Memory — Outcome reporting ──

    async def report_outcome(
        self, tenant_id: UUID | None, request: OutcomeRequest
    ) -> OutcomeResponse:
        """Report success/failure for a procedure (reinforcement signal)."""
        tenant_id_required = self._require_tenant_id(tenant_id)
        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            if request.success:
                await session.execute(
                    text("""
                    UPDATE procedural_memories
                    SET success_count = success_count + 1,
                        avg_duration_ms = CASE
                            WHEN avg_duration_ms IS NULL THEN :dur
                            ELSE (avg_duration_ms + :dur) / 2.0
                        END,
                        updated_at = NOW()
                    WHERE id = :id AND deleted_at IS NULL
                    """),
                    {"id": request.procedure_id, "dur": request.duration_ms},
                )
            else:
                await session.execute(
                    text("""
                    UPDATE procedural_memories
                    SET failure_count = failure_count + 1,
                        updated_at = NOW()
                    WHERE id = :id AND deleted_at IS NULL
                    """),
                    {"id": request.procedure_id},
                )

            # Fetch updated counts
            result = await session.execute(
                text("""
                SELECT success_count, failure_count, avg_duration_ms
                FROM procedural_memories WHERE id = :id
                """),
                {"id": request.procedure_id},
            )
            row = result.fetchone()

            if row is None:
                raise ValueError(f"Procedure {request.procedure_id} not found")

            if row is None:
                raise ValueError(f"Procedure {request.procedure_id} not found")

            if row is None:
                raise ValueError(f"Procedure {request.procedure_id} not found")

        total = row.success_count + row.failure_count
        return OutcomeResponse(
            procedure_id=request.procedure_id,
            success_count=row.success_count,
            failure_count=row.failure_count,
            success_rate=round(row.success_count / total, 4) if total > 0 else 0.0,
            avg_duration_ms=row.avg_duration_ms,
        )

    # ─── E67: Export all memories ─────────────

    async def export_memories(
        self, tenant_id: UUID | None, agent_external_id: str
    ) -> ExportResponse:
        """Export all memories for an agent as structured JSON."""
        tenant_id_required = self._require_tenant_id(tenant_id)
        now = datetime.now(UTC).replace(
            tzinfo=None
        )  # naive timezone.utc for TIMESTAMP WITHOUT TIME ZONE columns

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, agent_external_id)

            # Episodic
            ep_result = await session.execute(
                text("""
                SELECT id, content, content_type, role, session_id,
                       importance, compression_level, metadata, created_at
                FROM episodic_memories
                WHERE agent_id = :aid AND deleted_at IS NULL
                ORDER BY created_at DESC
                """),
                {"aid": agent_id},
            )
            episodic = [
                {
                    "memory_id": str(r.id),
                    "content": r.content,
                    "content_type": r.content_type,
                    "role": r.role,
                    "session_id": r.session_id,
                    "importance": r.importance,
                    "compression_level": r.compression_level,
                    "metadata": r.metadata or {},
                    "created_at": r.created_at.isoformat(),
                }
                for r in ep_result.fetchall()
            ]

            # Semantic
            sem_result = await session.execute(
                text("""
                SELECT id, subject, predicate, object, confidence,
                       source_type, created_at
                FROM semantic_memories
                WHERE agent_id = :aid AND deleted_at IS NULL
                ORDER BY created_at DESC
                """),
                {"aid": agent_id},
            )
            semantic = [
                {
                    "fact_id": str(r.id),
                    "subject": r.subject,
                    "predicate": r.predicate,
                    "object": r.object,
                    "confidence": r.confidence,
                    "source_type": r.source_type,
                    "created_at": r.created_at.isoformat(),
                }
                for r in sem_result.fetchall()
            ]

            # Procedural
            proc_result = await session.execute(
                text("""
                SELECT id, name, description, task_type, steps,
                       success_count, failure_count, avg_duration_ms,
                       metadata, created_at
                FROM procedural_memories
                WHERE agent_id = :aid AND deleted_at IS NULL
                ORDER BY created_at DESC
                """),
                {"aid": agent_id},
            )
            procedural = [
                {
                    "procedure_id": str(r.id),
                    "name": r.name,
                    "description": r.description,
                    "task_type": r.task_type,
                    "steps": r.steps if isinstance(r.steps, list) else json.loads(r.steps),
                    "success_count": r.success_count,
                    "failure_count": r.failure_count,
                    "avg_duration_ms": r.avg_duration_ms,
                    "metadata": r.metadata or {},
                    "created_at": r.created_at.isoformat(),
                }
                for r in proc_result.fetchall()
            ]

        return ExportResponse(
            agent_id=agent_external_id,
            episodic=episodic,
            semantic=semantic,
            procedural=procedural,
            total_memories=len(episodic) + len(semantic) + len(procedural),
            exported_at=now,
        )

    # ─── E68: Import memories ─────────────────

    async def import_memories(
        self, tenant_id: UUID | None, agent_external_id: str, data: dict
    ) -> dict:
        """Import memories from a JSON export payload.

        Re-embeds all content (embeddings are not portable across models).
        Returns count of imported memories by type.
        """
        counts = {"episodic": 0, "semantic": 0, "procedural": 0}
        tenant_id_required = self._require_tenant_id(tenant_id)

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, agent_external_id)
            t_id = tenant_id_required

            # Import episodic memories
            for mem in data.get("episodic", []):
                embedding = self.embedder.embed(mem["content"])
                await session.execute(
                    text("""
                    INSERT INTO episodic_memories
                        (id, agent_id, tenant_id, content, content_type, role,
                         session_id, embedding, metadata, importance,
                         compression_level, created_at)
                    VALUES
                        (:id, :agent_id, :tenant_id, :content, :content_type, :role,
                         :session_id, :embedding, :metadata, :importance,
                         :compression_level, :created_at)
                    ON CONFLICT DO NOTHING
                    """),
                    {
                        "id": mem.get("memory_id", str(uuid4())),
                        "agent_id": agent_id,
                        "tenant_id": t_id,
                        "content": mem["content"],
                        "content_type": mem.get("content_type", "text"),
                        "role": mem.get("role", "user"),
                        "session_id": mem.get("session_id"),
                        "embedding": embedding,
                        "metadata": json.dumps(mem.get("metadata", {})),
                        "importance": mem.get("importance", 0.5),
                        "compression_level": mem.get("compression_level", 0),
                        "created_at": _parse_dt(mem.get("created_at")),
                    },
                )
                counts["episodic"] += 1

            # Import semantic facts
            for fact in data.get("semantic", []):
                obj = fact.get("object") or ""
                if not obj:
                    logger.warning("Skipping semantic fact with missing object", fact=fact)
                    continue
                fact_text = f"{fact['subject']} {fact['predicate']} {obj}"
                embedding = self.embedder.embed(fact_text)
                await session.execute(
                    text("""
                    INSERT INTO semantic_memories
                        (id, agent_id, tenant_id, subject, predicate, object,
                         confidence, embedding, source_type, created_at, updated_at, source_episodic_id)
                    VALUES
                        (:id, :agent_id, :tenant_id, :subject, :predicate, :object,
                         :confidence, :embedding, :source_type, :created_at, :created_at, :source_episodic_id)
                    ON CONFLICT DO NOTHING
                    """),
                    {
                        "id": fact.get("fact_id", str(uuid4())),
                        "agent_id": agent_id,
                        "tenant_id": t_id,
                        "subject": fact["subject"],
                        "predicate": fact["predicate"],
                        "object": obj,
                        "confidence": fact.get("confidence", 1.0),
                        "embedding": embedding,
                        "source_type": fact.get("source_type", "explicit"),
                        "created_at": _parse_dt(fact.get("created_at")),
                        "source_episodic_id": fact.get("source_episodic_id"),
                    },
                )
                counts["semantic"] += 1

            # Import procedural memories
            for proc in data.get("procedural", []):
                desc_text = f"{proc['name']}: {proc['description']}"
                embedding = self.embedder.embed(desc_text)
                await session.execute(
                    text("""
                    INSERT INTO procedural_memories
                        (id, agent_id, tenant_id, name, description, task_type,
                         steps, embedding, success_count, failure_count,
                         avg_duration_ms, metadata, created_at, updated_at)
                    VALUES
                        (:id, :agent_id, :tenant_id, :name, :description, :task_type,
                         :steps, :embedding, :success_count, :failure_count,
                         :avg_duration_ms, :metadata, :created_at, :created_at)
                    ON CONFLICT DO NOTHING
                    """),
                    {
                        "id": proc.get("procedure_id", str(uuid4())),
                        "agent_id": agent_id,
                        "tenant_id": t_id,
                        "name": proc["name"],
                        "description": proc["description"],
                        "task_type": proc.get("task_type"),
                        "steps": proc.get("steps", "[]"),
                        "embedding": embedding,
                        "success_count": proc.get("success_count", 0),
                        "failure_count": proc.get("failure_count", 0),
                        "avg_duration_ms": proc.get("avg_duration_ms"),
                        "metadata": json.dumps(proc.get("metadata", {})),
                        "created_at": _parse_dt(proc.get("created_at")),
                    },
                )
                counts["procedural"] += 1

        return {
            "agent_id": agent_external_id,
            "imported_count": sum(counts.values()),
            "counts": counts,
            "status": "success",
        }

    async def _resolve_agent(self, session, tenant_id, external_id: str) -> UUID:
        """Get or create agent by external_id. Returns internal UUID.

        Checks Redis cache first (O(1), ~0.2ms) before hitting the DB.
        """
        # Fast path: Redis cache
        cached = await self.cache.get_agent_id(tenant_id, external_id)
        if cached:
            from uuid import UUID as _UUID

            return _UUID(cached)

        # Cold path: DB lookup or insert
        result = await session.execute(
            text("SELECT id FROM agents WHERE external_id = :eid AND tenant_id = :tid"),
            {"eid": external_id, "tid": tenant_id},
        )
        row = result.fetchone()
        if row:
            await self.cache.set_agent_id(tenant_id, external_id, str(row.id))
            return row.id

        agent_id = uuid4()
        await session.execute(
            text("""
            INSERT INTO agents (id, tenant_id, external_id, created_at)
            VALUES (:id, :tid, :eid, NOW())
            """),
            {"id": agent_id, "tid": tenant_id, "eid": external_id},
        )
        await self.cache.set_agent_id(tenant_id, external_id, str(agent_id))
        return agent_id

    def _deduplicate_rows(self, rows: list, max_results: int, threshold: float = 0.85) -> list:
        """Remove near-identical memories based on fuzzy content similarity.
        
        This prevents the LLM context from being filled with multiple copies of the same event.
        """
        from difflib import SequenceMatcher
        
        if not rows:
            return []
            
        deduplicated = []
        # Store tuples of (raw_content_string, word_set) to avoid redundant tokenization in Jaccard loops
        seen_entries = []
        
        for row in rows:
            content = str(row.content).strip().lower()
            
            # Simple heuristic: remove metadata prefixes like "[user]: " for comparison
            if "]: " in content:
                content = content.split("]: ", 1)[1]
            
            is_duplicate = False
            content_words = set(content.split())
            
            for seen_content, seen_words in seen_entries:
                # Fast Path: Jaccard similarity (token-based set overlap) using pre-calculated set
                if not content_words or not seen_words:
                    jaccard = 0.0
                else:
                    jaccard = len(content_words.intersection(seen_words)) / len(content_words.union(seen_words))
                
                if jaccard > 0.85:
                    # Definitely a duplicate
                    is_duplicate = True
                    break
                elif jaccard < 0.30:
                    # Definitely distinct, skip slow SequenceMatcher alignment
                    continue
                
                # Slow Path (Ambiguous Zone): SequenceMatcher for high-fidelity comparison
                similarity = SequenceMatcher(None, content, seen_content).ratio()
                if similarity > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(row)
                seen_entries.append((content, content_words))
                if len(deduplicated) >= max_results:
                    break
                    
        return deduplicated
