from typing import TYPE_CHECKING, Annotated

from annotated_doc import Doc

from aiopaysell import loggers
from aiopaysell._methods import Methods
from aiopaysell.client.network import MAINNET, Network
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
    """Client class providing the Paysell API."""

    def __init__(
        self,
        token: Annotated[str, Doc("Paysell API key.")],
        *,
        network: Annotated[
            Network,
            Doc(
                """
                Which server to talk to. Defaults to `aiopaysell.MAINNET`
                (`https://paysell.me/api/merchant/v1`).

                Point it at a local backend for integration tests —
                `Network(name="local", base="http://127.0.0.1:8000/merchant/v1")`
                matches a `client_area` checkout run without nginx in front
                of it, so no `/api` prefix.
                """
            ),
        ] = MAINNET,
        session: Annotated[
            "type[BaseSession]",
            Doc(
                "HTTP session class. Defaults to "
                "`aiopaysell.client.session.AiohttpSession`."
            ),
        ] = AiohttpSession,
        timeout: Annotated[float, Doc("HTTP request timeout in seconds.")] = 30,
        webhook_manager: Annotated[
            "WebhookManager | None",
            Doc(
                """
                A webhook manager (`aiopaysell.webhook.AiohttpManager`, etc.)
                to receive updates through your web server.
                """
            ),
        ] = None,
        webhook_secret: Annotated[
            str | None,
            Doc(
                """
                The webhook secret shown once when you created the API key —
                a different value from `token`. Required whenever
                `webhook_manager` is set; without it, no delivery can be
                verified.
                """
            ),
        ] = None,
        signature_header: Annotated[
            str,
            Doc(
                "Header carrying the webhook HMAC signature. "
                "See `aiopaysell.webhook.DEFAULT_SIGNATURE_HEADER`."
            ),
        ] = DEFAULT_SIGNATURE_HEADER,
        timestamp_header: Annotated[
            str,
            Doc(
                "Header carrying the unix-seconds timestamp that's part of "
                "the signed string. See `aiopaysell.webhook.DEFAULT_TIMESTAMP_HEADER`."
            ),
        ] = DEFAULT_TIMESTAMP_HEADER,
        timestamp_tolerance: Annotated[
            float,
            Doc(
                """
                Max allowed clock skew between that timestamp and now, in
                seconds, before a webhook is rejected as a possible replay.
                """
            ),
        ] = DEFAULT_TIMESTAMP_TOLERANCE,
        polling_config: Annotated[
            PollingConfig | None,
            Doc("Configuration for `aiopaysell.Paysell.start_polling`."),
        ] = None,
    ) -> None:
        self._token = token
        self.network = network
        self.session: BaseSession = session(network, timeout)
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
        method: Annotated[
            "PaysellMethod[_PaysellType]",
            Doc("A `aiopaysell._methods.PaysellMethod` instance."),
        ],
    ) -> "_PaysellType":
        """
        Perform a raw API request.

        Prefer the typed shortcuts (`create_invoice`, `get_invoice`,
        `cancel_invoice`) — this is the low-level entry point they're built on.

        Returns:
            The method's return type.
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

    def include_router(
        self,
        router: Annotated[
            "WebhookRouter | PollingRouter",
            Doc(
                "A `aiopaysell.webhook.WebhookRouter` or "
                "`aiopaysell.polling.PollingRouter`."
            ),
        ],
    ) -> None:
        """Include a standalone router built with decorators into this client."""
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
