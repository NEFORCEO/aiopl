import contextlib
import json
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

from pydantic import ValidationError

from aiopaysell.exceptions import (
    STATUS_TO_ERROR,
    DeserializationError,
    HTTPError,
    RateLimitError,
)
from aiopaysell.types import _PaysellType

if TYPE_CHECKING:
    from collections.abc import Mapping

    import aiopaysell
    from aiopaysell._methods import PaysellMethod
    from aiopaysell.client.network import Network


_ParsedError = tuple[str, str, "list[str] | None", "list[dict] | None"]

# Fallback `code` when a response gives a bare-string `detail` (seen from
# /public/invoices/{id}, which raises a plain FastAPI HTTPException instead
# of going through the core's documented {code, message} error contract).
_STATUS_TO_FALLBACK_CODE: dict[int, str] = {
    401: "invalid_api_key",
    404: "not_found",
    409: "conflict",
    422: "invalid_input",
    429: "too_many_requests",
    502: "cbc_unreachable",
}


def _parse_error_body(content: str, status_code: int) -> _ParsedError:
    """Return (code, message, details, errors) from any of the error shapes."""
    payload = json.loads(content)
    detail = payload["detail"]
    if isinstance(detail, dict):
        return detail["code"], detail["message"], detail.get("details"), None
    if isinstance(detail, list):
        message = (
            "; ".join(
                f"{'.'.join(str(p) for p in e.get('loc', []))}: {e.get('msg')}"
                for e in detail
            )
            or "request validation failed"
        )
        return "validation_error", message, None, detail
    if isinstance(detail, str):
        code = _STATUS_TO_FALLBACK_CODE.get(status_code, "unknown")
        return code, detail, None, None
    msg = "detail is neither an object, a list, nor a string"
    raise ValueError(msg)


class BaseSession(ABC):
    """
    Abstract session class.

    If you want to implement your own session class (e.g. on top of
    ``httpx``), inherit this class.
    """

    def __init__(self, network: "Network", timeout: float = 30) -> None:
        self.network = network
        self.timeout = timeout

    @abstractmethod
    async def request(
        self,
        token: str,
        client: "aiopaysell.Paysell",
        method: "PaysellMethod[_PaysellType]",
    ) -> "_PaysellType":
        """Make an HTTP request."""

    def _check_response(
        self,
        client: "aiopaysell.Paysell",
        method: "PaysellMethod[_PaysellType]",
        status_code: int,
        content: str,
        headers: "Mapping[str, str] | None" = None,
    ) -> "_PaysellType":
        if status_code < HTTPStatus.OK or status_code >= HTTPStatus.MULTIPLE_CHOICES:
            error_cls = STATUS_TO_ERROR.get(status_code)
            if error_cls is None:
                raise HTTPError(method, status_code, content)
            try:
                code, message, details, errors = _parse_error_body(content, status_code)
            except (ValueError, KeyError, TypeError) as e:
                raise HTTPError(method, status_code, content) from e
            error = error_cls(method, code, message, details=details, errors=errors)
            if isinstance(error, RateLimitError) and headers is not None:
                retry_after = headers.get("Retry-After") or headers.get("retry-after")
                if retry_after is not None:
                    with contextlib.suppress(ValueError):
                        error.retry_after = float(retry_after)
            raise error

        try:
            result = method.__return_type__.model_validate_json(
                content,
                context={"client": client},
            )
        except ValidationError as e:
            raise DeserializationError(
                method,
                "failed to deserialize response",
            ) from e
        return cast("_PaysellType", result)
