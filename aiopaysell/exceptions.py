from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiopaysell._methods import PaysellMethod


class PaysellError(Exception):
    """Base class for every exception this library raises."""


class APIError(PaysellError):
    """
    Base class for errors the API answered with.

    Raised for a non-2xx response — either the
    ``{"detail": {"code": ..., "message": ...}}`` shape the core produces,
    or FastAPI's own ``{"detail": [...]}`` list of field errors when the
    request body itself fails validation (``code`` is then the synthetic
    ``"validation_error"`` and :attr:`errors` holds the raw list).
    """

    status_code: int

    def __init__(
        self,
        method: "PaysellMethod",
        code: str,
        message: str,
        *,
        details: list[str] | None = None,
        errors: list[dict] | None = None,
    ) -> None:
        self.method = method
        self.code = code
        self.message = message
        self.details = details
        """Field-level detail strings, when the core included any."""
        self.errors = errors
        """The raw FastAPI validation error list, for a ``"validation_error"``."""

    def __str__(self) -> str:
        base = (
            f"[{self.status_code}] {self.method.__http_method__} "
            f"{self.method.build_path()} -> {self.code}: {self.message}"
        )
        if self.details:
            base += f" ({'; '.join(self.details)})"
        return base


class AuthenticationError(APIError):
    """401 ``invalid_api_key`` — the key is missing, malformed, unknown or revoked."""

    status_code = 401


class NotFoundError(APIError):
    """404 ``not_found`` — no such object, or it belongs to another shop."""

    status_code = 404


class ConflictError(APIError):
    """409 ``conflict`` — the invoice is in a state that forbids this (e.g. cancel a paid one)."""  # noqa: E501

    status_code = 409


class InvalidRequestError(APIError):
    """
    422 — the request is malformed or outside the invoice's limits.

    ``code`` is ``invalid_input`` for a core-level rejection (bad amount,
    too many decimal places, amount outside the min/max), or the synthetic
    ``validation_error`` when the request body itself failed validation
    before reaching the core — see :attr:`APIError.errors`.
    """

    status_code = 422


class RateLimitError(APIError):
    """
    429 ``too_many_requests`` — invoices this hour, open invoices, or requests per min.

    ``retry_after`` holds the ``Retry-After`` header, in seconds, when the
    response included one — wait that long before retrying rather than
    looping tightly.
    """

    status_code = 429
    retry_after: float | None = None


class BadGatewayError(APIError):
    """502 ``cbc_unreachable``/``cbc_error`` — processing core unreachable. Safe to retry with the same ``idempotency_key``."""  # noqa: E501

    status_code = 502


STATUS_TO_ERROR: dict[int, type[APIError]] = {
    401: AuthenticationError,
    404: NotFoundError,
    409: ConflictError,
    422: InvalidRequestError,
    429: RateLimitError,
    502: BadGatewayError,
}


class HTTPError(PaysellError):
    """Raised for a non-2xx response that doesn't match the documented error shape."""

    def __init__(self, method: "PaysellMethod", status_code: int, content: str) -> None:
        self.method = method
        self.status_code = status_code
        self.content = content

    def __str__(self) -> str:
        return (
            f"{self.method.__http_method__} {self.method.build_path()} "
            f"returned HTTP {self.status_code}: {self.content}"
        )


class DeserializationError(PaysellError):
    """Raised when a 2xx response body doesn't match the expected shape."""

    def __init__(self, method: "PaysellMethod", message: str) -> None:
        self.method = method
        self.message = message

    def __str__(self) -> str:
        path = self.method.build_path()
        return f"{self.method.__http_method__} {path}: {self.message}"


class NetworkError(PaysellError):
    """Raised when the request itself fails — DNS, connection refused, TLS, etc."""

    def __init__(self, method: "PaysellMethod", cause: Exception) -> None:
        self.method = method
        self.cause = cause

    def __str__(self) -> str:
        return (
            f"{self.method.__http_method__} {self.method.build_path()} "
            f"failed: {self.cause!r}"
        )


class APITimeoutError(PaysellError):
    """Raised when a request exceeds the configured timeout."""

    def __init__(self, method: "PaysellMethod", timeout: float) -> None:
        self.method = method
        self.timeout = timeout

    def __str__(self) -> str:
        return (
            f"{self.method.__http_method__} {self.method.build_path()} "
            f"exceeded the timeout of {self.timeout}s"
        )
