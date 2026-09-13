=======
Filters
=======

**Filters** route events to the right handler. Both the webhook and polling
routers check filters in registration order; the first handler whose filters
all pass wins, and the search stops there.

Filters can be:
-----------------
* an asynchronous function
* a synchronous function
* a lambda
* a class with a synchronous ``__call__``
* a class with an asynchronous ``__call__``
* a `MagicFilter <https://github.com/pypa/magic-filter>`_ instance

Magic filter
------------

.. code-block:: python

    from magic_filter import F

    @pay.payment_credited(F.status == "paid")
    async def on_paid(payment) -> None:
        print(f"order {payment.order_id} paid in full")


    @pay.payment_credited(F.status.in_({"overpaid", "underpaid"}))
    async def on_mismatch(payment) -> None:
        print(f"order {payment.order_id}: {payment.status}")

Function filter
----------------

You can use ``def``, ``async def`` or ``lambda``.

.. code-block:: python

    def is_ton(payment) -> bool:
        return payment.asset == "TON"

    async def is_large(payment) -> bool:
        return payment.credited_int > 100_000_000_000  # > 100 TON

    @pay.payment_credited(is_ton, is_large)
    async def on_large_ton_payment(payment) -> None: ...

Class filter
------------

.. code-block:: python

    class HasOrderId:
        def __call__(self, payment) -> bool:
            return payment.order_id is not None

    @pay.payment_credited(HasOrderId())
    async def on_paid(payment) -> None: ...

Get filter result as a handler argument
-----------------------------------------

Use `MagicFilter's <https://github.com/pypa/magic-filter>`_ ``as_`` to get the
filter result as a handler argument.

.. code-block:: python

    from magic_filter import F

    @pay.payment_credited(F.order_id.as_("order_id"))
    async def on_paid(payment, order_id: str) -> None:
        print(f"order {order_id} paid")

You can also return context data from any filter:

.. code-block:: python

    def with_order(payment) -> bool | dict[str, object]:
        if payment.order_id is None:
            return False
        return {"order_id": payment.order_id}

    @pay.payment_credited(with_order)
    async def on_paid(payment, order_id: str) -> None: ...
