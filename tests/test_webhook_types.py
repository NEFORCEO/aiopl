from aiopaysell.types import PaymentCredited, PaymentRejected


def test_payment_credited_int_properties() -> None:
    payment = PaymentCredited(
        invoice_id="abc-123",
        order_id="order-1",
        asset="TON",
        amount="1500000000",
        credited="1471500000",
        fee="28500000",
        status="paid",
        paid_minor="1500000000",
        tx_hash="97a1f0",
    )
    assert payment.amount_int == 1_500_000_000
    assert payment.credited_int == 1_471_500_000
    assert payment.fee_int == 28_500_000
    assert payment.paid_minor_int == 1_500_000_000
    assert payment.asset_mismatch is False
    assert payment.invoice_asset is None


def test_payment_credited_fields_are_nullable() -> None:
    """The OpenAPI schema marks every money field nullable; None must not blow up .*_int."""
    payment = PaymentCredited()
    assert payment.amount_int is None
    assert payment.credited_int is None
    assert payment.fee_int is None
    assert payment.paid_minor_int is None


def test_payment_credited_asset_mismatch() -> None:
    payment = PaymentCredited(
        asset="TON",
        invoice_asset="USDT_TON",
        asset_mismatch=True,
        status="pending",
    )
    assert payment.asset_mismatch is True
    assert payment.invoice_asset == "USDT_TON"


def test_payment_rejected() -> None:
    payment = PaymentRejected(
        invoice_id="abc-123",
        order_id="order-1",
        asset="TON",
        amount="100000000",
        tx_hash="97a1f0",
        reason="could not be matched to any order",
    )
    assert payment.amount_int == 100_000_000
    assert payment.reason == "could not be matched to any order"
