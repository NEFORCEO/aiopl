import ssl
from typing import TYPE_CHECKING, cast

import certifi
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from aiopaysell.__meta__ import __version__
from aiopaysell.exceptions import APITimeoutError

from .base import BaseSession

if TYPE_CHECKING:
    import aiopaysell
    from aiopaysell._methods import PaysellMethod
    from aiopaysell.client.network import Network
    from aiopaysell.types import _PaysellType


class AiohttpSession(BaseSession):
    """
    HTTP session based on `aiohttp <https://docs.aiohttp.org/en/stable/>`_.

    The default session used by :class:`aiopaysell.Paysell`.
    """

    def __init__(self, network: "Network", timeout: float = 30) -> None:
        super().__init__(network, timeout)

    async def request(
        self,
        token: str,
        client: "aiopaysell.Paysell",
        method: "PaysellMethod[_PaysellType]",
    ) -> "_PaysellType":
        """Make an HTTP request via aiohttp."""
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"aiopaysell/{__version__}",
        }
        if method.__requires_auth__:
            headers["Authorization"] = f"Bearer {token}"
        url = self.network.url(method)
        async with ClientSession(
            timeout=ClientTimeout(self.timeout),
            connector=TCPConnector(ssl_context=ssl_context),
        ) as session:
            try:
                if method.__http_method__ == "GET":
                    resp = await session.get(url, headers=headers)
                else:
                    resp = await session.post(
                        url,
                        data=method.model_dump_json(exclude_none=True),
                        headers=headers,
                    )
            except TimeoutError as e:
                raise APITimeoutError(method, self.timeout) from e
            content = await resp.text()
            status = resp.status
            response_headers = dict(resp.headers)
        return cast(
            "_PaysellType",
            self._check_response(client, method, status, content, response_headers),
        )
