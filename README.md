<p align="center">
  <h1 align="center">aiopaysell</h1>
</p>

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![Aiohttp](https://img.shields.io/badge/aiohttp-v3-2c5bb4?logo=aiohttp)](https://docs.aiohttp.org/en/stable/)
[![Code linter: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)

**aiopaysell** is an async Python client for the [Paysell](https://pay.saleprofit.dev/docs) payment API — accept TON & USDT on TON with invoices, webhooks, and a polling fallback.

> ## [API documentation](https://pay.saleprofit.dev/docs)
>
> ## [Repository](https://github.com/NEFORCEO/aiopl)

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

```python
from aiohttp import web
from magic_filter import F
from aiopaysell import Paysell
from aiopaysell.webhook import AiohttpManager

app = web.Application()
pay = Paysell(
    "sk_live_YOUR_KEY",
    webhook_manager=AiohttpManager(app, path="/webhooks/paysell"),
)


@pay.payment_credited(F.status == "paid")
async def on_paid(payment):
    print(f"order {payment.order_id} paid, {payment.credited} credited")


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

Webhook and polling events live on separate routers (`payment_credited` vs. `invoice_paid`/`invoice_expired`/`invoice_cancelled`) — running both is safe, just make handlers idempotent since the same payment could be reported by each.

More in `examples/`: FastAPI webhooks, a standalone router for splitting handlers across modules, polling.

## Good to know

- **`create_invoice(amount=...)` takes human units** — `5`, `5.5`, `Decimal("5.5")` — and converts them to the wire format for you. Pass a `str` if you already have the raw smallest-unit value and want it sent through unchanged. Don't mix the two up: `amount=5` is always 5 whole coins, never smallest units.
- **The wire format itself is smallest-unit strings, never floats** — `Invoice.amount` on a response stays a `str` for that reason; use `Invoice.amount_int` for an `int`.
- **`idempotency_key`** is yours to generate and persist per order; the library won't invent one for you, since its entire value is surviving a retry with the *same* key.
- **The webhook signature header isn't named in the docs** — only the algorithm is (HMAC-SHA256 hex, `sha256=` prefix, raw body). `aiopaysell` defaults to `X-Paysell-Signature`; confirm the real name in your shop's settings and pass `Paysell(..., signature_header="...")` if it differs.
- **There's a single network** (`https://pay.saleprofit.dev`) — no test/live split to configure, the client always talks to it.

## Errors

| Status | Exception |
| --- | --- |
| 401 | `AuthenticationError` |
| 404 | `NotFoundError` |
| 409 | `ConflictError` |
| 422 | `InvalidRequestError` |
| 429 | `RateLimitError` |
| 502 | `BadGatewayError` (safe to retry with the same `idempotency_key`) |

All inherit `aiopaysell.exceptions.APIError` → `PaysellError`.

## License

MIT
# aiopl
