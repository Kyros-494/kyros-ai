"""Structured logging configuration for Kyros.

- Development: colored, human-readable console output
- Production: JSON lines for log aggregation (Datadog, ELK, CloudWatch)
"""

import logging
import sys

import structlog


def setup_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """Configure structlog + stdlib logging for the entire application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        environment: 'development' for pretty console, anything else for JSON.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if environment == "development":
        # Pretty, colored output for local development
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON lines for production log aggregation
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("memory stored", agent_id="abc", memory_id="xyz")
    """
    return structlog.get_logger(name)
