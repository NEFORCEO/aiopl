from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aiopaysell.enums import Asset, InvoiceStatus


class PaymentCredited(BaseModel):
    """
    The ``data`` payload of a ``payment.credited`` webhook.

    All money here is an integer in the coin's smallest unit, as a string —
    the opposite of the REST API, which takes and returns normal units.
    """

    model_config = ConfigDict(extra="allow", frozen=True)

    invoice_id: str | None = None
    """The invoice this payment landed on."""
    order_id: str | None = None
    """Your own reference, exactly as you sent it. ``None`` if you sent none."""
    asset: Asset | str | None = None
    """The coin that actually arrived — not necessarily the coin of the invoice."""
    amount: str | None = None
    """What arrived in this transfer, in smallest units."""
    credited: str | None = None
    """What landed on your balance — ``amount`` minus ``fee``, in smallest units."""
    fee: str | None = None
    """What Paysell took, in smallest units."""
    status: InvoiceStatus | str | None = None
    """The invoice's status now. Release the goods only on ``paid`` or ``overpaid``."""
    paid_minor: str | None = None
    """Total received on this invoice so far, in smallest units. The field
    that matters on ``underpaid``: :attr:`status` says less arrived, this
    says how much less."""
    tx_hash: str | None = None
    """The on-chain transaction, for your records and support."""
    asset_mismatch: bool = False
    """``True`` only when the coin that arrived isn't the coin of the
    invoice. One deposit address serves both TON and USDT, so a USDT
    invoice can be paid in TON: the money is credited to you, but the
    invoice stays unpaid — see :attr:`invoice_asset`."""
    invoice_asset: Asset | str | None = None
    """Present with :attr:`asset_mismatch`: the coin the invoice actually asks for."""

    @property
    def amount_int(self) -> int | None:
        """:attr:`amount` as an :class:`int`, or ``None`` if absent."""
        return int(self.amount) if self.amount is not None else None

    @property
    def credited_int(self) -> int | None:
        """:attr:`credited` as an :class:`int`, or ``None`` if absent."""
        return int(self.credited) if self.credited is not None else None

    @property
    def fee_int(self) -> int | None:
        """:attr:`fee` as an :class:`int`, or ``None`` if absent."""
        return int(self.fee) if self.fee is not None else None

    @property
    def paid_minor_int(self) -> int | None:
        """:attr:`paid_minor` as an :class:`int`, or ``None`` if absent."""
        return int(self.paid_minor) if self.paid_minor is not None else None


class PaymentRejected(BaseModel):
    """
    The ``data`` payload of a ``payment.rejected`` webhook.

    Fewer fields than a credited payment, and not out of thrift: a rejected
    deposit has no ``credited`` and no ``fee``, and the invoice's status
    does not change — it stays unpaid. Do not release the goods; if the
    invoice was already ``paid`` by an earlier transfer, this event is
    about the extra deposit, not about that payment.
    """

    model_config = ConfigDict(extra="allow", frozen=True)

    invoice_id: str | None = None
    order_id: str | None = None
    """Your own reference, looked up from the invoice."""
    asset: Asset | str | None = None
    amount: str | None = None
    """What arrived on chain, in smallest units."""
    tx_hash: str | None = None
    reason: str | None = None
    """Why the operator declined to credit it. You'll have to explain this to the buyer."""  # noqa: E501

    @property
    def amount_int(self) -> int | None:
        """:attr:`amount` as an :class:`int`, or ``None`` if absent."""
        return int(self.amount) if self.amount is not None else None


class WebhookEvent(BaseModel):
    """
    The full webhook request body, before its ``data`` is parsed against
    the shape matching its ``type``.
    """

    model_config = ConfigDict(extra="allow", frozen=True)

    event_id: UUID
    """Unique per delivery, repeated in the ``X-Paysell-Event-Id`` header.
    The same event can arrive more than once; dedupe on this."""
    type: str
    """``payment.credited`` or ``payment.rejected``."""
    data: dict[str, object]
    """Parsed into :class:`PaymentCredited` or :class:`PaymentRejected` by
    :meth:`aiopaysell.webhook.WebhookHandler.feed_update`, based on :attr:`type`."""
