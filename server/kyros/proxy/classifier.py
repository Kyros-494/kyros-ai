from datetime import datetime
from typing import Any

def extract_temporal_info(content: str, reference_time: datetime | None = None) -> dict[str, Any] | None:
    """Fallback implementation that returns None so event times default to creation time."""
    return None
