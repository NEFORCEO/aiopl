from typing import TYPE_CHECKING

from pydantic import Field

from aiopaysell.types import Invoice

from .base import PaysellMethod

if TYPE_CHECKING:
    from aiopaysell.client.client import Paysell


class CancelInvoice:
    """POST /invoices/{invoice_id}/cancel."""

    class CancelInvoiceMethod(PaysellMethod[Invoice]):
        __return_type__ = Invoice
        __method_name__ = "cancelInvoice"
        __http_method__ = "POST"

        invoice_id: str = Field(exclude=True)

        def build_path(self) -> str:
            return f"/invoices/{self.invoice_id}/cancel"

    async def cancel_invoice(  # type: ignore[misc]
        self: "Paysell",
        invoice: "str | Invoice",
    ) -> Invoice:
        """
        Cancel an unpaid invoice early and release its address.

        Use this when the customer abandons checkout — addresses are a
        finite resource, and returning them keeps the pool healthy.

        :param invoice: an invoice id, or an :class:`aiopaysell.types.Invoice`.
        :return: the cancelled :class:`aiopaysell.types.Invoice`.
        :raise aiopaysell.exceptions.ConflictError: the invoice is already paid.
        :raise aiopaysell.exceptions.NotFoundError: unknown id, or another shop's.
        """
        invoice_id = invoice.invoice_id if isinstance(invoice, Invoice) else invoice
        return await self(self.CancelInvoiceMethod(invoice_id=invoice_id))
