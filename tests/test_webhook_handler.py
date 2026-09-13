import hashlib
import hmac
import json
import time

import pytest
from aiohttp import web

from aiopaysell import Paysell
from aiopaysell.webhook import AiohttpManager


def _sign(body: bytes, secret: str, timestamp: str) -> str:
    signed = timestamp.encode() + b"." + body
    return "sha256=" + hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def test_webhook_manager_without_secret_raises() -> None:
    """The exact bug report: webhooks must be signed with webhook_secret, not the API key."""
    app = web.Application()
    with pytest.raises(ValueError, match="webhook_secret"):
        Paysell("sk_live_x", webhook_manager=AiohttpManager(app))


async def test_feed_update_end_to_end() -> None:
    api_key = "sk_live_x"
    webhook_secret = "whsec_totally_different_from_the_key"
    pay = Paysell(api_key, webhook_secret=webhook_secret)

    received = []

    @pay.payment_credited()
    async def on_paid(payment) -> None:
        received.append(payment.order_id)

    body = json.dumps(
        {
            "event_id": "99f74f58-efbb-4af1-b0a3-76b0073f9e6b",
            "type": "payment.credited",
            "data": {"order_id": "order-1", "status": "paid"},
        },
    ).encode()
    ts = str(int(time.time()))

    good_sig = _sign(body, webhook_secret, ts)
    ok = await pay.feed_update(body, {"X-Paysell-Signature": good_sig, "X-Paysell-Timestamp": ts})
    assert ok is True
    assert received == ["order-1"]

    bad_sig = _sign(body, api_key, ts)  # the pre-fix behavior
    received.clear()
    rejected = await pay.feed_update(
        body,
        {"X-Paysell-Signature": bad_sig, "X-Paysell-Timestamp": ts},
    )
    assert rejected is False
    assert received == []


async def test_feed_update_without_secret_configured_fails_closed() -> None:
    pay = Paysell("sk_live_x")  # no webhook_manager, no webhook_secret
    body = b'{"event_id": "1", "type": "payment.credited", "data": {}}'
    ts = str(int(time.time()))
    sig = _sign(body, "whatever", ts)
    ok = await pay.feed_update(body, {"X-Paysell-Signature": sig, "X-Paysell-Timestamp": ts})
    assert ok is False
