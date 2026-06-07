"""Entity Resolution Engine.

Extracts named entities from conversational text using LLM calls, resolves them
against the database, and maintains a unified, canonical entity state using JSONB.
"""

from __future__ import annotations

import json
from datetime import datetime
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from kyros.logging import get_logger
from kyros.ml.models import call_llm
from kyros.storage.postgres import get_db_session

logger = get_logger("kyros.entity_resolver")

# Global callback for tracing (used by benchmarks)
_entity_trace_callback = None

def set_entity_trace_callback(callback):
    global _entity_trace_callback
    _entity_trace_callback = callback

ENTITY_EXTRACTION_PROMPT = """
You are a domain-agnostic Entity and Knowledge Extraction Engine.
Analyze the text and extract every significant Entity, Attribute, and Relationship.

CRITICAL INSTRUCTIONS:
1. UNIVERSAL ENTITY EXTRACTION: Extract People, Organizations, Locations, Objects, Concepts, and Specialized Terms (e.g. Medical conditions, Business projects, Legal terms).
2. DYNAMIC ATTRIBUTE DISCOVERY: Capture ANY key-value fact. (e.g. "Status: Completed", "Symptom: Fever", "Hobby: Painting").
3. TEMPORAL ANCHORING: Link facts to specific dates, times, or relative durations mentioned in the context.
4. RELATIONSHIP MAPPING: Map how entities interact (e.g. "Subject A reports to Subject B", "Entity C is part of Organization D").
5. GRANULARITY: Extract minor details that define a persona or situation (e.g. specific preferences, past experiences, or unique identifiers).
6. SPEAKER ATTRIBUTION: The text may be prefixed with [Speaker: Name]. When the speaker uses first-person pronouns (e.g., "I", "my", "me"), attribute those actions, properties, or relationships directly to the Speaker entity (e.g., "Melanie") instead of creating an entity named "I" or "Speaker".

Input Text:
{text}

Return ONLY a JSON list of objects. No markdown.

Format:
[
  {{
    "name": "EntityName",
    "type": "Person|Org|Place|Concept|Object|Other",
    "properties": {{
      "key1": "value1",
      "key2": ["list", "of", "values"],
      "temporal_context": "When this fact was true",
      "relationships": {{"type": "TargetEntity"}}
    }}
  }}
]
"""


async def extract_entities(text_content: str) -> list[dict[str, Any]]:
    """Extract named entities and their properties from content using LLM."""
    if not text_content or not text_content.strip():
        return []

    prompt = ENTITY_EXTRACTION_PROMPT.format(text=text_content)
    try:
        response_text = await call_llm(prompt, temperature=0.1)
        if not response_text or not response_text.strip():
            logger.warning("Entity extraction returned an empty response")
            return []

        cleaned = response_text.strip()
        
        # Robust JSON extraction: look for the first [ and last ]
        import re
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group()
        elif cleaned.startswith("```"):
            # Fallback to the old cleaning method if regex fails but it looks like markdown
            cleaned = cleaned.split("```", 2)[-1] if cleaned.count("```") >= 2 else cleaned
            cleaned = cleaned.removeprefix("json").strip().strip("`").strip()

        try:
            entities = json.loads(cleaned)
            if isinstance(entities, list):
                return entities
        except json.JSONDecodeError:
            # If standard JSON parsing fails, try to fix common LLM JSON errors (like trailing commas)
            try:
                # Remove trailing commas in arrays/objects
                cleaned_fixed = re.sub(r',\s*([\]}])', r'\1', cleaned)
                entities = json.loads(cleaned_fixed)
                if isinstance(entities, list):
                    return entities
            except Exception:
                pass
            
            logger.warning("Entity extraction returned non-JSON response", error_raw=response_text[:200])
            
    except Exception as e:
        logger.error("Failed to extract entities", error=str(e))
    return []


