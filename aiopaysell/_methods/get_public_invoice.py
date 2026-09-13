from typing import TYPE_CHECKING

from pydantic import Field

from aiopaysell.types import PublicInvoice

from .base import PaysellMethod

if TYPE_CHECKING:
    from aiopaysell.client.client import Paysell
    from aiopaysell.types import Invoice


class ReadPublicInvoice:
    """GET /public/invoices/{invoice_id} — no API key required."""

    class GetPublicInvoiceMethod(PaysellMethod[PublicInvoice]):
        __return_type__ = PublicInvoice
        __method_name__ = "getPublicInvoice"
        __http_method__ = "GET"
        __requires_auth__ = False

        invoice_id: str = Field(exclude=True)

        def build_path(self) -> str:
            return f"/public/invoices/{self.invoice_id}"

    async def get_public_invoice(  # type: ignore[misc]
        self: "Paysell",
        invoice: "str | Invoice | PublicInvoice",
    ) -> PublicInvoice:
        """
        Read an invoice the way the hosted checkout page does — no API key needed.

        This is the same unauthenticated endpoint
        :attr:`~aiopaysell.types.Invoice.payment_url` points a buyer's
        browser at. Useful only if you're building your own checkout UI
        instead of redirecting to ``payment_url``; it's rate limited per
        IP, so poll it no more often than every few seconds.

        :param invoice: an invoice id, or an :class:`~aiopaysell.types.Invoice`
            / :class:`~aiopaysell.types.PublicInvoice` to re-read.
        :return: the current :class:`aiopaysell.types.PublicInvoice`.
        :raise aiopaysell.exceptions.NotFoundError: unknown id.
        """
        invoice_id = (
            invoice if isinstance(invoice, str) else invoice.invoice_id
        )
        return await self(self.GetPublicInvoiceMethod(invoice_id=invoice_id))
