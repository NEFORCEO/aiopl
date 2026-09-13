from aiopaysell._events import BaseRouter, EventObserver


class PollingRouter(BaseRouter):
    """Router for polling events, fired while re-fetching invoices handed to ``.poll()``."""  # noqa: E501

    def __init__(self, *, name: str | None = None) -> None:
        super().__init__(name=name)

        self.invoice_paid = EventObserver()
        self.invoice_expired = EventObserver()
        self.invoice_cancelled = EventObserver()

        self.observers = {
            "invoice_paid": self.invoice_paid,
            "invoice_expired": self.invoice_expired,
            "invoice_cancelled": self.invoice_cancelled,
        }
