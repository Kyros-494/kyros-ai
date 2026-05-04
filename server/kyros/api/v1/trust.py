"""Trust Portal API — platform status and compliance information."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def get_trust_status() -> dict[str, any]:
    """Return the current trust and compliance status of the platform.

    Update the compliance fields to reflect your actual certification status
    before deploying to production.
    """
    return {
        "status": "operational",
        "last_updated": datetime.now(UTC).isoformat(),
        "compliance": {
            "soc2_type_1": "not_certified",
            "soc2_type_2": "not_certified",
            "hipaa": "not_certified",
            "gdpr": "self_assessed",
            "iso_27001": "not_certified",
        },
        "open_cves": [],
        "note": (
            "This is a self-hosted open-source deployment. "
            "Update compliance fields to reflect your organisation's actual certifications."
        ),
    }
