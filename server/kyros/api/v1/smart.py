"""Unified Smart API Gateway - Consolidated Ingestion and Recall."""

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError

from kyros.api.v1.deps import get_memory_service
from kyros.logging import get_logger
from kyros.schemas.memory import (
    RecallRequest,
    RecallResponse,
    RememberRequest,
    RememberResponse,
)

router = APIRouter()
logger = get_logger("kyros.api.smart")


@router.post("/remember", response_model=RememberResponse, status_code=201)
async def smart_remember(request: Request, body: RememberRequest) -> RememberResponse:
    """Smart Ingestion Gateway: Ingests raw turn into episodic memories,

    while automatically extracting and writing bitemporal semantic facts and
    causal edges asynchronously in the background.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.remember_episodic(tenant_id=tenant_id, request=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in smart_remember", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in smart_remember", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/recall", response_model=RecallResponse)
async def smart_recall(request: Request, body: RecallRequest) -> RecallResponse:
    """Smart Retrieval Gateway: Searches across episodic, semantic, and procedural

    memories concurrently using query classification, freshness decay, and
    local Cross-Encoder reranking.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.recall(tenant_id=tenant_id, request=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in smart_recall", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in smart_recall", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e
