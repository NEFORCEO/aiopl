import asyncio

from aiopaysell import Paysell


async def main() -> None:
    pay = Paysell("sk_live_YOUR_KEY")

    invoice = await pay.create_invoice(
        "USDT_TON",
        5,
        order_id="order-1042",
        description="Pro subscription",
    )
    print(f"pay: {invoice.payment_url}")

    invoice = await pay.get_invoice(invoice)
    print(f"status: {invoice.status}")


if __name__ == "__main__":
    asyncio.run(main())
