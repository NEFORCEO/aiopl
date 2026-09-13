Routers
-------

A router is an object for routing events. There are two kinds:
:class:`PollingRouter <aiopaysell.polling.PollingRouter>` and
:class:`WebhookRouter <aiopaysell.webhook.WebhookRouter>`. :class:`Paysell <aiopaysell.Paysell>`
composes one of each internally — they're kept on separate routers on purpose, so a
``payment.credited`` webhook and an ``invoice_paid`` polling event never collide in the
same handler list. See :doc:`webhook` and :doc:`invoice_polling`.

One router can include another router; the parent must eventually be attached to the
client via :meth:`Paysell.include_router <aiopaysell.Paysell.include_router>` or
:meth:`include_routers <aiopaysell.Paysell.include_routers>`.

Usage example

.. literalinclude:: ../../examples/router.py

.. automethod:: aiopaysell.Paysell.include_router
.. automethod:: aiopaysell.Paysell.include_routers

.. autoclass:: aiopaysell._events.BaseRouter
    :members:

.. autoclass:: aiopaysell.webhook.WebhookRouter
    :show-inheritance:

.. autoclass:: aiopaysell.polling.PollingRouter
    :show-inheritance:

Event observers
----------------
An event observer stores handlers for one event. Attach a handler with a
:code:`@router.<event>(...)` decorator or a :code:`router.<event>.register(...)` call.

.. autoclass:: aiopaysell._events.EventObserver
    :members:

Webhook router
===============

Available observers for :class:`WebhookRouter <aiopaysell.webhook.WebhookRouter>`.

Payment credited
~~~~~~~~~~~~~~~~~

.. code-block:: python

    @router.payment_credited()
    async def on_credited(payment: PaymentCredited) -> None: ...

Payment rejected
~~~~~~~~~~~~~~~~~

.. code-block:: python

    @router.payment_rejected()
    async def on_rejected(payment: PaymentRejected) -> None: ...

Polling router
===============

Available observers for :class:`PollingRouter <aiopaysell.polling.PollingRouter>`.

Paid invoice
~~~~~~~~~~~~~

.. code-block:: python

    @router.invoice_paid()
    async def on_paid(invoice: Invoice) -> None: ...

Expired invoice
~~~~~~~~~~~~~~~~

.. code-block:: python

    @router.invoice_expired()
    async def on_expired(invoice: Invoice) -> None: ...

Cancelled invoice
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @router.invoice_cancelled()
    async def on_cancelled(invoice: Invoice) -> None: ...
