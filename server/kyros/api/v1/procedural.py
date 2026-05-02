"""Procedural memory routes — store, match, and track learned workflows."""

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError

from kyros.api.v1.deps import get_memory_service
from kyros.logging import get_logger
from kyros.schemas.memory import (
    MatchProcedureRequest,
    OutcomeRequest,
    OutcomeResponse,
    ProceduralMatchResponse,
    StoreProcedureRequest,
    StoreProcedureResponse,
)

router = APIRouter()
logger = get_logger("kyros.api.procedural")


@router.post("/store", status_code=201, response_model=StoreProcedureResponse)
async def store_procedure(request: Request, body: StoreProcedureRequest):
    """Store a learned procedure (workflow, tool-call sequence)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.store_procedure(tenant_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        logger.error("DB error in store_procedure", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")
    except Exception as e:
        logger.error("Unexpected error in store_procedure", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/match", response_model=ProceduralMatchResponse)
async def match_procedure(request: Request, body: MatchProcedureRequest):
    """Find the best matching procedure for a task description.

    Results are ranked by: 0.60 × cosine_similarity + 0.40 × success_rate
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.match_procedure(tenant_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        logger.error("DB error in match_procedure", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")
    except Exception as e:
        logger.error("Unexpected error in match_procedure", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/outcome", response_model=OutcomeResponse)
async def report_outcome(request: Request, body: OutcomeRequest):
    """Report success/failure for a procedure (reinforcement signal)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.report_outcome(tenant_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        logger.error("DB error in report_outcome", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")
    except Exception as e:
        logger.error("Unexpected error in report_outcome", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
