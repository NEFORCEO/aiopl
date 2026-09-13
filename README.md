<p align="center">
  <h1 align="center">aiopaysell</h1>
</p>

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![Aiohttp](https://img.shields.io/badge/aiohttp-v3-2c5bb4?logo=aiohttp)](https://docs.aiohttp.org/en/stable/)
[![Code linter: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)

**aiopaysell** is an async Python client for the [Paysell](https://paysell.me/docs) payment API — accept TON & USDT on TON with invoices, webhooks, and a polling fallback.

> ## [API documentation](https://paysell.me/docs)

## Install

```bash
pip install aiopaysell
# pip install aiopaysell[fastapi]   # if you use the FastAPI webhook manager
```

## Quick start

```python
import asyncio
from aiopaysell import Paysell


async def main():
    pay = Paysell("sk_live_YOUR_KEY")

    invoice = await pay.create_invoice("TON", 5, order_id="order-1042")
    print(f"pay: {invoice.payment_url}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Webhook example

`webhook_secret` is **not** your API key — it's a separate secret shown once,
next to the key, when you create it. Without it no delivery can be verified,
and `payment_credited` never fires.

```python
from aiohttp import web
from magic_filter import F
from aiopaysell import Paysell
from aiopaysell.webhook import AiohttpManager

app = web.Application()
pay = Paysell(
    "sk_live_YOUR_KEY",
    webhook_manager=AiohttpManager(app, path="/webhooks/paysell"),
    webhook_secret="YOUR_WEBHOOK_SECRET",
)


@pay.payment_credited(F.status == "paid")
async def on_paid(payment):
    print(f"order {payment.order_id} paid, {payment.credited_int} credited")


@pay.payment_rejected()
async def on_rejected(payment):
    print(f"order {payment.order_id}: deposit rejected ({payment.reason})")


if __name__ == "__main__":
    web.run_app(app, port=8080)
```

FastAPI works the same way via `aiopaysell.webhook.FastAPIManager`. No webhooks in local dev? Poll instead:

```python
@pay.invoice_paid()
async def on_paid(invoice):
    print(invoice.status)


invoice = await pay.create_invoice("TON", 1.5)
invoice.poll()
await pay.start_polling()
```

Webhook and polling events live on separate routers (`payment_credited`/`payment_rejected` vs. `invoice_paid`/`invoice_expired`/`invoice_cancelled`) — running both is safe, just make handlers idempotent since the same payment could be reported by each.

Need your own checkout page instead of redirecting to `payment_url`? `pay.get_public_invoice(invoice_id)` reads the same unauthenticated endpoint the hosted page uses — no API key needed.

More in `examples/`: FastAPI webhooks, a standalone router for splitting handlers across modules, polling, a public-invoice checkout.

## Good to know

- **`webhook_secret` is required for webhooks to work at all.** It's shown once when the key is created, separately from the key itself. Passing `webhook_manager=` without it raises immediately; leaving both out (polling-only usage) is fine.
- **`create_invoice(amount=...)` takes normal units, like on an exchange** — `5`, `1.5`, `Decimal("1.5")` — and formats them for you (decimal places validated against the coin). Pass a `str` if you already have it formatted and want it sent through unchanged.
- **The REST API and the webhook body disagree about units, on purpose.** `Invoice.amount` is normal units, exactly what you sent; `Invoice.amount_minor` is the same as an integer smallest-unit string — use `Invoice.amount_minor_int`. Webhook payloads (`PaymentCredited.amount`, `.credited`, `.fee`) are smallest-unit integers throughout — use the matching `*_int` properties.
- **`idempotency_key`** is yours to generate and persist per order; the library won't invent one for you, since its entire value is surviving a retry with the *same* key.
- **The webhook signature is `HMAC-SHA256(secret, "{timestamp}.{raw_body}")`**, header names `X-Paysell-Signature` / `X-Paysell-Timestamp`. `aiopaysell` verifies both, including a ±5 minute replay window, before any handler runs.
- **There's a single network** (`https://paysell.me`) — no test/live split to configure, the client always talks to it.

## Errors

| Status | Exception |
| --- | --- |
| 401 | `AuthenticationError` |
| 404 | `NotFoundError` |
| 409 | `ConflictError` |
| 422 | `InvalidRequestError` |
| 429 | `RateLimitError` (`.retry_after` holds the `Retry-After` header, in seconds, when present) |
| 502 | `BadGatewayError` (safe to retry with the same `idempotency_key`) |

All inherit `aiopaysell.exceptions.APIError` → `PaysellError`.

## License

MIT
