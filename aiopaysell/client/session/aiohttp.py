import asyncio
import ssl
from typing import TYPE_CHECKING, cast

import aiohttp
import certifi
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from aiopaysell.__meta__ import __version__
from aiopaysell.exceptions import APITimeoutError, NetworkError

from .base import BaseSession

if TYPE_CHECKING:
    import aiopaysell
    from aiopaysell._methods import PaysellMethod
    from aiopaysell.client.network import Network
    from aiopaysell.types import _PaysellType


class AiohttpSession(BaseSession):
    """
    HTTP session based on `aiohttp <https://docs.aiohttp.org/en/stable/>`_.

    Lazily opens one persistent :class:`aiohttp.ClientSession` and reuses it
    across requests instead of opening a new connection (and TLS handshake)
    per call. Call :meth:`close` when you're done — or use
    :class:`aiopaysell.Paysell` as an async context manager, which does it
    for you.
    """

    def __init__(self, network: "Network", timeout: float = 30) -> None:
        super().__init__(network, timeout)
        self._client_session: ClientSession | None = None

    def _get_client_session(self) -> ClientSession:
        if self._client_session is None or self._client_session.closed:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            self._client_session = ClientSession(
                timeout=ClientTimeout(self.timeout),
                connector=TCPConnector(ssl=ssl_context),
            )
        return self._client_session

    async def close(self) -> None:
        """Close the underlying connection pool."""
        if self._client_session is not None and not self._client_session.closed:
            await self._client_session.close()

    async def request(
        self,
        token: str,
        client: "aiopaysell.Paysell",
        method: "PaysellMethod[_PaysellType]",
    ) -> "_PaysellType":
        """Make an HTTP request via aiohttp."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"aiopaysell/{__version__}",
        }
        if method.__requires_auth__:
            headers["Authorization"] = f"Bearer {token}"
        url = self.network.url(method)
        session = self._get_client_session()
        data = (
            None
            if method.__http_method__ == "GET"
            else method.model_dump_json(exclude_none=True)
        )
        try:
            async with session.request(
                method.__http_method__,
                url,
                data=data,
                headers=headers,
            ) as resp:
                content = await resp.text()
                status = resp.status
                response_headers = dict(resp.headers)
        except asyncio.TimeoutError as e:
            # Not `except TimeoutError` — on Python 3.10, asyncio.TimeoutError
            # and the builtin TimeoutError are unrelated classes; aiohttp
            # raises the former. They're the same class from 3.11 on, so this
            # catches it correctly on every supported version.
            raise APITimeoutError(method, self.timeout) from e
        except aiohttp.ClientError as e:
            raise NetworkError(method, e) from e
        return cast(
            "_PaysellType",
            self._check_response(client, method, status, content, response_headers),
        )
