import asyncio
from contextlib import asynccontextmanager

import aiohttp
import pytest

from aiopaysell import MAINNET, Paysell
from aiopaysell.client.network import Network
from aiopaysell.exceptions import APITimeoutError, NetworkError


@pytest.fixture
def client() -> Paysell:
    return Paysell("sk_live_abc123")


def test_default_network_is_mainnet(client: Paysell) -> None:
    assert client.network is MAINNET
    assert client.session.network is MAINNET


def test_network_can_be_overridden() -> None:
    """No way to point at a local backend meant every integration test hit prod."""
    local = Network(name="local", base="http://127.0.0.1:8000/merchant/v1")
    client = Paysell("sk_test_abc123", network=local)
    assert client.network is local
    assert client.session.network is local


async def test_client_session_is_reused_across_requests(client: Paysell) -> None:
    """A new ClientSession + SSL context per request defeats connection pooling."""
    first = client.session._get_client_session()  # noqa: SLF001
    second = client.session._get_client_session()  # noqa: SLF001
    assert first is second
    await client.close()


async def test_close_releases_the_session(client: Paysell) -> None:
    session = client.session._get_client_session()  # noqa: SLF001
    assert not session.closed
    await client.close()
    assert session.closed


async def test_close_is_a_no_op_if_never_used(client: Paysell) -> None:
    await client.close()  # must not raise even though no request was ever made


async def test_context_manager_closes_on_exit() -> None:
    async with Paysell("sk_live_abc123") as pay:
        session = pay.session._get_client_session()  # noqa: SLF001
        assert not session.closed
    assert session.closed


class _FakeRequestCM:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def __aenter__(self) -> None:
        raise self._exc

    async def __aexit__(self, *exc_info: object) -> None:
        return None


async def test_asyncio_timeout_is_wrapped(
    client: Paysell,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """aiohttp raises asyncio.TimeoutError, not the builtin, pre-3.11 — must still be caught."""
    session = client.session._get_client_session()  # noqa: SLF001
    monkeypatch.setattr(
        session,
        "request",
        lambda *a, **kw: _FakeRequestCM(asyncio.TimeoutError()),
    )
    method = client.GetInvoiceMethod(invoice_id="abc")
    with pytest.raises(APITimeoutError):
        await client.session.request("sk_live_x", client, method)
    await client.close()


async def test_connection_error_is_wrapped(
    client: Paysell,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = client.session._get_client_session()  # noqa: SLF001
    monkeypatch.setattr(
        session,
        "request",
        lambda *a, **kw: _FakeRequestCM(
            aiohttp.ClientConnectorError(connection_key=None, os_error=OSError("boom")),
        ),
    )
    method = client.GetInvoiceMethod(invoice_id="abc")
    with pytest.raises(NetworkError):
        await client.session.request("sk_live_x", client, method)
    await client.close()
