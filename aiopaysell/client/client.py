from typing import TYPE_CHECKING

from aiopaysell import loggers
from aiopaysell._methods import Methods
from aiopaysell.client.network import MAINNET
from aiopaysell.polling import PollingConfig, PollingManager, PollingRouter
from aiopaysell.tools.verify_signature import DEFAULT_TIMESTAMP_TOLERANCE
from aiopaysell.webhook import (
    DEFAULT_SIGNATURE_HEADER,
    DEFAULT_TIMESTAMP_HEADER,
    WebhookHandler,
    WebhookRouter,
)

from .session import AiohttpSession

if TYPE_CHECKING:
    from types import TracebackType

    from aiopaysell._methods import PaysellMethod
    from aiopaysell.client.session import BaseSession
    from aiopaysell.types import _PaysellType
    from aiopaysell.webhook import WebhookManager


class Paysell(Methods, WebhookHandler, PollingManager):
    """
    Client class providing the Paysell API.

    :param token: Paysell API key.
    :param session: HTTP session class. Defaults to
        :class:`aiopaysell.client.session.AiohttpSession`.
    :param webhook_manager: a webhook manager
        (:class:`aiopaysell.webhook.AiohttpManager`, etc.) to receive
        updates through your web server.
    :param webhook_secret: the webhook secret shown once when you created
        the API key — a different value from ``token``. Required whenever
        ``webhook_manager`` is set; without it, no delivery can be verified.
    :param signature_header: header carrying the webhook HMAC signature.
        See :data:`aiopaysell.webhook.DEFAULT_SIGNATURE_HEADER`.
    :param timestamp_header: header carrying the unix-seconds timestamp
        that's part of the signed string. See
        :data:`aiopaysell.webhook.DEFAULT_TIMESTAMP_HEADER`.
    :param timestamp_tolerance: max allowed clock skew between that
        timestamp and now, in seconds, before a webhook is rejected as a
        possible replay.
    :param polling_config: configuration for :meth:`aiopaysell.Paysell.start_polling`.
    :param timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        token: str,
        *,
        session: type["BaseSession"] = AiohttpSession,
        timeout: float = 30,
        webhook_manager: "WebhookManager | None" = None,
        webhook_secret: str | None = None,
        signature_header: str = DEFAULT_SIGNATURE_HEADER,
        timestamp_header: str = DEFAULT_TIMESTAMP_HEADER,
        timestamp_tolerance: float = DEFAULT_TIMESTAMP_TOLERANCE,
        polling_config: PollingConfig | None = None,
    ) -> None:
        self._token = token
        self.session: BaseSession = session(MAINNET, timeout)
        self._kwargs: dict[str, object] = {"paysell": self}

        WebhookHandler.__init__(
            self,
            webhook_manager,
            webhook_secret,
            signature_header,
            timestamp_header,
            timestamp_tolerance,
        )
        PollingManager.__init__(self, polling_config or PollingConfig())

    async def __call__(
        self,
        method: "PaysellMethod[_PaysellType]",
    ) -> "_PaysellType":
        """
        Perform a raw API request.

        Prefer the typed shortcuts (:meth:`create_invoice`,
        :meth:`get_invoice`, :meth:`cancel_invoice`) — this is the low-level
        entry point they're built on.

        :param method: a :class:`aiopaysell._methods.PaysellMethod` instance.
        :return: the method's return type.
        """
        loggers.client.debug(
            "Requesting %s %s",
            method.__http_method__,
            method.build_path(),
        )
        return await self.session.request(self._token, self, method)

    async def close(self) -> None:
        """Close the underlying HTTP session and release its connections."""
        await self.session.close()

    async def __aenter__(self) -> "Paysell":
        return self

    async def __aexit__(
        self,
        exc_type: "type[BaseException] | None",
        exc: BaseException | None,
        traceback: "TracebackType | None",
    ) -> None:
        await self.close()

    def include_router(self, router: "WebhookRouter | PollingRouter") -> None:
        """
        Include a standalone router built with decorators into this client.

        :param router: a :class:`aiopaysell.webhook.WebhookRouter` or
            :class:`aiopaysell.polling.PollingRouter`.
        """
        if isinstance(router, WebhookRouter):
            self._webhook_router.include_router(router)
        elif isinstance(router, PollingRouter):
            self._polling_router.include_router(router)
        else:
            msg = f"Router {router} is neither a WebhookRouter nor a PollingRouter"
            raise TypeError(msg)

    def include_routers(self, *routers: "WebhookRouter | PollingRouter") -> None:
        """Include multiple routers at once."""
        for router in routers:
            self.include_router(router)

    def __setitem__(self, key: str, value: object) -> None:
        self._kwargs[key] = value

    def __getitem__(self, key: str) -> object:
        return self._kwargs[key]

    def __delitem__(self, key: str) -> None:
        del self._kwargs[key]

    def __contains__(self, key: str) -> bool:
        return key in self._kwargs
