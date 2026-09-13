=======
Webhook
=======

Every delivery is signed as ``HMAC-SHA256(secret, "{timestamp}.{raw_body}")``,
hex-encoded and prefixed ``sha256=``. **aiopaysell** verifies this for you —
including rejecting anything whose ``X-Paysell-Timestamp`` is more than
:data:`~aiopaysell.tools.verify_signature.DEFAULT_TIMESTAMP_TOLERANCE`
(300s) from your own clock, a replay-protection window that's part of the
signed string and can't be edited without breaking the signature.

.. autodata:: aiopaysell.webhook.DEFAULT_SIGNATURE_HEADER
.. autodata:: aiopaysell.webhook.DEFAULT_TIMESTAMP_HEADER

Pass ``signature_header=``, ``timestamp_header=`` or ``timestamp_tolerance=``
to :class:`aiopaysell.Paysell` if a deployment ever names these differently
or you want a tighter/looser clock-skew window.

Two events arrive at the same endpoint:

.. list-table::
   :header-rows: 1

   * - Event
     - Fires as
     - When
   * - ``payment.credited``
     - :attr:`~aiopaysell.Paysell.payment_credited`
     - a transfer is confirmed and credited — ``data`` is a :class:`~aiopaysell.types.PaymentCredited`
   * - ``payment.rejected``
     - :attr:`~aiopaysell.Paysell.payment_rejected`
     - a held deposit is declined — ``data`` is a :class:`~aiopaysell.types.PaymentRejected`

.. autoproperty:: aiopaysell.Paysell.payment_credited
.. autoproperty:: aiopaysell.Paysell.payment_rejected

Release the goods only when :attr:`PaymentCredited.status <aiopaysell.types.PaymentCredited.status>`
is ``paid`` or ``overpaid`` — never on the call merely arriving, and never on ``payment.rejected``.

Usage example with `aiohttp web server <https://docs.aiohttp.org/en/stable/web_quickstart.html>`_
-----------------------------------------------------------------------------------------------------
.. literalinclude:: ../../examples/webhook_aiohttp.py

Usage example with `FastAPI web server <https://fastapi.tiangolo.com/tutorial/first-steps/>`_
---------------------------------------------------------------------------------------------
.. tip::
    In order to use aiopaysell with FastAPI you need to install the extra:

.. code-block:: bash

    pip install aiopaysell[fastapi]

.. literalinclude:: ../../examples/webhook_fastapi.py

.. attention::
    The provider retries an undelivered webhook seven times over roughly
    31 hours; the same ``event_id`` can arrive more than once even after a
    2xx. **aiopaysell** verifies and routes each delivery but does not
    deduplicate for you — record ``event_id`` yourself and make a repeat
    arrival a no-op.

**aiopaysell** uses `aiohttp <https://docs.aiohttp.org/en/stable/index.html>`_ as its web
server by default. Implement your own webhook manager by inheriting
:class:`aiopaysell.webhook.WebhookManager` and overriding
:attr:`aiopaysell.webhook.WebhookManager.register_handler`.

.. autoclass:: aiopaysell.webhook.WebhookManager
    :members:

.. autoclass:: aiopaysell.webhook.WebhookHandler
    :members:
    :exclude-members: payment_credited, payment_rejected

.. autoclass:: aiopaysell.webhook.AiohttpManager
    :show-inheritance:
    :members:

.. autoclass:: aiopaysell.webhook.FastAPIManager
    :show-inheritance:
    :members:
