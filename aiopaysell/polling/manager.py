import asyncio
import warnings
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
_STOP = (*_TERMINAL_PAID, InvoiceStatus.EXPIRED, InvoiceStatus.CANCELLED)


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
        self._timeout = config.timeout
        self._delay = config.delay

    @property
    def invoice_paid(self) -> "EventObserver":
        """Fires when a tracked invoice reaches ``paid`` or ``overpaid``."""
        return self._polling_router.invoice_paid

    @property
    def invoice_expired(self) -> "EventObserver":
        """Fires when a tracked invoice's payment window closes unpaid."""
        return self._polling_router.invoice_expired

    @property
    def invoice_cancelled(self) -> "EventObserver":
        """Fires when a tracked invoice is cancelled."""
        return self._polling_router.invoice_cancelled

    def _poll_invoice(self, invoice: "Invoice", **kwargs: object) -> None:
        self._invoice_tasks[invoice.invoice_id] = PollingTask(
            invoice,
            self._timeout,
            kwargs,
        )

    async def _handle_invoice(self, invoice: "Invoice") -> None:
        task = self._invoice_tasks.get(invoice.invoice_id)
        if task is None:
            return
        task.timeout -= self._delay
        status = invoice.status
        expired_by_timeout = task.timeout <= 0

        if status in _STOP or expired_by_timeout:
            del self._invoice_tasks[invoice.invoice_id]

        if status in _TERMINAL_PAID:
            event = "invoice_paid"
        elif status == InvoiceStatus.CANCELLED:
            event = "invoice_cancelled"
        elif status == InvoiceStatus.EXPIRED or expired_by_timeout:
            event = "invoice_expired"
        else:
            return  # still pending/underpaid — keep watching

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
