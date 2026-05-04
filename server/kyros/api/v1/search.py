"""Unified search across all memory types."""

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError

from kyros.api.v1.deps import get_memory_service
from kyros.logging import get_logger
from kyros.schemas.memory import RecallRequest, RecallResponse

router = APIRouter()
logger = get_logger("kyros.api.search")


@router.post("/unified", response_model=RecallResponse)
async def unified_search(request: Request, body: RecallRequest) -> RecallResponse:
    """Search across episodic, semantic, and procedural memory simultaneously."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.recall(tenant_id=tenant_id, request=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in unified_search", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in unified_search", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e
