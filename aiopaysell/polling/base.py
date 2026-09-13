import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from aiopaysell import loggers

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiopaysell.types import Invoice


@dataclass(slots=True)
class PollingConfig:
    """Polling configuration."""

    timeout: int = 1800
    """How long to keep polling one invoice, in seconds.

    30 minutes covers the default ``ttl_minutes``; raise it if you set a
    longer invoice lifetime and want polling to track it to expiry.
    """
    delay: int = 3
    """Seconds to wait between polling rounds."""


@dataclass(slots=True)
class PollingTask:
    """A tracked invoice and how much longer to keep checking it."""

    obj: "Invoice"
    """The invoice as it was when handed to :meth:`~aiopaysell.types.Invoice.poll`."""
    timeout: int
    """Remaining time before this task gives up, in seconds."""
    data: dict[str, object] = field(default_factory=dict)
    """Extra payload passed through to the event handler."""


class BasePollingManager:
    """Polling loop shared by :class:`aiopaysell.polling.PollingManager`."""

    _timeout: int
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
                except Exception:
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
