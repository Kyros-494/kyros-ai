from enum import Enum
from typing import Any

class QueryType(str, Enum):
    TEMPORAL = "temporal"
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    GENERAL = "general"

class QueryClassification:
    def __init__(self, query: str):
        self.query = query
        self.query_type = QueryType.GENERAL
        self.entities: list[str] = []
        self.expanded_keywords: list[str] = []
        self.temporal_info: dict[str, Any] | None = None

def classify_query(query: str) -> QueryClassification:
    """Fallback classification returning GENERAL query type."""
    return QueryClassification(query)
