from typing import TYPE_CHECKING, Annotated

from annotated_doc import Doc
from pydantic import Field

from aiopaysell.types import Invoice

from .base import PaysellMethod

if TYPE_CHECKING:
    from aiopaysell.client.client import Paysell


class ReadInvoice:
    """GET /invoices/{invoice_id}."""

    class GetInvoiceMethod(PaysellMethod[Invoice]):
        __return_type__ = Invoice
        __method_name__ = "getInvoice"
        __http_method__ = "GET"

        invoice_id: str = Field(exclude=True)

        def build_path(self) -> str:
            return f"/invoices/{self.invoice_id}"

    async def get_invoice(  # type: ignore[misc]
        self: "Paysell",
        invoice: Annotated[
            "str | Invoice",
            Doc("An id, or an `aiopaysell.types.Invoice` to refresh."),
        ],
    ) -> Invoice:
        """
        Read an invoice.

        Useful as a fallback when a webhook was missed, or on a thank-you
        page. Poll it at most every few seconds and treat webhooks as the
        primary channel.

        Returns:
            The current `aiopaysell.types.Invoice`.

        Raises:
            aiopaysell.exceptions.NotFoundError: unknown id, or another shop's.
        """
        invoice_id = invoice.invoice_id if isinstance(invoice, Invoice) else invoice
        return await self(self.GetInvoiceMethod(invoice_id=invoice_id))
