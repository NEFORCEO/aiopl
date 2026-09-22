<p align="center">
  <strong><em>Async Python client for Paysell — accept TON & USDT with invoices, webhooks, and a polling fallback.</em></strong>
</p>

<p align="center">
<a href="https://github.com/paysell/aiopl/actions/workflows/release.yml" target="_blank">
    <img src="https://github.com/paysell/aiopl/actions/workflows/release.yml/badge.svg" alt="Release">
</a>
<a href="https://pypi.org/project/aiopaysell" target="_blank">
    <img src="https://img.shields.io/pypi/v/aiopaysell?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://www.python.org/" target="_blank">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
</a>
<a href="https://pypi.org/project/aiopaysell" target="_blank">
    <img src="https://img.shields.io/pypi/dm/aiopaysell?color=%2334D058&label=downloads" alt="Monthly downloads">
</a>
<a href="https://pydantic.dev" target="_blank">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json" alt="Pydantic v2">
</a>
<a href="LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</a>
<a href="https://github.com/paysell/aiopl" target="_blank">
    <img src="https://img.shields.io/github/stars/paysell/aiopl?style=social" alt="GitHub Stars">
</a>
</p>

---

**Documentation**: <a href="https://aiopaysell.readthedocs.io/" target="_blank">https://aiopaysell.readthedocs.io/</a>

**Source Code**: <a href="https://github.com/paysell/aiopl" target="_blank">https://github.com/paysell/aiopl</a>

**Paysell API docs**: <a href="https://paysell.me/docs" target="_blank">https://paysell.me/docs</a>

---

**aiopaysell** wraps the [Paysell](https://paysell.me/docs) merchant API: open an invoice, redirect the buyer to a hosted checkout page, and get a signed webhook the moment it's paid. Built with pydantic models throughout, a decorator-based event router in the style of aiogram, and a polling fallback for when a webhook can't reach you.

Key features:

- **Typed** — full type annotations and pydantic v2 models for every request and response; `mypy`-clean.
- **Async** — built on `aiohttp`, with a pooled, reusable connection instead of one per call.
- **Webhooks** — signature and replay-window verification (`HMAC-SHA256`, ±5 min) done for you, for both `payment.credited` and `payment.rejected`; handlers via `@pay.payment_credited(...)`, filterable with [magic-filter](https://github.com/pypa/magic-filter).
- **Polling** — a fallback for local dev or a missed webhook, tracking each invoice's real `expires_at` instead of a guessed timeout.
- **Honest amounts** — pass `5` or `Decimal("1.5")` for normal units; the wire format, decimal-place validation, and the webhook's smallest-unit integers are handled for you.
- **Typed errors** — one exception class per HTTP status, carrying the API's `code`/`message`, `Retry-After`, and field-level validation detail.

## Requirements

Python 3.10+

**aiopaysell** depends on:

- <a href="https://docs.aiohttp.org/en/stable/" target="_blank"><code>aiohttp</code></a> — async HTTP transport.
- <a href="https://docs.pydantic.dev/" target="_blank"><code>pydantic</code></a> — request/response models and validation.
- <a href="https://github.com/pypa/magic-filter" target="_blank"><code>magic-filter</code></a> — event filters (`F.status == "paid"`).
- <a href="https://certifiio.readthedocs.io/" target="_blank"><code>certifi</code></a> — CA bundle for TLS.

## Installation

```console
$ pip install aiopaysell

---> 100%
```

Using the FastAPI webhook manager instead of aiohttp's:

```console
$ pip install aiopaysell[fastapi]
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
- **`Paysell` defaults to Paysell's one production network** — pass `network=` (a `aiopaysell.client.network.Network`) to point at a local backend for integration tests.

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
