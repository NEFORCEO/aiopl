import asyncio

from aiohttp import web
from magic_filter import F

from aiopaysell import Paysell
from aiopaysell.webhook import AiohttpManager

app = web.Application()
pay = Paysell(
    "sk_live_YOUR_KEY",
    webhook_manager=AiohttpManager(app, path="/webhooks/paysell"),
)

# Real code should also deduplicate on `payment.event_id` — see the docs'
# "A complete receiver" for a full example with storage-backed dedup.


@pay.payment_credited(F.status == "paid")
async def on_paid(payment) -> None:
    # payment.order_id, payment.credited_int, payment.tx_hash, ...
    print(f"order {payment.order_id} paid in full, {payment.credited_int} credited")


@pay.payment_credited(F.status.in_({"overpaid", "underpaid"}))
async def on_mismatch(payment) -> None:
    print(f"order {payment.order_id}: {payment.status} ({payment.amount_int} sent)")


@pay.payment_rejected()
async def on_rejected(payment) -> None:
    # A held deposit was declined — release nothing, but let support know.
    print(f"order {payment.order_id}: deposit rejected ({payment.reason})")


if __name__ == "__main__":
    web.run_app(app, port=8080)
