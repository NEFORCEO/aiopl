from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import Field

from aiopaysell.tools import normalize_amount
from aiopaysell.types import Invoice

from .base import PaysellMethod

if TYPE_CHECKING:
    from aiopaysell.client.client import Paysell
    from aiopaysell.enums import Asset, LiteralAsset


class CreateInvoice:
    """POST /invoices."""

    class CreateInvoiceMethod(PaysellMethod[Invoice]):
        __return_type__ = Invoice
        __method_name__ = "createInvoice"
        __http_method__ = "POST"

        asset: str
        amount: str = Field(pattern=r"^[0-9]+(\.[0-9]+)?$")
        order_id: str | None = Field(None, max_length=200)
        description: str | None = Field(None, max_length=1000)
        ttl_minutes: int | None = Field(None, ge=1, le=1440)
        idempotency_key: str | None = Field(None, max_length=200)

        def build_path(self) -> str:
            return "/invoices"

    async def create_invoice(  # type: ignore[misc]
        self: "Paysell",
        asset: "Asset | LiteralAsset | str",
        amount: "str | int | float | Decimal",
        *,
        order_id: str | None = None,
        description: str | None = None,
        ttl_minutes: int | None = None,
        idempotency_key: str | None = None,
    ) -> Invoice:
        """
        createInvoice method.

        Create an invoice with its own receiving address. Redirect the buyer
        to the returned ``payment_url`` — amount, address, QR, countdown and
        live status are all handled for you on that page.

        :param asset: ``"TON"`` or ``"USDT_TON"``.
        :param amount: The amount to charge, in the coin's **normal units**
            — like on an exchange, not smallest units. Pass a number —
            ``5``, ``1.5``, ``Decimal("1.5")`` — and it's formatted for you
            via :func:`aiopaysell.tools.normalize_amount`; a :class:`str` is
            sent through unchanged (it must already look like ``"5"`` or
            ``"1.5"``). No more decimal places than the asset supports (TON
            9, USDT_TON 6). Sending smallest units by mistake (e.g.
            ``"5000000"`` for 5 USDT) is caught by the invoice's upper limit,
            not silently accepted.
        :param order_id: *Optional*. Up to 200 characters. Your own
            reference; comes back in every webhook so you can match the
            payment to an order.
        :param description: *Optional*. Up to 1000 characters. Shown to the
            buyer on the payment page.
        :param ttl_minutes: *Optional*. Invoice lifetime, 1-1440 minutes.
            Omit it and the server's default applies (2 hours today).
        :param idempotency_key: *Optional*. Up to 200 characters. Reuse the
            same value on retries (e.g. after a 502) to get the existing
            invoice back instead of a duplicate. Generate it once per order
            and keep it — don't mint a fresh one on every call. This is a
            body field; the ``Idempotency-Key`` header is not read.
        :return: the created :class:`aiopaysell.types.Invoice`.
        :raise ValueError: ``amount`` has more decimal places than ``asset`` supports.
        :raise aiopaysell.exceptions.InvalidRequestError: amount outside the
            invoice's limits, or a malformed request.
        :raise aiopaysell.exceptions.RateLimitError: too many invoices this
            hour, or too many open at once.
        """
        if not isinstance(amount, str):
            amount = normalize_amount(amount, asset)
        return await self(self.CreateInvoiceMethod(**locals()))
