from http import HTTPStatus
from typing import TYPE_CHECKING

from aiohttp.web import json_response

from .base import WebhookManager

if TYPE_CHECKING:
    from aiohttp.web import Application, Request, Response  # noqa: F401

    from .base import WebServerHandler


class AiohttpManager(WebhookManager["Application"]):
    """
    aiohttp webhook manager.

    Webhook manager based on `aiohttp <https://docs.aiohttp.org/en/stable/web_reference.html>`_.
    """

    def register_handler(self, feed_update: "WebServerHandler") -> None:
        """Register the webhook route on the aiohttp application."""

        async def handle(request: "Request") -> "Response":
            ok = await feed_update(await request.read(), dict(request.headers))
            return json_response(
                {"ok": ok},
                status=HTTPStatus.OK if ok else HTTPStatus.BAD_REQUEST,
            )

        self._app.router.add_post(self._path, handle)
