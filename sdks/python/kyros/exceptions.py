"""Kyros SDK exception classes."""


class KyrosError(Exception):
    """Base exception for all Kyros SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize KyrosError.

        Args:
            message: Error message
            status_code: HTTP status code (if applicable)
            error_code: Application-specific error code
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

    def __str__(self) -> str:
        """Return string representation of error."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        return " ".join(parts)


class AuthenticationError(KyrosError):
    """Raised when authentication fails (401/403)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
        error_code: str | None = None,
    ) -> None:
        """Initialize AuthenticationError.

        Args:
            message: Error message
            status_code: HTTP status code (401 or 403)
            error_code: Application-specific error code
        """
        super().__init__(message, status_code, error_code)


class RateLimitError(KyrosError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: int = 0,
        remaining: int = 0,
        reset_at: int = 0,
        error_code: str | None = None,
    ) -> None:
        """Initialize RateLimitError.

        Args:
            message: Error message
            limit: Rate limit maximum
            remaining: Remaining requests in current window
            reset_at: Unix timestamp when limit resets
            error_code: Application-specific error code
        """
        super().__init__(message, 429, error_code)
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at
        self.retry_after = max(0, reset_at - int(__import__("time").time()))

    def __str__(self) -> str:
        """Return string representation with rate limit details."""
        base = super().__str__()
        return (
            f"{base} (limit={self.limit}, remaining={self.remaining}, "
            f"retry_after={self.retry_after}s)"
        )


class NotFoundError(KyrosError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str | None = None,
    ) -> None:
        """Initialize NotFoundError.

        Args:
            message: Error message
            error_code: Application-specific error code
        """
        super().__init__(message, 404, error_code)


class ValidationError(KyrosError):
    """Raised when request validation fails (422)."""

    def __init__(
        self,
        message: str = "Validation error",
        error_code: str | None = None,
    ) -> None:
        """Initialize ValidationError.

        Args:
            message: Error message
            error_code: Application-specific error code
        """
        super().__init__(message, 422, error_code)


class ServerError(KyrosError):
    """Raised when server returns 5xx error."""

    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = 500,
        error_code: str | None = None,
    ) -> None:
        """Initialize ServerError.

        Args:
            message: Error message
            status_code: HTTP status code (5xx)
            error_code: Application-specific error code
        """
        super().__init__(message, status_code, error_code)


class TimeoutError(KyrosError):
    """Raised when request times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        timeout: float | None = None,
    ) -> None:
        """Initialize TimeoutError.

        Args:
            message: Error message
            timeout: Timeout value in seconds
        """
        super().__init__(message)
        self.timeout = timeout

    def __str__(self) -> str:
        """Return string representation with timeout."""
        if self.timeout:
            return f"{self.message} (timeout={self.timeout}s)"
        return self.message


class ConnectionError(KyrosError):
    """Raised when connection to server fails."""

    def __init__(
        self,
        message: str = "Connection failed",
        base_url: str | None = None,
    ) -> None:
        """Initialize ConnectionError.

        Args:
            message: Error message
            base_url: Base URL that failed to connect
        """
        super().__init__(message)
        self.base_url = base_url

    def __str__(self) -> str:
        """Return string representation with base URL."""
        if self.base_url:
            return f"{self.message} (url={self.base_url})"
        return self.message
