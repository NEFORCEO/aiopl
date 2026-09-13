=====
Tools
=====

Standalone helpers that don't map to an API endpoint.

.. autofunction:: aiopaysell.tools.normalize_amount

Usage example

.. code-block:: python

    from aiopaysell import normalize_amount

    normalize_amount(5, "TON")            # "5"
    normalize_amount(1.5, "USDT_TON")     # "1.5"

.. autofunction:: aiopaysell.tools.to_smallest_units

Requests no longer need this — :meth:`~aiopaysell.Paysell.create_invoice`
takes normal units directly, and every response already carries
``amount_minor``/``paid_minor``. It's still useful for something the
response doesn't give you, e.g. building a ``ton://transfer`` link from an
amount a user just typed.

Usage example

.. code-block:: python

    from aiopaysell import to_smallest_units

    to_smallest_units(5, "TON")          # "5000000000"
    to_smallest_units(1.5, "USDT_TON")   # "1500000"

.. autofunction:: aiopaysell.tools.verify_signature
.. autodata:: aiopaysell.tools.verify_signature.DEFAULT_TIMESTAMP_TOLERANCE

Usage example

.. code-block:: python

    from aiopaysell import verify_signature

    verify_signature(
        raw_body,
        headers["X-Paysell-Signature"],
        headers["X-Paysell-Timestamp"],
        webhook_secret,
    )
