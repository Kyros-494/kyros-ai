"""Advanced debugging and inspection tools for Kyros.

This module provides tools for debugging memory operations, inspecting memory state,
and profiling performance.

Example:
    ```python
    from kyros import KyrosClient
    from kyros.debug import MemoryInspector, PerformanceProfiler

    # Inspect memories
    inspector = MemoryInspector(client)
    report = inspector.inspect_agent("user123")
    print(report)

    # Profile performance
    with PerformanceProfiler() as profiler:
        response = proxy.chat(...)

    print(profiler.get_report())
    ```
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

from .client import KyrosClient


class MemoryInspector:
    """Tool for inspecting and analyzing memory state.

    Provides detailed insights into memory content, quality, and patterns.
    """

    def __init__(self, client: KyrosClient) -> None:
        """Initialize memory inspector.

        Args:
            client: Kyros client instance
        """
        self.client = client

    def inspect_agent(self, agent_id: str, detailed: bool = True) -> dict[str, Any]:
        """Inspect all memories for an agent.

        Args:
            agent_id: Agent ID to inspect
            detailed: Include detailed analysis (default: True)

        Returns:
            Inspection report with memory statistics and analysis
        """
        print(f"\n🔍 Inspecting memories for agent: {agent_id}\n")

        report: dict[str, Any] = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {},
            "memories": [],
            "analysis": {},
        }

        # Get all memories (we'll use search with empty query)
        try:
            # Try to get memories via search endpoint
            response = self.client.post(
                "/v1/search/unified",
                json={"agent_id": agent_id, "query": "memories", "k": 100},
            )

            if response.status_code == 200:
                data = response.json()
                memories = data.get("results", [])

                report["summary"]["total_memories"] = len(memories)
                report["memories"] = memories

                if detailed and memories:
                    report["analysis"] = self._analyze_memories(memories)

                self._print_report(report)
                return report
            else:
                print(f"❌ Failed to fetch memories: {response.status_code}")
                return report

        except Exception as e:
            print(f"❌ Error inspecting memories: {e}")
            return report

    def _analyze_memories(self, memories: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze memory patterns and quality.

        Args:
            memories: List of memory objects

        Returns:
            Analysis results
        """
        analysis: dict[str, Any] = {
            "by_type": defaultdict[str, int](int),
            "importance_stats": {
                "min": 1.0,
                "max": 0.0,
                "avg": 0.0,
                "high_quality": 0,  # importance > 0.7
                "medium_quality": 0,  # 0.4 < importance <= 0.7
                "low_quality": 0,  # importance <= 0.4
            },
            "content_stats": {
                "avg_length": 0,
                "min_length": float('inf'),
                "max_length": 0,
            },
            "temporal": {
                "oldest": None,
                "newest": None,
            },
        }

        total_importance = 0.0
        total_length = 0

        for mem in memories:
            # Type distribution
            mem_type = str(mem.get("type", "unknown"))
            analysis["by_type"][mem_type] += 1

            # Importance stats
            raw_importance = mem.get("importance", 0.5)
            importance = (
                float(raw_importance)
                if isinstance(raw_importance, int | float)
                else 0.5
            )
            total_importance += importance
            analysis["importance_stats"]["min"] = min(
                analysis["importance_stats"]["min"], importance
            )
            analysis["importance_stats"]["max"] = max(
                analysis["importance_stats"]["max"], importance
            )

            if importance > 0.7:
                analysis["importance_stats"]["high_quality"] += 1
            elif importance > 0.4:
                analysis["importance_stats"]["medium_quality"] += 1
            else:
                analysis["importance_stats"]["low_quality"] += 1

            # Content stats
            content = str(mem.get("content", ""))
            length = len(content)
            total_length += length
            analysis["content_stats"]["min_length"] = min(
                analysis["content_stats"]["min_length"], length
            )
            analysis["content_stats"]["max_length"] = max(
                analysis["content_stats"]["max_length"], length
            )

            # Temporal stats
            raw_created_at = mem.get("created_at")
            created_at = str(raw_created_at) if raw_created_at else None
            if created_at:
                if not analysis["temporal"]["oldest"]:
                    analysis["temporal"]["oldest"] = created_at
                    analysis["temporal"]["newest"] = created_at
                else:
                    if created_at < analysis["temporal"]["oldest"]:
                        analysis["temporal"]["oldest"] = created_at
                    if created_at > analysis["temporal"]["newest"]:
                        analysis["temporal"]["newest"] = created_at

        # Calculate averages
        count = len(memories)
        if count > 0:
            analysis["importance_stats"]["avg"] = total_importance / count
            analysis["content_stats"]["avg_length"] = total_length / count

        # Convert defaultdict to regular dict
        analysis["by_type"] = dict(analysis["by_type"])

        return analysis

    def _print_report(self, report: dict[str, Any]) -> None:
        """Print formatted inspection report.

        Args:
            report: Inspection report
        """
        print("=" * 60)
        print("MEMORY INSPECTION REPORT")
        print("=" * 60)

        print("\n📊 Summary:")
        print(f"  Agent ID: {report['agent_id']}")
        print(f"  Total Memories: {report['summary'].get('total_memories', 0)}")
        print(f"  Timestamp: {report['timestamp']}")

        if report.get("analysis"):
            analysis = report["analysis"]

            print("\n📝 Memory Types:")
            for mem_type, count in analysis["by_type"].items():
                print(f"  {mem_type}: {count}")

            print("\n⭐ Importance Distribution:")
            imp_stats = analysis["importance_stats"]
            print(f"  Min: {imp_stats['min']:.2f}")
            print(f"  Max: {imp_stats['max']:.2f}")
            print(f"  Avg: {imp_stats['avg']:.2f}")
            print(f"  High Quality (>0.7): {imp_stats['high_quality']}")
            print(f"  Medium Quality (0.4-0.7): {imp_stats['medium_quality']}")
            print(f"  Low Quality (<0.4): {imp_stats['low_quality']}")

            print("\n📏 Content Stats:")
            content_stats = analysis["content_stats"]
            print(f"  Avg Length: {content_stats['avg_length']:.0f} chars")
            print(f"  Min Length: {content_stats['min_length']} chars")
            print(f"  Max Length: {content_stats['max_length']} chars")

            print("\n📅 Temporal Range:")
            temporal = analysis["temporal"]
            if temporal["oldest"]:
                print(f"  Oldest: {temporal['oldest']}")
                print(f"  Newest: {temporal['newest']}")

        print("\n" + "=" * 60)

    def compare_agents(self, agent_ids: list[str]) -> dict[str, Any]:
        """Compare memory patterns across multiple agents.

        Args:
            agent_ids: List of agent IDs to compare

        Returns:
            Comparison report
        """
        print(f"\n🔍 Comparing {len(agent_ids)} agents...\n")

        reports: dict[str, dict[str, Any]] = {}
        for agent_id in agent_ids:
            reports[agent_id] = self.inspect_agent(agent_id, detailed=True)

        # Generate comparison
        comparison: dict[str, Any] = {
            "agents": agent_ids,
            "summary": {},
        }

        for agent_id, report in reports.items():
            comparison["summary"][agent_id] = {
                "total": report["summary"].get("total_memories", 0),
                "avg_importance": report.get("analysis", {}).get(
                    "importance_stats", {}
                ).get("avg", 0),
            }

        return comparison


