from aiopaysell._events import BaseRouter, EventObserver


class WebhookRouter(BaseRouter):
    """
    Router for webhook events.

    ``payment_credited`` fires with a :class:`aiopaysell.types.PaymentCredited`
    whose ``status`` is ``paid``, ``overpaid`` or ``underpaid`` — filter on
    it if you only care about full payments::

        from magic_filter import F

        @router.payment_credited(F.status == "paid")
        async def on_paid(payment): ...

    ``payment_rejected`` fires with a :class:`aiopaysell.types.PaymentRejected`
    when a deposit held for an additional check was declined — release
    nothing on it.
    """

    def __init__(self, *, name: str | None = None) -> None:
        super().__init__(name=name)

        self.payment_credited = EventObserver()
        self.payment_rejected = EventObserver()

        self.observers = {
            "payment.credited": self.payment_credited,
            "payment.rejected": self.payment_rejected,
        }
