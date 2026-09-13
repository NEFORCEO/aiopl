.. raw:: html

   <h1 class="main-title">aiopaysell</h1>

Introduction
------------

**aiopaysell** is an async Python client for the `Paysell <https://paysell.me/docs>`_
payment API — accept TON and USDT (on TON) with invoices, webhooks, and a polling fallback.

Features
--------
* fully typed, pydantic-based models
* one method per endpoint: :doc:`create, read, cancel, and publicly read invoices <api/methods>`
* :doc:`webhook handling <events/webhook>` for aiohttp and FastAPI, covering both
  ``payment.credited`` and ``payment.rejected``
* :doc:`invoice polling <events/invoice_polling>` as a fallback when webhooks aren't reachable
* powerful `magic filters <https://github.com/pypa/magic-filter>`_ for routing events, see :doc:`events/filters`
* pass a number, get the exchange-ready string — ``5`` becomes ``"5"``, decimal
  places validated against the coin, see :doc:`client/tools`

Quick start
-----------

.. literalinclude:: ../examples/quick_start.py

Contents
--------
.. toctree::
   :maxdepth: 1

   install
   api/index
   client/index
   events/index