class PerformanceProfiler:
    """Tool for profiling Kyros operations.

    Tracks timing, memory usage, and API calls.
    """

    def __init__(self) -> None:
        """Initialize performance profiler."""
        self.metrics: dict[str, Any] = {
            "operations": [],
            "total_time": 0,
            "api_calls": 0,
        }
        self.start_time: float | None = None

    def __enter__(self) -> PerformanceProfiler:
        """Start profiling."""
        self.start_time = time.time()
        print("\n⏱️  Performance profiling started...\n")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        """Stop profiling and print report."""
        started_at = self.start_time or time.time()
        self.metrics["total_time"] = time.time() - started_at
        self.print_report()

    def record_operation(
        self,
        operation: str,
        duration: float,
        details: dict[str, Any] | None = None
    ) -> None:
        """Record an operation.

        Args:
            operation: Operation name
            duration: Duration in seconds
            details: Optional operation details
        """
        self.metrics["operations"].append({
            "operation": operation,
            "duration": duration,
            "details": details or {},
        })

    def record_api_call(self) -> None:
        """Record an API call."""
        self.metrics["api_calls"] += 1

    def get_report(self) -> dict[str, Any]:
        """Get performance report.

        Returns:
            Performance metrics
        """
        return self.metrics

    def print_report(self) -> None:
        """Print formatted performance report."""
        print("\n" + "=" * 60)
        print("PERFORMANCE PROFILE REPORT")
        print("=" * 60)

        print(f"\n⏱️  Total Time: {self.metrics['total_time']:.3f}s")
        print(f"📡 API Calls: {self.metrics['api_calls']}")

        if self.metrics["operations"]:
            print("\n📊 Operations:")
            for op in self.metrics["operations"]:
                print(f"  {op['operation']}: {op['duration']:.3f}s")
                if op["details"]:
                    for key, value in op["details"].items():
                        print(f"    {key}: {value}")

        print("\n" + "=" * 60)


