Polling configuration
----------------------
You can configure your own polling delay and timeout.

.. autoclass:: aiopaysell.polling.PollingConfig
    :members:

.. code-block:: python

    from aiopaysell import Paysell, PollingConfig

    pay = Paysell("sk_live_YOUR_KEY", polling_config=PollingConfig(delay=5, timeout=900))

.. autoclass:: aiopaysell.polling.PollingManager
    :members:

.. automethod:: aiopaysell.Paysell.start_polling
