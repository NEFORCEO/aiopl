import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from aiopaysell import loggers
from aiopaysell.exceptions import NotFoundError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiopaysell.types import Invoice


@dataclass(slots=True)
class PollingConfig:
    """Polling configuration."""

    timeout: int | None = None
    """Max seconds to keep polling one invoice.

    ``None`` (default) tracks the invoice's own ``expires_at`` instead of a
    fixed guess — extended once by 24h if it goes ``underpaid``, matching
    the grace period the API itself gives it. Set a number to override this
    with a fixed timeout for every invoice instead.
    """
    delay: int = 3
    """Seconds to wait between polling rounds."""


@dataclass(slots=True)
class PollingTask:
    """A tracked invoice and when to give up on it."""

    obj: "Invoice"
    """The invoice as it was when handed to :meth:`~aiopaysell.types.Invoice.poll`."""
    deadline: datetime
    """Timezone-aware point in time after which this task gives up."""
    data: dict[str, object] = field(default_factory=dict)
    """Extra payload passed through to the event handler."""


class BasePollingManager:
    """Polling loop shared by :class:`aiopaysell.polling.PollingManager`."""

    _delay: int

    async def _start_polling(
        self,
        get_one: "Callable[[str], Awaitable[Invoice]]",
        handle_update: "Callable[[Invoice], Awaitable[None]]",
        tasks: dict[str, PollingTask],
    ) -> None:
        """
        Run the polling loop.

        There is no "list invoices" endpoint, so unlike a batched poller
        this re-fetches every tracked invoice individually each round —
        fine for a handful of open orders, but prefer webhooks at volume.
        """
        while True:
            await asyncio.sleep(self._delay)
            if not tasks:
                continue
            for invoice_id in list(tasks):
                try:
                    invoice = await get_one(invoice_id)
                except NotFoundError:
                    # Permanent: this id will never succeed. Stop immediately
                    # instead of retrying it every round until the deadline.
                    loggers.polling.warning(
                        "Stopped polling invoice_id=%s: it no longer exists (404).",
                        invoice_id,
                    )
                    del tasks[invoice_id]
                    continue
                except Exception:  # transient, keep retrying until the deadline
                    loggers.polling.exception(
                        "Error while polling invoice_id=%s:\n",
                        invoice_id,
                    )
                    continue
                try:
                    await handle_update(invoice)
                except Exception:
                    loggers.polling.exception(
                        "Error while handling invoice_id=%s:\n",
                        invoice_id,
                    )
            loggers.polling.debug(
                "Tasks left: %d. Waiting %ds...",
                len(tasks),
                self._delay,
            )
