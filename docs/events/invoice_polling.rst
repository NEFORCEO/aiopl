===============
Invoice polling
===============

Polling is a fallback for the cases you can't run a webhook (local development,
a thank-you page). Once you call :meth:`invoice.poll() <aiopaysell.types.Invoice.poll>`,
the :class:`polling manager <aiopaysell.polling.PollingManager>` re-fetches that
invoice on an interval and calls
:attr:`invoice_paid <aiopaysell.Paysell.invoice_paid>`,
:attr:`invoice_expired <aiopaysell.Paysell.invoice_expired>` or
:attr:`invoice_cancelled <aiopaysell.Paysell.invoice_cancelled>` once its status
leaves ``pending``/``underpaid``.

.. autoproperty:: aiopaysell.Paysell.invoice_paid
.. autoproperty:: aiopaysell.Paysell.invoice_expired
.. autoproperty:: aiopaysell.Paysell.invoice_cancelled

.. attention::
    There is no "list invoices" endpoint, so unlike a batched poller this makes
    one request per tracked invoice, every round — fine for a handful of open
    orders, prefer webhooks at volume.

    :class:`Polling manager <aiopaysell.polling.PollingManager>` has a
    :class:`configuration <aiopaysell.polling.PollingConfig>` that defines the
    :attr:`delay <aiopaysell.polling.PollingConfig.delay>` between rounds and the
    :attr:`timeout <aiopaysell.polling.PollingConfig.timeout>` per invoice.

    **Default is 3 seconds delay and 1800 seconds (30 min) timeout.**

    :doc:`Change the polling configuration. <polling_config>`

Usage example
--------------
.. literalinclude:: ../../examples/polling.py