async def resolve_and_update_entities(
    agent_id: UUID,
    text_content: str,
) -> list[dict[str, Any]]:
    """Extract entities from the text, resolve them against DB, and update/insert records.

    Performs dynamic JSONB property state merging.
    """
    extracted = await extract_entities(text_content)
    if not extracted:
        return []

    resolved_entities = []
    now = datetime.now(UTC).replace(tzinfo=None)

    async with get_db_session() as session:
        for ent in extracted:
            name = ent.get("name", "").strip()
            if not name:
                continue

            properties = ent.get("properties", {})
            canonical_name = ent.get("canonical_name", name).strip()

            try:
                # 1. Look up existing entity case-insensitively
                result = await session.execute(
                    text("""
                    SELECT id, name, canonical_name, state
                    FROM entities
                    WHERE agent_id = :agent_id
                      AND (LOWER(name) = LOWER(:name) OR LOWER(canonical_name) = LOWER(:name))
                      AND deleted_at IS NULL
                    LIMIT 1
                    """),
                    {"agent_id": agent_id, "name": name},
                )
                row = result.fetchone()

                if row:
                    # Resolve to existing and merge properties
                    entity_id = row.id
                    existing_state = dict(row.state or {})
                    # Merge logic (new overrides old where present)
                    merged_state = {**existing_state, **properties}

                    await session.execute(
                        text("""
                        UPDATE entities
                        SET state = :state, updated_at = :now, canonical_name = :canonical_name
                        WHERE id = :id
                        """),
                        {
                            "id": entity_id,
                            "state": json.dumps(merged_state),
                            "canonical_name": canonical_name,
                            "now": now,
                        },
                    )
                    logger.info(
                        "Resolved and updated existing entity",
                        entity_id=str(entity_id),
                        name=name,
                    )
                    print(f"      [ENTITY] Resolved and updated: {name} | Properties: {properties}")
                    if _entity_trace_callback:
                        _entity_trace_callback("ENTITY_UPDATE", f"Updated entity: {name}", {"entity_id": str(entity_id), "properties": properties})
                    resolved_entities.append(
                        {
                            "entity_id": str(entity_id),
                            "name": name,
                            "canonical_name": canonical_name,
                            "state": merged_state,
                            "status": "updated",
                        }
                    )
                else:
                    # Create or update entity (handle race conditions with ON CONFLICT)
                    entity_id = uuid4()
                    # First try insert with ON CONFLICT DO NOTHING
                    insert_result = await session.execute(
                        text("""
                        INSERT INTO entities (id, agent_id, name, canonical_name, state, created_at, updated_at)
                        VALUES (:id, :agent_id, :name, :canonical_name, :state, :now, :now)
                        ON CONFLICT ON CONSTRAINT uq_entity_agent_name DO NOTHING
                        RETURNING id
                        """),
                        {
                            "id": entity_id,
                            "agent_id": agent_id,
                            "name": name,
                            "canonical_name": canonical_name,
                            "state": json.dumps(properties),
                            "now": now,
                        },
                    )
                    inserted_id = insert_result.scalar()
                    
                    if inserted_id:
                        # Successfully inserted new entity
                        logger.info("Created new canonical entity", entity_id=str(inserted_id), name=name)
                        print(f"      [ENTITY] Created new entity: {name} | Properties: {properties}")
                        if _entity_trace_callback:
                            _entity_trace_callback("ENTITY_CREATE", f"Created entity: {name}", {"entity_id": str(inserted_id), "properties": properties})
                        resolved_entities.append(
                            {
                                "entity_id": str(inserted_id),
                                "name": name,
                                "canonical_name": canonical_name,
                                "state": properties,
                                "status": "created",
                            }
                        )
                    else:
                        # Insert failed due to conflict, fetch existing entity and update it
                        result = await session.execute(
                            text("""
                            SELECT id, name, canonical_name, state
                            FROM entities
                            WHERE agent_id = :agent_id
                              AND name = :name
                              AND deleted_at IS NULL
                            LIMIT 1
                            """),
                            {"agent_id": agent_id, "name": name},
                        )
                        row = result.fetchone()
                        if row:
                            # Resolve to existing and merge properties
                            existing_entity_id = row.id
                            existing_state = dict(row.state or {})
                            merged_state = {**existing_state, **properties}
                            
                            await session.execute(
                                text("""
                                UPDATE entities
                                SET state = :state, updated_at = :now, canonical_name = :canonical_name
                                WHERE id = :id
                                """),
                                {
                                    "id": existing_entity_id,
                                    "state": json.dumps(merged_state),
                                    "canonical_name": canonical_name,
                                    "now": now,
                                },
                            )
                            logger.info(
                                "Resolved and updated existing entity (after conflict)",
                                entity_id=str(existing_entity_id),
                                name=name,
                            )
                            print(f"      [ENTITY] Resolved and updated: {name} | Properties: {properties}")
                            if _entity_trace_callback:
                                _entity_trace_callback("ENTITY_UPDATE", f"Updated entity: {name}", {"entity_id": str(existing_entity_id), "properties": properties})
                            resolved_entities.append(
                                {
                                    "entity_id": str(existing_entity_id),
                                    "name": name,
                                    "canonical_name": canonical_name,
                                    "state": merged_state,
                                    "status": "updated",
                                }
                            )
            except Exception as e:
                logger.error("Failed to resolve entity", error=str(e), name=name)
                print(f"      [ENTITY ERROR] Failed to process {name}: {e}")
                if _entity_trace_callback:
                    _entity_trace_callback("ENTITY_ERROR", f"Failed to process {name}", {"error": str(e)})

    return resolved_entities
