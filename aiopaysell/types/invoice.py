from datetime import datetime

from aiopaysell.enums import Asset, InvoiceStatus

from .base import PaysellObject


class Invoice(PaysellObject):
    """
    Invoice object.

    Returned by :meth:`aiopaysell.Paysell.create_invoice`,
    :meth:`aiopaysell.Paysell.get_invoice` and
    :meth:`aiopaysell.Paysell.cancel_invoice`.
    """

    invoice_id: str
    """Unique ID for this invoice."""
    payment_url: str | None = None
    """Redirect the buyer here. Nothing else to build. ``None`` only on a
    deployment with no checkout page configured."""
    address: str
    """
    The receiving address, in non-bounceable form (``UQ…`` on mainnet,
    ``0Q…`` on testnet). Display it *exactly* as returned if you render your
    own checkout — re-encoding it can send a payment to a not-yet-deployed
    wallet, which bounces back to the sender.
    """
    asset: Asset | str
    """``TON`` or ``USDT_TON``."""
    amount: str
    """The amount asked for, in normal units, exactly as sent. Display this."""
    amount_minor: str
    """The same amount as an integer in the smallest unit, as a string. Compute with this."""  # noqa: E501
    status: InvoiceStatus | str
    """Current status. Real changes arrive by webhook; this is the value as of the read."""  # noqa: E501
    paid: str | None = None
    """How much has arrived on this invoice so far, in normal units."""
    paid_minor: str | None = None
    """The same, as an integer in the smallest unit. The field that matters
    on ``underpaid``: :attr:`status` says less arrived, this says how much less."""
    order_id: str | None = None
    """*Optional*. Your own reference, echoed back in the webhook."""
    description: str | None = None
    """*Optional*. Shown to the buyer on the payment page."""
    expires_at: datetime
    """After this passes, the address stops being watched for this invoice
    (plus a 24h grace period while ``underpaid``)."""
    created_at: datetime
    """Date the invoice was created."""

    @property
    def amount_minor_int(self) -> int:
        """:attr:`amount_minor` as an :class:`int`, in the asset's smallest unit."""
        return int(self.amount_minor)

    @property
    def paid_minor_int(self) -> int:
        """:attr:`paid_minor` as an :class:`int`, or ``0`` if nothing arrived yet."""
        return int(self.paid_minor) if self.paid_minor is not None else 0

    async def refresh(self) -> None:
        """
        Shortcut for :meth:`aiopaysell.Paysell.get_invoice`.

        Updates this object in place with the invoice's current state.

        :return:
        """
        fresh = await self._client.get_invoice(self.invoice_id)
        for name in type(self).model_fields:
            setattr(self, name, getattr(fresh, name))

    async def cancel(self) -> "Invoice":
        """
        Shortcut for :meth:`aiopaysell.Paysell.cancel_invoice`.

        Use this to close an unpaid invoice early and release its address.

        :return: the cancelled :class:`Invoice`.
        """
        return await self._client.cancel_invoice(self.invoice_id)

    def poll(self, **kwargs: object) -> None:
        """
        Hand this invoice to the polling manager.

        Use this as a fallback when you can't receive webhooks (e.g. local
        development), or to drive a UI countdown independently of them.

        :param kwargs: extra data forwarded to the matching event handler.
        :return:
        """
        self._client._poll_invoice(self, **kwargs)
