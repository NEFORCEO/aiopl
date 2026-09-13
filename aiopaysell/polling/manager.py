import asyncio
import warnings
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from aiopaysell import loggers
from aiopaysell.enums import InvoiceStatus

from .base import BasePollingManager, PollingConfig, PollingTask
from .router import PollingRouter

if TYPE_CHECKING:
    from collections.abc import Callable

    from aiopaysell._events import EventObserver
    from aiopaysell.types import Invoice

_TERMINAL_PAID = (InvoiceStatus.PAID, InvoiceStatus.OVERPAID)
_STOP_STATUSES = (*_TERMINAL_PAID, InvoiceStatus.EXPIRED, InvoiceStatus.CANCELLED)

UNDERPAID_GRACE = timedelta(hours=24)
"""How much longer an ``underpaid`` invoice keeps its address, per the docs."""


class PollingManager(BasePollingManager):
    """
    Fallback for missed webhooks: re-fetches tracked invoices on an interval.

    Composes its own :class:`PollingRouter` rather than inheriting one, so
    its events stay independent of the webhook router's ``payment_credited``
    — see :class:`aiopaysell.webhook.WebhookHandler`.
    """

    _kwargs: dict[str, object]

    def __init__(self, config: PollingConfig) -> None:
        self._polling_router = PollingRouter()
        self._invoice_tasks: dict[str, PollingTask] = {}
        self._fixed_timeout = config.timeout
        self._delay = config.delay

    @property
    def invoice_paid(self) -> "EventObserver":
        """Fires when a tracked invoice reaches ``paid`` or ``overpaid``."""
        return self._polling_router.invoice_paid

    @property
    def invoice_expired(self) -> "EventObserver":
        """Fires when a tracked invoice's status actually becomes ``expired``."""
        return self._polling_router.invoice_expired

    @property
    def invoice_cancelled(self) -> "EventObserver":
        """Fires when a tracked invoice is cancelled."""
        return self._polling_router.invoice_cancelled

    def _poll_invoice(self, invoice: "Invoice", **kwargs: object) -> None:
        if self._fixed_timeout is None:
            deadline = invoice.expires_at
        else:
            deadline = datetime.now(UTC) + timedelta(seconds=self._fixed_timeout)
        self._invoice_tasks[invoice.invoice_id] = PollingTask(invoice, deadline, kwargs)

    async def _handle_invoice(self, invoice: "Invoice") -> None:
        task = self._invoice_tasks.get(invoice.invoice_id)
        if task is None:
            return
        status = invoice.status

        if status == InvoiceStatus.UNDERPAID:
            # The API keeps an underpaid invoice's address for 24h past
            # expires_at — extend the deadline to match, once.
            task.deadline = max(task.deadline, invoice.expires_at + UNDERPAID_GRACE)

        timed_out = datetime.now(UTC) >= task.deadline

        if status in _STOP_STATUSES or timed_out:
            del self._invoice_tasks[invoice.invoice_id]

        if status in _TERMINAL_PAID:
            event = "invoice_paid"
        elif status == InvoiceStatus.CANCELLED:
            event = "invoice_cancelled"
        elif status == InvoiceStatus.EXPIRED:
            event = "invoice_expired"
        elif timed_out:
            # We gave up watching, but the invoice itself isn't actually
            # expired server-side (still pending/underpaid) — say so rather
            # than firing invoice_expired for a status that isn't expired.
            loggers.polling.warning(
                "Gave up polling invoice_id=%s: still %s after the deadline. "
                "Check aiopaysell.Paysell.get_invoice() directly, or raise "
                "PollingConfig.timeout.",
                invoice.invoice_id,
                status,
            )
            return
        else:
            return  # still pending/underpaid, not timed out — keep watching

        if await self._polling_router.propagate_event(
            invoice,
            event,
            **task.data | self._kwargs,
        ):
            loggers.polling.info(
                "%s invoice_id=%s is handled.",
                event.upper(),
                invoice.invoice_id,
            )
        else:
            loggers.polling.info(
                "%s invoice_id=%s has no matching handler.",
                event.upper(),
                invoice.invoice_id,
            )

    async def _start_invoice_polling(self) -> None:
        await self._start_polling(
            self.get_invoice,  # type: ignore[attr-defined]
            self._handle_invoice,
            self._invoice_tasks,
        )

    async def start_polling(
        self,
        parallel: "Callable[[], object] | None" = None,
    ) -> None:
        """
        Poll tracked invoices until cancelled.

        :param parallel: an optional sync function to run alongside, in an executor.
        :return:
        """
        if getattr(self, "_webhook_manager", None) is not None:
            red, reset = "\033[91m", "\033[0m"
            warnings.warn(
                f"{red}A webhook manager is set. Polling on top of webhooks "
                f"can deliver the same invoice twice; make handlers "
                f"idempotent.{reset}",
                stacklevel=2,
            )
        if parallel is not None:
            asyncio.get_event_loop().run_in_executor(None, parallel)
        loggers.polling.info("Start polling")
        await self._start_invoice_polling()