class DebugLogger:
    """Enhanced debug logger with structured output.

    Provides detailed logging for debugging Kyros operations.
    """

    def __init__(self, enabled: bool = True, verbose: bool = False) -> None:
        """Initialize debug logger.

        Args:
            enabled: Enable logging (default: True)
            verbose: Enable verbose logging (default: False)
        """
        self.enabled = enabled
        self.verbose = verbose
        self.logs: list[dict[str, Any]] = []

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log a message.

        Args:
            level: Log level (INFO, DEBUG, WARNING, ERROR)
            message: Log message
            **kwargs: Additional context
        """
        if not self.enabled:
            return

        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            **kwargs,
        }

        self.logs.append(log_entry)

        # Print if verbose
        if self.verbose or level in ("WARNING", "ERROR"):
            icon = {
                "INFO": "ℹ️ ",
                "DEBUG": "🐛",
                "WARNING": "⚠️ ",
                "ERROR": "❌",
            }.get(level, "  ")

            print(f"{icon} [{level}] {message}")
            if kwargs:
                for key, value in kwargs.items():
                    print(f"    {key}: {value}")

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.log("INFO", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.log("DEBUG", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.log("ERROR", message, **kwargs)

    def get_logs(self, level: str | None = None) -> list[dict[str, Any]]:
        """Get logged messages.

        Args:
            level: Filter by log level (optional)

        Returns:
            List of log entries
        """
        if level:
            return [log for log in self.logs if log["level"] == level]
        return self.logs

    def export_logs(self, filepath: str) -> None:
        """Export logs to file.

        Args:
            filepath: Path to export file
        """
        with open(filepath, "w") as f:
            json.dump(self.logs, f, indent=2)

        print(f"✅ Logs exported to: {filepath}")

    def clear(self) -> None:
        """Clear all logs."""
        self.logs = []


def trace_memory_operation(func: Any) -> Any:
    """Decorator to trace memory operations.

    Usage:
        ```python
        @trace_memory_operation
        def store_memory(content):
            # ... operation ...
            pass
        ```
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        print(f"\n🔍 Tracing: {func.__name__}")
        print(f"   Args: {args}")
        print(f"   Kwargs: {kwargs}")

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            print(f"   ✅ Success ({duration:.3f}s)")
            print(f"   Result: {result}")
            return result
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ Error ({duration:.3f}s)")
            print(f"   Exception: {e}")
            raise

    return wrapper
