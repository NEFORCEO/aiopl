from http import HTTPStatus
from typing import TYPE_CHECKING

from .base import WebhookManager

if TYPE_CHECKING:
    from fastapi import APIRouter, FastAPI  # noqa: F401

    from .base import WebServerHandler


class FastAPIManager(WebhookManager["FastAPI | APIRouter"]):
    """
    FastAPI webhook manager.

    Webhook manager based on `FastAPI <https://fastapi.tiangolo.com/>`_.
    """

    def register_handler(self, feed_update: "WebServerHandler") -> None:
        """Register the webhook route on the FastAPI app or router."""
        try:
            from fastapi import Request
            from fastapi.responses import JSONResponse
        except ModuleNotFoundError as e:
            msg = "FastAPI is not installed. Run `pip install aiopaysell[fastapi]`."
            raise RuntimeError(msg) from e

        async def handle(request: Request) -> JSONResponse:
            ok = await feed_update(await request.body(), dict(request.headers))
            return JSONResponse(
                {"ok": ok},
                status_code=HTTPStatus.OK if ok else HTTPStatus.BAD_REQUEST,
            )

        self._app.add_api_route(self._path, handle, methods=["POST"])
