from enum import Enum
from typing import Literal


class InvoiceStatus(str, Enum):
    """
    Invoice status.

    Source: the "Status reference" section of the docs.
    """

    PENDING = "pending"
    """Waiting for payment. Keep the order open."""
    PAID = "paid"
    """Paid in full. Release the goods."""
    OVERPAID = "overpaid"
    """More arrived than asked. The surplus is credited in full."""
    UNDERPAID = "underpaid"
    """Less arrived. Stays open for a top-up to the same address."""
    EXPIRED = "expired"
    """The window closed unpaid. Offer a new invoice."""
    CANCELLED = "cancelled"
    """Cancelled by you."""


LiteralInvoiceStatus = Literal[
    "pending",
    "paid",
    "overpaid",
    "underpaid",
    "expired",
    "cancelled",
]
