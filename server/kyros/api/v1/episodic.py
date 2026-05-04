"""Episodic memory routes — store, recall, and forget conversation history."""

from uuid import UUID

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
logger = get_logger("kyros.api.episodic")


@router.post("/remember", response_model=RememberResponse, status_code=201)
async def remember(request: Request, body: RememberRequest) -> RememberResponse:
    """Store an episodic memory (conversation turn, action, observation)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.remember_episodic(tenant_id=tenant_id, request=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in remember", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in remember", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/recall", response_model=RecallResponse)
async def recall(request: Request, body: RecallRequest) -> RecallResponse:
    """Retrieve relevant episodic memories via semantic search."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.recall(tenant_id=tenant_id, request=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in recall", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in recall", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.delete("/{memory_id}", status_code=204)
async def forget(memory_id: UUID, request: Request) -> None:
    """Soft-delete a specific episodic memory."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        await service.forget(tenant_id=tenant_id, memory_id=memory_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in forget", memory_id=str(memory_id), error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in forget", memory_id=str(memory_id), error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e
