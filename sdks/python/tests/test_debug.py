"""Tests for debug module."""

import time
from typing import Any, Never
from unittest.mock import MagicMock

import pytest

from kyros.debug import (
    DebugLogger,
    MemoryInspector,
    PerformanceProfiler,
    trace_memory_operation,
)


class TestMemoryInspector:
    """Tests for MemoryInspector."""

    def test_init(self) -> None:
        """Test inspector initialization."""
        client = MagicMock()
        inspector = MemoryInspector(client)
        assert inspector.client == client

    def test_inspect_agent_no_memories(self) -> None:
        """Test inspecting agent with no memories."""
        client = MagicMock()
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {"results": []}

        inspector = MemoryInspector(client)
        report = inspector.inspect_agent("test-agent")

        assert report["agent_id"] == "test-agent"
        assert report["summary"]["total_memories"] == 0
        assert report["memories"] == []

    def test_inspect_agent_with_memories(self) -> None:
        """Test inspecting agent with memories."""
        client = MagicMock()
        memories = [
            {
                "id": "1",
                "type": "semantic",
                "content": "User prefers dark mode",
                "importance": 0.8,
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "2",
                "type": "episodic",
                "content": "User completed onboarding",
                "importance": 0.6,
                "created_at": "2024-01-02T00:00:00Z",
            },
        ]
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {"results": memories}

        inspector = MemoryInspector(client)
        report = inspector.inspect_agent("test-agent", detailed=True)

        assert report["agent_id"] == "test-agent"
        assert report["summary"]["total_memories"] == 2
        assert len(report["memories"]) == 2
        assert "analysis" in report

        # Check analysis
        analysis = report["analysis"]
        assert analysis["by_type"]["semantic"] == 1
        assert analysis["by_type"]["episodic"] == 1
        assert analysis["importance_stats"]["min"] == 0.6
        assert analysis["importance_stats"]["max"] == 0.8
        assert analysis["importance_stats"]["avg"] == 0.7

    def test_inspect_agent_error(self) -> None:
        """Test inspector handles errors gracefully."""
        client = MagicMock()
        client.post.return_value.status_code = 500

        inspector = MemoryInspector(client)
        report = inspector.inspect_agent("test-agent")

        assert report["agent_id"] == "test-agent"
        assert report["summary"] == {}

    def test_compare_agents(self) -> None:
        """Test comparing multiple agents."""
        client = MagicMock()
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {
            "results": [
                {
                    "id": "1",
                    "type": "semantic",
                    "content": "Test",
                    "importance": 0.7,
                }
            ]
        }

        inspector = MemoryInspector(client)
        comparison = inspector.compare_agents(["agent1", "agent2"])

        assert "agents" in comparison
        assert len(comparison["agents"]) == 2
        assert "summary" in comparison


class TestPerformanceProfiler:
    """Tests for PerformanceProfiler."""

    def test_init(self) -> None:
        """Test profiler initialization."""
        profiler = PerformanceProfiler()
        assert profiler.metrics["operations"] == []
        assert profiler.metrics["total_time"] == 0
        assert profiler.metrics["api_calls"] == 0

    def test_context_manager(self) -> None:
        """Test profiler as context manager."""
        with PerformanceProfiler() as profiler:
            time.sleep(0.01)
            profiler.record_operation("test_op", 0.01)
            profiler.record_api_call()

        assert profiler.metrics["total_time"] > 0
        assert len(profiler.metrics["operations"]) == 1
        assert profiler.metrics["api_calls"] == 1

    def test_record_operation(self) -> None:
        """Test recording operations."""
        profiler = PerformanceProfiler()
        profiler.record_operation("test_op", 0.5, {"detail": "value"})

        assert len(profiler.metrics["operations"]) == 1
        op = profiler.metrics["operations"][0]
        assert op["operation"] == "test_op"
        assert op["duration"] == 0.5
        assert op["details"]["detail"] == "value"

    def test_record_api_call(self) -> None:
        """Test recording API calls."""
        profiler = PerformanceProfiler()
        profiler.record_api_call()
        profiler.record_api_call()

        assert profiler.metrics["api_calls"] == 2

    def test_get_report(self) -> None:
        """Test getting performance report."""
        profiler = PerformanceProfiler()
        profiler.record_operation("op1", 0.1)
        profiler.record_api_call()

        report = profiler.get_report()
        assert "operations" in report
        assert "total_time" in report
        assert "api_calls" in report


class TestDebugLogger:
    """Tests for DebugLogger."""

    def test_init(self) -> None:
        """Test logger initialization."""
        logger = DebugLogger(enabled=True, verbose=False)
        assert logger.enabled is True
        assert logger.verbose is False
        assert logger.logs == []

    def test_log_disabled(self) -> None:
        """Test logging when disabled."""
        logger = DebugLogger(enabled=False)
        logger.log("INFO", "test message")
        assert len(logger.logs) == 0

    def test_log_enabled(self) -> None:
        """Test logging when enabled."""
        logger = DebugLogger(enabled=True, verbose=False)
        logger.log("INFO", "test message", key="value")

        assert len(logger.logs) == 1
        log = logger.logs[0]
        assert log["level"] == "INFO"
        assert log["message"] == "test message"
        assert log["key"] == "value"

    def test_log_levels(self) -> None:
        """Test different log levels."""
        logger = DebugLogger(enabled=True)

        logger.info("info message")
        logger.debug("debug message")
        logger.warning("warning message")
        logger.error("error message")

        assert len(logger.logs) == 4
        assert logger.logs[0]["level"] == "INFO"
        assert logger.logs[1]["level"] == "DEBUG"
        assert logger.logs[2]["level"] == "WARNING"
        assert logger.logs[3]["level"] == "ERROR"

    def test_get_logs(self) -> None:
        """Test getting logs."""
        logger = DebugLogger(enabled=True)
        logger.info("info")
        logger.error("error")

        all_logs = logger.get_logs()
        assert len(all_logs) == 2

        error_logs = logger.get_logs(level="ERROR")
        assert len(error_logs) == 1
        assert error_logs[0]["level"] == "ERROR"

    def test_export_logs(self, tmp_path: Any) -> None:
        """Test exporting logs to file."""
        logger = DebugLogger(enabled=True)
        logger.info("test message")

        output_file = tmp_path / "logs.json"
        logger.export_logs(str(output_file))

        assert output_file.exists()

        import json
        with open(output_file) as f:
            logs = json.load(f)

        assert len(logs) == 1
        assert logs[0]["message"] == "test message"

    def test_clear(self) -> None:
        """Test clearing logs."""
        logger = DebugLogger(enabled=True)
        logger.info("test")
        assert len(logger.logs) == 1

        logger.clear()
        assert len(logger.logs) == 0


class TestTraceDecorator:
    """Tests for trace_memory_operation decorator."""

    def test_trace_success(self, capsys: Any) -> None:
        """Test tracing successful operation."""

        @trace_memory_operation
        def test_func(x: int, y: int) -> int:
            return x + y

        result = test_func(1, 2)
        assert result == 3

        captured = capsys.readouterr()
        assert "Tracing: test_func" in captured.out
        assert "Success" in captured.out

    def test_trace_error(self, capsys: Any) -> None:
        """Test tracing failed operation."""

        @trace_memory_operation
        def test_func() -> Never:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            test_func()

        captured = capsys.readouterr()
        assert "Tracing: test_func" in captured.out
        assert "Error" in captured.out
        assert "test error" in captured.out
