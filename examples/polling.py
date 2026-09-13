import asyncio

from aiopaysell import Paysell, PollingConfig


async def main() -> None:
    pay = Paysell("sk_live_YOUR_KEY", polling_config=PollingConfig(delay=3))

    @pay.invoice_paid()
    async def on_paid(invoice) -> None:
        print(f"invoice {invoice.invoice_id} is {invoice.status}")

    @pay.invoice_expired()
    async def on_expired(invoice) -> None:
        print(f"invoice {invoice.invoice_id} expired unpaid")

    invoice = await pay.create_invoice("TON", 1.5, order_id="order-1")
    print(f"pay: {invoice.payment_url}")
    invoice.poll()

    await pay.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
