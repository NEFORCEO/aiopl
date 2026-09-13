"""Splitting handlers across modules with a standalone router, like aiogram's Router/Dispatcher."""

import asyncio

from magic_filter import F

from aiopaysell import Paysell
from aiopaysell.webhook import WebhookRouter

# orders.py
orders_router = WebhookRouter(name="orders")


@orders_router.payment_credited(F.status == "paid")
async def release_goods(payment) -> None:
    print(f"releasing goods for order {payment.order_id}")


# app.py
async def main() -> None:
    pay = Paysell("sk_live_YOUR_KEY")
    pay.include_router(orders_router)


if __name__ == "__main__":
    asyncio.run(main())
