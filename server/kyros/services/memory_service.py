"""Core memory service — business logic for all memory operations."""

import asyncio
import json
import os
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
from kyros.intelligence.integrity import stamp_memory
from kyros.intelligence.integrity_service import update_agent_merkle_root
from kyros.logging import get_logger
from kyros.ml.embedder import EmbeddingModel
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


class MemoryService:
    """Orchestrates memory operations across storage, cache, and ML layers."""

    def __init__(self, embedder: EmbeddingModel, cache: MemoryCache) -> None:
        self.embedder = embedder
        self.cache = cache

    @staticmethod
    def _require_tenant_id(tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise ValueError("tenant_id is required for memory operations")
        return tenant_id

    def _run_task(self, coro: Any, name: str) -> asyncio.Task[Any]:
        """Helper to run a fire-and-forget task with error logging.

        Uses the global tracked task registry from main.py when available
        so tasks are properly cancelled on shutdown.
        """
        try:
            from kyros.main import create_background_task

            return create_background_task(coro)
        except ImportError:
            pass

        task = asyncio.create_task(coro)

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

    async def remember_episodic(
        self, tenant_id: UUID | None, request: RememberRequest, override_id: UUID | None = None
    ) -> RememberResponse:
        """Store an episodic memory: embed content → write DB → update cache."""
        embedding, embedding_secondary = self.embedder.embed_with_secondary(request.content)
        memory_id = override_id or uuid4()
        now = self._parse_timestamp(request.timestamp)

        stamp = stamp_memory(request.content, request.metadata, now.isoformat())
        tenant_id_required = self._require_tenant_id(tenant_id)

        # Autonomous Temporal Extraction (Phase 5)
        from kyros.proxy.classifier import extract_temporal_info
        event_time_str = json.dumps(request.event_time) if request.event_time else None
        if not event_time_str:
            extracted_time = extract_temporal_info(request.content, reference_time=now)
            if extracted_time and "resolved_date" in extracted_time:
                event_time_str = json.dumps({"timestamp": extracted_time["resolved_date"], "relative": extracted_time.get("relative_day")})

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)

            await session.execute(
                text("""
                INSERT INTO episodic_memories
                    (id, agent_id, tenant_id, content, content_type, role,
                     session_id, embedding, embedding_secondary, embedding_model,
                     metadata, importance, created_at, event_time,
                     content_hash, merkle_leaf, nonce)
                VALUES
                    (:id, :agent_id, :tenant_id, :content, :content_type, :role,
                     :session_id, :embedding, :embedding_secondary, :embedding_model,
                     :metadata, :importance, :created_at, :event_time,
                     :content_hash, :merkle_leaf, :nonce)
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
                    "embedding_model": self.embedder.model_name,
                    "metadata": json.dumps(request.metadata),
                    "importance": request.importance,
                    "created_at": now,
                    "event_time": event_time_str,
                    "content_hash": stamp.content_hash,
                    "merkle_leaf": stamp.merkle_leaf,
                    "nonce": stamp.nonce,
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
        self._run_task(update_agent_merkle_root(agent_id, tenant_id_required), "update_merkle")

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
            )

        # D04: Asynchronously extract implicit causal relationships using LLM
        if recent_memories and (
            os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        ):
            self._run_task(
                extract_and_store_causal_edges(
                    tenant_id_required, agent_id, memory_id, request.content, recent_memories
                ),
                "extract_causal",
            )

        # E01: Asynchronously extract and store structured semantic facts (Knowledge Graph)
        from kyros.intelligence.semantic import extract_and_store_semantic_facts
        self._run_task(
            extract_and_store_semantic_facts(
                tenant_id_required, agent_id, memory_id, request.content
            ),
            "extract_semantic"
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
        start = time.monotonic()
        tenant_id_required = self._require_tenant_id(tenant_id)
        query_embedding = self.embedder.embed(request.query)

        # Classify query to adjust retrieval weights
        from kyros.proxy.query_classifier import QueryType, classify_query
        qc = classify_query(request.query)

        if qc.query_type == QueryType.TEMPORAL:
            # Temporal queries: boost recency heavily
            w_sim = 0.30
            w_bm25 = 0.15
            w_recency = 0.35
            w_importance = 0.10
            w_freshness = 0.10
        elif qc.query_type == QueryType.FACTUAL:
            # Factual queries: boost similarity and BM25 (semantic match + keyword hit)
            w_sim = 0.45
            w_bm25 = 0.30
            w_recency = 0.05
            w_importance = 0.15
            w_freshness = 0.05
        elif qc.query_type == QueryType.PROCEDURAL:
            # Procedural queries: balanced with importance boost
            w_sim = 0.35
            w_bm25 = 0.20
            w_recency = 0.10
            w_importance = 0.25
            w_freshness = 0.10
        else:
            # Default balanced weights
            w_sim = 0.40
            w_bm25 = 0.20
            w_recency = 0.15
            w_importance = 0.15
            w_freshness = 0.10

        half_life_hours = 168.0
        freshness_warning_threshold = 0.40

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)

            # E57: Build optional session_id filter
            session_filter = ""
            query_text_bm25 = request.query
            if getattr(qc, "expanded_keywords", None):
                query_text_bm25 += " " + " ".join(qc.expanded_keywords)

            params: dict = {
                "agent_id": agent_id,
                "min_rel": request.min_relevance,
                "k": request.k,
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
                    boost_parts.append(f"(CASE WHEN metadata @> CAST(:{param_name} AS jsonb) THEN 0.2 ELSE 0 END)")
                entity_boost_sql = " + ".join(boost_parts)

            # Temporal Boost logic (Phase 5: Temporal Engine)
            temporal_boost_sql = "0"
            if getattr(qc, "temporal_info", None) and qc.temporal_info.get("resolved_date"):
                params["resolved_date"] = qc.temporal_info["resolved_date"]
                temporal_boost_sql = """
                    (CASE 
                        WHEN event_time IS NOT NULL AND event_time::jsonb->>'timestamp' = CAST(:resolved_date AS text) THEN 2.0
                        WHEN created_at::date = CAST(:resolved_date AS date) THEN 0.5
                        ELSE 0 
                    END)
                """

            # B08: Hybrid search with freshness-weighted ranking across all memory types
            query = f"""
                WITH ep_vector AS (
                    SELECT id, content, importance, created_at, metadata, freshness_score, 'episodic' as memory_type, embedding, event_time
                    FROM episodic_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL {session_filter}
                    ORDER BY embedding <=> :query_vec LIMIT :k_fetch
                ),
                ep_text AS (
                    SELECT id, content, importance, created_at, metadata, freshness_score, 'episodic' as memory_type, embedding, event_time
                    FROM episodic_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL {session_filter}
                      AND to_tsvector('english', content) @@ plainto_tsquery('english', :query_text)
                    ORDER BY ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', :query_text)) DESC LIMIT :k_fetch
                ),
                sem_vector AS (
                    SELECT id, (subject || ' ' || predicate || ': ' || object) as content, confidence as importance, created_at, '{{}}'::jsonb as metadata, freshness_score, 'semantic' as memory_type, embedding, NULL::jsonb as event_time
                    FROM semantic_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL
                    ORDER BY embedding <=> :query_vec LIMIT :k_fetch
                ),
                sem_text AS (
                    SELECT id, (subject || ' ' || predicate || ': ' || object) as content, confidence as importance, created_at, '{{}}'::jsonb as metadata, freshness_score, 'semantic' as memory_type, embedding, NULL::jsonb as event_time
                    FROM semantic_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL
                      AND to_tsvector('english', subject || ' ' || predicate || ': ' || object) @@ plainto_tsquery('english', :query_text)
                    ORDER BY ts_rank_cd(to_tsvector('english', subject || ' ' || predicate || ': ' || object), plainto_tsquery('english', :query_text)) DESC LIMIT :k_fetch
                ),
                proc_vector AS (
                    SELECT id, (name || ': ' || description) as content, 0.8 as importance, created_at, metadata, freshness_score, 'procedural' as memory_type, embedding, NULL::jsonb as event_time
                    FROM procedural_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL
                    ORDER BY embedding <=> :query_vec LIMIT :k_fetch
                ),
                proc_text AS (
                    SELECT id, (name || ': ' || description) as content, 0.8 as importance, created_at, metadata, freshness_score, 'procedural' as memory_type, embedding, NULL::jsonb as event_time
                    FROM procedural_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL
                      AND to_tsvector('english', name || ': ' || description) @@ plainto_tsquery('english', :query_text)
                    ORDER BY ts_rank_cd(to_tsvector('english', name || ': ' || description), plainto_tsquery('english', :query_text)) DESC LIMIT :k_fetch
                ),
                all_memories AS (
                    SELECT * FROM ep_vector
                    UNION SELECT * FROM ep_text
                    UNION SELECT * FROM sem_vector
                    UNION SELECT * FROM sem_text
                    UNION SELECT * FROM proc_vector
                    UNION SELECT * FROM proc_text
                )
                SELECT id, content, importance, created_at, metadata, 
                       freshness_score, memory_type, event_time,
                       1 - (embedding <=> :query_vec) AS similarity,
                       ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', :query_text)) AS bm25_score,
                       (
                           :w_sim * (1 - (embedding <=> :query_vec))
                         + :w_bm25 * (
                               CASE 
                                   WHEN ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', :query_text)) > 0 
                                   THEN LEAST(ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', :query_text)) * 5.0, 1.0)
                                   ELSE 0 
                               END
                           )
                         + :w_recency * EXP(
                               -1.0 * EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600.0 
                               / :half_life
                           )
                         + :w_importance * importance
                         + :w_freshness * freshness_score
                         + {entity_boost_sql}
                         + {temporal_boost_sql}
                       ) AS hybrid_score
                FROM all_memories
                WHERE (1 - (embedding <=> :query_vec)) >= :min_rel
                ORDER BY hybrid_score DESC
                LIMIT :k_fetch
            """

            # Over-fetch 3x to allow deduplication headroom
            params["k_fetch"] = request.k * 3

            # Phase 3: Strict Deterministic Mode
            if request.strict:
                # Bypass probabilistic vector/BM25 search entirely
                rows = []
            else:
                result = await session.execute(text(query), params)
                rows = result.fetchall()
            
            # Deterministic Canonical Fact Store Injection
            # Resolves "No canonical fact store" & "No structured entity state"
            deterministic_facts = []
            if qc.entities:
                entities_str = [ent.lower() for ent in qc.entities]
                # Fetch Entity State (O(1) JSONB Retrieval)
                entity_query = text("""
                    SELECT id, name, state, created_at, updated_at
                    FROM entities
                    WHERE agent_id = :agent_id
                    AND LOWER(name) = ANY(:entities)
                """)
                entity_result = await session.execute(entity_query, {
                    "agent_id": agent_id,
                    "entities": entities_str
                })
                
                class MockRow:
                    def __init__(self, **kwargs):
                        self.__dict__.update(kwargs)
                        
                for fact_row in entity_result.fetchall():
                    # Format the JSONB state into a readable block for the LLM
                    state_str = []
                    for key, value in fact_row.state.items():
                        state_str.append(f"  - {key.replace('_', ' ').title()}: {value}")
                    
                    formatted_state = f"[CANONICAL FACT] Entity: {fact_row.name}\n" + "\n".join(state_str)
                    
                    # Create a mock row that perfectly mirrors the Hybrid Search output
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
            
            # Inject deterministic facts before deduplication
            rows = deterministic_facts + list(rows)

            # Deduplicate near-identical memories before building results
            rows = self._deduplicate_rows(rows, max_results=request.k)

            # Return structured results
            results = []
            
            # Prepare graph traversal tasks for concurrent execution
            causal_tasks = []
            if request.include_causal_ancestry:
                from kyros.intelligence.causal import traverse_causal_chain
                import asyncio
                for row in rows:
                    causal_tasks.append(
                        traverse_causal_chain(
                            agent_id=agent_id, memory_id=row.id, max_depth=2, direction="both"
                        )
                    )
            else:
                for _ in rows:
                    causal_tasks.append(asyncio.sleep(0)) # No-op dummy tasks

            # Wait for all graph traversals concurrently (they manage their own DB sessions)
            causal_results = await asyncio.gather(*causal_tasks, return_exceptions=True)

            for i, row in enumerate(rows):
                causal_ancestry: list[dict] = []
                
                # Assign causal results from concurrent tasks
                if request.include_causal_ancestry:
                    graph_res = causal_results[i]
                    if not isinstance(graph_res, Exception) and graph_res and graph_res.get("edges"):
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

        # Apply Cross-Encoder Reranking
        try:
            from kyros.ml.reranker import get_reranker
            reranker = get_reranker()
            results = reranker.rerank(request.query, results, top_k=request.k)
        except Exception as e:
            logger.warning(f"Reranking skipped or failed: {e}")
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
        self._run_task(update_agent_merkle_root(agent_id, tenant_id_required), "update_merkle")

    async def store_fact(self, tenant_id: UUID | None, request: StoreFactRequest, override_id: UUID | None = None) -> FactResult:
        """Store a semantic fact with automatic contradiction detection."""
        tenant_id_required = self._require_tenant_id(tenant_id)
        fact_text = f"{request.subject} {request.predicate} {request.object}"
        embedding, embedding_secondary = self.embedder.embed_with_secondary(fact_text)
        fact_id = override_id or uuid4()
        now = datetime.now(UTC).replace(tzinfo=None)
        was_contradiction = False
        replaced_id = None
        stamp = stamp_memory(fact_text, None, now.isoformat())

        async with get_db_session_for_tenant(str(tenant_id_required)) as session:
            agent_id = await self._resolve_agent(session, tenant_id_required, request.agent_id)

            existing = await session.execute(
                text("""
                SELECT id, object, confidence FROM semantic_memories
                WHERE agent_id = :agent_id
                  AND subject = :subject AND predicate = :predicate
                  AND deleted_at IS NULL
                LIMIT 1
                """),
                {"agent_id": agent_id, "subject": request.subject, "predicate": request.predicate},
            )
            old = existing.fetchone()

            if old and old.object != request.object:
                was_contradiction = True
                if request.confidence >= old.confidence:
                    replaced_id = old.id
                    await session.execute(
                        text("UPDATE semantic_memories SET deleted_at = NOW() WHERE id = :id"),
                        {"id": old.id},
                    )

            await session.execute(
                text("""
                INSERT INTO semantic_memories
                    (id, agent_id, tenant_id, subject, predicate, object,
                     confidence, embedding, embedding_secondary, embedding_model,
                     source_type, created_at, updated_at, event_time,
                     content_hash, merkle_leaf, nonce)
                VALUES
                    (:id, :agent_id, :tenant_id, :subject, :predicate, :object,
                     :confidence, :embedding, :embedding_secondary, :embedding_model,
                     :source_type, :now, :now, :event_time,
                     :content_hash, :merkle_leaf, :nonce)
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
                    "embedding_model": self.embedder.model_name,
                    "source_type": request.source_type,
                    "now": now,
                    "event_time": json.dumps(request.event_time) if request.event_time else None,
                    "content_hash": stamp.content_hash,
                    "merkle_leaf": stamp.merkle_leaf,
                    "nonce": stamp.nonce,
                },
            )

        # Update cache
        await self.cache.cache_semantic_fact(
            agent_id, request.subject, request.predicate, request.object
        )

        # C08: Recalculate Merkle root asynchronously
        self._run_task(update_agent_merkle_root(agent_id, tenant_id_required), "update_merkle")

        # E02: Index semantic relationships asynchronously
        self._run_task(
            index_fact_relationships(tenant_id_required, agent_id, fact_id, embedding),
            "index_fact",
        )

        propagated_updates: list[dict] = []
        # E07: Trigger Belief Propagation if there was a contradiction (confidence delta)
        if was_contradiction and old:
            delta = request.confidence - old.confidence
            if abs(delta) > 0.01:
                try:
                    propagated_updates = await run_belief_propagation(agent_id, fact_id, delta)
                except Exception:
                    pass  # propagation is best-effort

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
        query_embedding = self.embedder.embed(request.query)

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
        embedding, embedding_secondary = self.embedder.embed_with_secondary(desc_text)
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
                    "embedding_model": self.embedder.model_name,
                    "metadata": json.dumps(request.metadata),
                    "now": now,
                    "event_time": json.dumps(request.event_time) if request.event_time else None,
                    "content_hash": stamp.content_hash,
                    "merkle_leaf": stamp.merkle_leaf,
                    "nonce": stamp.nonce,
                },
            )

        # C08: Recalculate Merkle root asynchronously
        self._run_task(update_agent_merkle_root(agent_id, tenant_id_required), "update_merkle")

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
        query_embedding = self.embedder.embed(request.task_description)

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
                         confidence, embedding, source_type, created_at, updated_at)
                    VALUES
                        (:id, :agent_id, :tenant_id, :subject, :predicate, :object,
                         :confidence, :embedding, :source_type, :created_at, :created_at)
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
        seen_contents = []
        
        for row in rows:
            content = str(row.content).strip().lower()
            
            # Simple heuristic: remove metadata prefixes like "[user]: " for comparison
            if "]: " in content:
                content = content.split("]: ", 1)[1]
            
            is_duplicate = False
            for seen in seen_contents:
                # SequenceMatcher is slower than set lookup but handles small variations
                similarity = SequenceMatcher(None, content, seen).ratio()
                if similarity > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(row)
                seen_contents.append(content)
                if len(deduplicated) >= max_results:
                    break
                    
        return deduplicated
