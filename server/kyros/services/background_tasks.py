import asyncio
from datetime import datetime
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
from typing import Any

# Global sets and lists for tracking tasks
_background_tasks: set[asyncio.Task] = set()
_task_history: list[dict[str, Any]] = []

def create_background_task(coro, name: str | None = None, details: str | None = None) -> asyncio.Task:
    """Create a tracked background task with exception tracking and history logging."""
    task = asyncio.create_task(coro, name=name)
    _background_tasks.add(task)
    
    task_info = {
        "id": id(task),
        "name": name or "unnamed",
        "details": details or "—",
        "status": "running",
        "started_at": datetime.now(UTC).isoformat(),
        "completed_at": None,
        "error": None
    }
    _task_history.append(task_info)
    
    # Keep history size bounded
    if len(_task_history) > 100:
        _task_history.pop(0)

    def _on_done(t: asyncio.Task) -> None:
        _background_tasks.discard(t)
        task_info["completed_at"] = datetime.now(UTC).isoformat()
        if t.cancelled():
            task_info["status"] = "cancelled"
        elif t.exception() is not None:
            task_info["status"] = "failed"
            task_info["error"] = str(t.exception())
        else:
            task_info["status"] = "completed"

    task.add_done_callback(_on_done)
    return task

def get_task_history() -> list[dict[str, Any]]:
    """Get list of recent background tasks and their statuses."""
    return _task_history
