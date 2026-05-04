"""E82 — S3 archival for forgotten memories.

Soft-deleted memories can be archived to S3 for long-term recovery.
This provides a safety net: data is never truly lost, just moved
to cold storage.

Usage:
    python -m kyros.intelligence.archival

    # Or triggered after forgetting cycle
    from kyros.intelligence.archival import archive_deleted_memories
    await archive_deleted_memories()
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import UTC, datetime, timedelta

from kyros.logging import get_logger
from kyros.storage.postgres import get_db_session

logger = get_logger("kyros.intelligence.archival")

# ─── Configuration ─────────────────────────────

S3_BUCKET = os.environ.get("KYROS_ARCHIVE_BUCKET", "kyros-memory-archive")
S3_PREFIX = os.environ.get("KYROS_ARCHIVE_PREFIX", "archives/")
ARCHIVE_AFTER_DAYS = 7  # Archive memories deleted more than 7 days ago
BATCH_SIZE = 500


class S3Archiver:
    """Handles archival of deleted memories to S3."""

    def __init__(self, bucket: str = S3_BUCKET, prefix: str = S3_PREFIX) -> None:
        self.bucket = bucket
        self.prefix = prefix
        self._client = None

    def _get_client(self) -> Any:
        """Lazy-init S3 client."""
        if self._client is None:
            try:
                import boto3

                self._client = boto3.client("s3")
            except ImportError:
                logger.warning("boto3 not installed, archival will use local fallback")
                self._client = None
        return self._client

    def archive_batch(self, memories: list[dict], tenant_id: str) -> str:
        """Archive a batch of memories to S3 or local fallback.

        Args:
            memories: List of memory dicts to archive.
            tenant_id: Tenant identifier for partitioning.

        Returns:
            S3 key or local file path where the archive was stored.
        """
        timestamp = datetime.now(UTC).strftime("%Y/%m/%d/%H%M%S")
        key = f"{self.prefix}{tenant_id}/{timestamp}.jsonl"

        payload = "\n".join(json.dumps(m, default=str) for m in memories)

        client = self._get_client()
        if client:
            try:
                client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=payload.encode("utf-8"),
                    ContentType="application/x-ndjson",
                    ServerSideEncryption="AES256",
                    Metadata={
                        "tenant_id": tenant_id,
                        "memory_count": str(len(memories)),
                        "archived_at": datetime.now(UTC).isoformat(),
                    },
                )
                logger.info("Archived to S3", bucket=self.bucket, key=key, count=len(memories))
                return f"s3://{self.bucket}/{key}"
            except Exception as e:
                logger.error("S3 upload failed, using local fallback", error=str(e))

        # Local fallback: write to ./archives/
        local_dir = os.path.join("archives", tenant_id, timestamp.replace("/", os.sep))
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, "memories.jsonl")
        with open(local_path, "w") as f:
            f.write(payload)
        logger.info("Archived locally", path=local_path, count=len(memories))
        return local_path

    def recover_batch(self, key: str) -> list[dict]:
        """Recover an archived batch from S3.

        Args:
            key: S3 key or local path returned by archive_batch.

        Returns:
            List of recovered memory dicts.
        """
        if key.startswith("s3://"):
            client = self._get_client()
            if not client:
                raise RuntimeError("boto3 not available for S3 recovery")
            bucket_key = key.replace(f"s3://{self.bucket}/", "")
            resp = client.get_object(Bucket=self.bucket, Key=bucket_key)
            content = resp["Body"].read().decode("utf-8")
        else:
            with open(key) as f:
                content = f.read()

        return [json.loads(line) for line in content.strip().split("\n") if line]


async def find_archivable_memories() -> dict[str, list[dict]]:
    """Find deleted memories ready for archival, grouped by tenant."""
    from sqlalchemy import text

    cutoff = datetime.now(UTC) - timedelta(days=ARCHIVE_AFTER_DAYS)

    async with get_db_session() as session:
        result = await session.execute(
            text("""
            SELECT e.id, e.agent_id, e.tenant_id, e.content, e.content_type,
                   e.role, e.session_id, e.importance, e.metadata,
                   e.created_at, e.deleted_at
            FROM episodic_memories e
            WHERE e.deleted_at IS NOT NULL
              AND e.deleted_at < :cutoff
            ORDER BY e.tenant_id, e.created_at
            LIMIT :limit
            """),
            {"cutoff": cutoff, "limit": BATCH_SIZE},
        )

        by_tenant: dict[str, list[dict]] = {}
        for row in result.fetchall():
            tid = str(row.tenant_id)
            if tid not in by_tenant:
                by_tenant[tid] = []
            by_tenant[tid].append(
                {
                    "memory_id": str(row.id),
                    "agent_id": str(row.agent_id),
                    "content": row.content,
                    "content_type": row.content_type,
                    "role": row.role,
                    "session_id": row.session_id,
                    "importance": row.importance,
                    "metadata": row.metadata,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "deleted_at": row.deleted_at.isoformat() if row.deleted_at else None,
                }
            )

        return by_tenant


async def hard_delete_archived(memory_ids: list[str]) -> int:
    """Permanently remove archived memories from the database."""
    from sqlalchemy import text

    if not memory_ids:
        return 0

    async with get_db_session() as session:
        for mid in memory_ids:
            await session.execute(
                text("DELETE FROM episodic_memories WHERE id = :id AND deleted_at IS NOT NULL"),
                {"id": mid},
            )
    return len(memory_ids)


async def archive_deleted_memories() -> None:
    """Run one archival cycle: find deleted → S3 → hard delete."""
    start = time.monotonic()
    logger.info("Starting archival cycle")

    archiver = S3Archiver()
    by_tenant = await find_archivable_memories()
    total_archived = 0

    for tenant_id, memories in by_tenant.items():
        try:
            archive_key = archiver.archive_batch(memories, tenant_id)
            memory_ids = [m["memory_id"] for m in memories]
            await hard_delete_archived(memory_ids)
            total_archived += len(memories)
            logger.info(
                "Tenant archived",
                tenant_id=tenant_id,
                count=len(memories),
                archive=archive_key,
            )
        except Exception as e:
            logger.error("Archival failed", tenant_id=tenant_id, error=str(e))

    elapsed = (time.monotonic() - start) * 1000
    logger.info(
        "Archival cycle complete",
        total_archived=total_archived,
        tenants=len(by_tenant),
        latency_ms=round(elapsed, 2),
    )
    return total_archived


# ─── CLI Entry Point ─────────────────────────

if __name__ == "__main__":
    asyncio.run(archive_deleted_memories())
