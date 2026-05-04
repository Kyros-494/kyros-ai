"""Kyros SDK Exceptions."""


class KyrosError(Exception):
    """Base exception for Kyros SDK."""


class KyrosAPIError(KyrosError):
    """API error from Kyros server."""


class KyrosConnectionError(KyrosError):
    """Connection error to Kyros server."""
