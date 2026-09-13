from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from aiopaysell import loggers
from aiopaysell.tools.verify_signature import (
    DEFAULT_TIMESTAMP_TOLERANCE,
    verify_signature,
)
from aiopaysell.types import PaymentCredited, PaymentRejected, WebhookEvent

from .router import WebhookRouter

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping

    from aiopaysell._events import EventObserver

    WebServerHandler = Callable[[bytes, "Mapping[str, str]"], "Awaitable[bool]"]

_APP = TypeVar("_APP")

DEFAULT_SIGNATURE_HEADER = "X-Paysell-Signature"
"""Header carrying ``sha256=`` followed by the hex HMAC."""

DEFAULT_TIMESTAMP_HEADER = "X-Paysell-Timestamp"
"""Header carrying the unix-seconds timestamp that's part of the signed string."""

_EVENT_DATA_TYPES: dict[str, type[BaseModel]] = {
    "payment.credited": PaymentCredited,
    "payment.rejected": PaymentRejected,
}


class WebhookManager(ABC, Generic[_APP]):
    """
    Webhook manager.

    Wires an HTTP route in your web framework to
    :meth:`WebhookHandler.feed_update`. To support a framework not covered
    here, inherit this class and implement :meth:`register_handler`.
    """

    def __init__(self, app: _APP, path: str = "/paysell/webhook") -> None:
        self._app = app
        self._path = path

    @abstractmethod
    def register_handler(self, feed_update: "WebServerHandler") -> None:
        """Register ``feed_update`` to run on POST requests at ``self._path``."""


class WebhookHandler:
    """
    Verifies and dispatches incoming webhooks.

    Composes its own :class:`WebhookRouter` rather than inheriting one, so
    its events stay independent of the polling router's — see
    :class:`aiopaysell.polling.PollingManager`.
    """

    _kwargs: dict[str, object]

    def __init__(
        self,
        manager: "WebhookManager | None",
        webhook_secret: str | None,
        signature_header: str = DEFAULT_SIGNATURE_HEADER,
        timestamp_header: str = DEFAULT_TIMESTAMP_HEADER,
        timestamp_tolerance: float = DEFAULT_TIMESTAMP_TOLERANCE,
    ) -> None:
        if manager is not None and webhook_secret is None:
            msg = (
                "webhook_secret is required when webhook_manager is set. "
                "It's the secret shown once when you created the API key — "
                "not the key itself. Pass Paysell(..., webhook_secret=...)."
            )
            raise ValueError(msg)
        self._webhook_router = WebhookRouter()
        self._webhook_secret = webhook_secret
        self._signature_header = signature_header
        self._timestamp_header = timestamp_header
        self._timestamp_tolerance = timestamp_tolerance
        self._webhook_manager = manager
        if manager is not None:
            manager.register_handler(self.feed_update)

    @property
    def payment_credited(self) -> "EventObserver":
        """Fires for every ``payment.credited`` webhook (paid, overpaid, underpaid)."""
        return self._webhook_router.payment_credited

    @property
    def payment_rejected(self) -> "EventObserver":
        """Fires when a held deposit is declined. Release nothing on it."""
        return self._webhook_router.payment_rejected

    def _header(self, headers: "Mapping[str, str]", name: str) -> str | None:
        target = name.lower()
        return next(
            (value for key, value in headers.items() if key.lower() == target),
            None,
        )

    def _check_signature(self, body: bytes, headers: "Mapping[str, str]") -> bool:
        """
        Verify the raw body against the configured signature and timestamp headers.

        :param body: raw request body.
        :param headers: request headers.
        :return: ``True`` if the signature is present, correct, and its
            timestamp is within :attr:`_timestamp_tolerance`.
        """
        if self._webhook_secret is None:
            loggers.webhook.error(
                "Webhook is not handled: no webhook_secret configured. "
                "Pass Paysell(..., webhook_secret=...) — it's the secret "
                "shown once when the API key was created, not the key itself.",
            )
            return False
        signature = self._header(headers, self._signature_header)
        timestamp = self._header(headers, self._timestamp_header)
        if signature is None or timestamp is None:
            return False
        return verify_signature(
            body,
            signature,
            timestamp,
            self._webhook_secret,
            tolerance=self._timestamp_tolerance,
        )

    async def feed_update(
        self,
        body: bytes,
        headers: "Mapping[str, str]",
        **kwargs: object,
    ) -> bool:
        """
        Verify, parse and dispatch one webhook delivery.

        :param body: raw request body, exactly as received — do not
            re-serialise it before calling this, the signature check needs
            the original bytes.
        :param headers: request headers.
        :param kwargs: extra data forwarded to the matching handler.
        :return: ``True`` if the signature was valid (whether or not a
            handler matched); answer the caller with a 2xx in that case so
            the provider doesn't retry.
        """
        if not self._check_signature(body, headers):
            loggers.webhook.warning(
                "Webhook is not handled: invalid or missing signature/timestamp.",
            )
            return False
        try:
            event = WebhookEvent.model_validate_json(body)
        except ValidationError as e:
            loggers.webhook.warning(
                "Webhook is not handled: failed to parse body. %s",
                e,
            )
            return False
        data_type = _EVENT_DATA_TYPES.get(event.type)
        payload = data_type.model_validate(event.data) if data_type else event.data
        try:
            handled = await self._webhook_router.propagate_event(
                payload,
                event.type,
                **self._kwargs | kwargs,
            )
        except Exception:
            loggers.webhook.exception(
                "Error while handling webhook event_id=%s:\n",
                event.event_id,
            )
            return False
        if handled:
            loggers.webhook.info(
                "Webhook event_id=%s type=%s is handled.",
                event.event_id,
                event.type,
            )
        else:
            loggers.webhook.info(
                "Webhook event_id=%s type=%s has no matching handler.",
                event.event_id,
                event.type,
            )
        return True
