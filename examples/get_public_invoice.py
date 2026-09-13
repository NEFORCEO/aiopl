"""
Building your own checkout page instead of redirecting to `payment_url`.

get_public_invoice() needs no API key — it's the same unauthenticated
endpoint the hosted checkout page itself polls.
"""

import asyncio

from aiopaysell import Paysell


async def main() -> None:
    pay = Paysell("sk_live_YOUR_KEY")

    invoice = await pay.create_invoice("TON", 1.5, order_id="order-1")

    # Anything that only has the invoice_id (a customer's browser, a
    # separate frontend service) can poll this without your API key:
    public = await pay.get_public_invoice(invoice.invoice_id)
    print(f"send {public.amount} {public.asset} to {public.address}")
    print(f"status: {public.status} ({public.paid or '0'} received so far)")

    # amount_minor_int is what a `ton://transfer` deep link's `amount` takes.
    print(f"ton://transfer/{public.address}?amount={public.amount_minor_int}")


if __name__ == "__main__":
    asyncio.run(main())
