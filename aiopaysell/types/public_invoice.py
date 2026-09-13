from datetime import datetime

from aiopaysell.enums import Asset, InvoiceStatus

from .base import PaysellObject


class PublicInvoice(PaysellObject):
    """
    What the buyer's payment page is allowed to see.

    Returned by :meth:`aiopaysell.Paysell.get_public_invoice` — the same
    unauthenticated read the hosted checkout page itself uses. Deliberately
    narrower than :class:`~aiopaysell.types.Invoice`: no ``order_id``, no
    ``created_at``, no API key required to read it.
    """

    invoice_id: str
    """The invoice being paid."""
    address: str
    """The receiving address, non-bounceable. Show it exactly as returned."""
    asset: Asset | str
    """The coin to send. Anything else sent to this address is lost."""
    amount: str
    """The amount asked for, in normal units."""
    amount_minor: str
    """The same amount in smallest units — what a ``ton://transfer`` link's ``amount`` takes."""  # noqa: E501
    status: InvoiceStatus | str
    """``pending``, ``underpaid``, ``paid``, ``overpaid``, ``expired`` or ``cancelled``."""  # noqa: E501
    paid: str | None = None
    """How much has arrived so far, in normal units."""
    paid_minor: str | None = None
    """How much has arrived so far, smallest unit. Subtract from
    :attr:`amount_minor` for what's still owed."""
    description: str | None = None
    """What the buyer is paying for."""
    expires_at: datetime
    """When the invoice stops being payable. Add 24h when :attr:`status` is ``underpaid``."""  # noqa: E501
    shop_name: str | None = None
    """The merchant's shop name."""
    shop_url: str | None = None
    """The merchant's storefront, for a "back to the shop" link."""

    @property
    def amount_minor_int(self) -> int:
        """:attr:`amount_minor` as an :class:`int`."""
        return int(self.amount_minor)

    @property
    def paid_minor_int(self) -> int:
        """:attr:`paid_minor` as an :class:`int`, or ``0`` if nothing arrived yet."""
        return int(self.paid_minor) if self.paid_minor is not None else 0
