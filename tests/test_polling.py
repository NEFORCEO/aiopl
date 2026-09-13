import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from aiopaysell import Paysell, PollingConfig
from aiopaysell.exceptions import NotFoundError
from aiopaysell.types import Invoice


@pytest.fixture
def client() -> Paysell:
    return Paysell("sk_live_abc123", polling_config=PollingConfig(delay=0))


def _invoice(pay: Paysell, **overrides: object) -> Invoice:
    data = {
        "invoice_id": "abc-123",
        "address": "UQtest",
        "asset": "TON",
        "amount": "1.5",
        "amount_minor": "1500000000",
        "status": "pending",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=2),
        "created_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return Invoice.model_validate(data, context={"client": pay})


async def test_timed_out_but_still_pending_does_not_fire_expired(client: Paysell) -> None:
    """The exact bug: giving up on a poll deadline must not claim the invoice expired."""
    invoice = _invoice(
        client,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),  # already past deadline
        status="pending",
    )
    client._poll_invoice(invoice)  # noqa: SLF001

    fired = []

    @client.invoice_expired()
    async def on_expired(inv: Invoice) -> None:
        fired.append(inv)

    # Feed back the same (still pending) invoice: deadline has passed.
    await client._handle_invoice(invoice)  # noqa: SLF001

    assert fired == []
    assert "abc-123" not in client._invoice_tasks  # noqa: SLF001


async def test_actually_expired_status_fires_expired(client: Paysell) -> None:
    invoice = _invoice(client, status="pending")
    client._poll_invoice(invoice)  # noqa: SLF001

    fired = []

    @client.invoice_expired()
    async def on_expired(inv: Invoice) -> None:
        fired.append(inv.invoice_id)

    expired_invoice = _invoice(client, status="expired")
    await client._handle_invoice(expired_invoice)  # noqa: SLF001

    assert fired == ["abc-123"]


async def test_deadline_defaults_to_invoice_expires_at(client: Paysell) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=90)
    invoice = _invoice(client, expires_at=expires_at)
    client._poll_invoice(invoice)  # noqa: SLF001
    task = client._invoice_tasks["abc-123"]  # noqa: SLF001
    assert task.deadline == expires_at


async def test_underpaid_extends_deadline_by_24h(client: Paysell) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    invoice = _invoice(client, expires_at=expires_at, status="pending")
    client._poll_invoice(invoice)  # noqa: SLF001

    underpaid_invoice = _invoice(client, expires_at=expires_at, status="underpaid")
    await client._handle_invoice(underpaid_invoice)  # noqa: SLF001

    task = client._invoice_tasks["abc-123"]  # noqa: SLF001
    assert task.deadline == expires_at + timedelta(hours=24)


async def test_fixed_timeout_override_still_works() -> None:
    pay = Paysell("sk_live_x", polling_config=PollingConfig(delay=0, timeout=60))
    before = datetime.now(timezone.utc)
    invoice = _invoice(pay, expires_at=datetime.now(timezone.utc) + timedelta(hours=2))
    pay._poll_invoice(invoice)  # noqa: SLF001
    task = pay._invoice_tasks["abc-123"]  # noqa: SLF001
    assert before + timedelta(seconds=59) <= task.deadline <= before + timedelta(seconds=61)


async def test_not_found_stops_polling_immediately(client: Paysell) -> None:
    """A 404 must drop the task at once, not retry it forever."""
    invoice = _invoice(client)
    client._poll_invoice(invoice)  # noqa: SLF001

    calls = {"n": 0}

    async def failing_get_invoice(invoice_id: str) -> Invoice:
        calls["n"] += 1
        raise NotFoundError(client.GetInvoiceMethod(invoice_id=invoice_id), "not_found", "gone")

    tasks = client._invoice_tasks  # noqa: SLF001
    task = asyncio.create_task(
        client._start_polling(failing_get_invoice, client._handle_invoice, tasks),  # noqa: SLF001
    )
    for _ in range(50):
        if not tasks:
            break
        await asyncio.sleep(0.01)
    task.cancel()

    assert tasks == {}
    assert calls["n"] >= 1
    # A permanent 404 must not be retried more than once or twice, not forever.
    assert calls["n"] < 10
