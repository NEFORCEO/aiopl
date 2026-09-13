from decimal import Decimal

import pytest

from aiopaysell import (
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    Paysell,
    RateLimitError,
)
from aiopaysell.client.network import MAINNET


@pytest.fixture
def client() -> Paysell:
    return Paysell("sk_live_abc123")


def test_client_always_uses_mainnet() -> None:
    assert Paysell("sk_live_x").session.network is MAINNET
    assert MAINNET.base == "https://paysell.me/api/merchant/v1"


def test_create_invoice_method_shape(client: Paysell) -> None:
    method = client.CreateInvoiceMethod(
        asset="USDT_TON",
        amount="5",
        order_id="order-1",
    )
    assert method.__http_method__ == "POST"
    assert method.build_path() == "/invoices"
    assert method.model_dump_json(exclude_none=True) == (
        '{"asset":"USDT_TON","amount":"5","order_id":"order-1"}'
    )


def test_get_invoice_method_has_no_body_field_leak(client: Paysell) -> None:
    method = client.GetInvoiceMethod(invoice_id="abc-123")
    assert method.__http_method__ == "GET"
    assert method.build_path() == "/invoices/abc-123"
    assert method.model_dump_json(exclude_none=True) == "{}"


def test_cancel_invoice_method_path(client: Paysell) -> None:
    method = client.CancelInvoiceMethod(invoice_id="abc-123")
    assert method.build_path() == "/invoices/abc-123/cancel"


def test_get_public_invoice_method_needs_no_auth(client: Paysell) -> None:
    method = client.GetPublicInvoiceMethod(invoice_id="abc-123")
    assert method.build_path() == "/public/invoices/abc-123"
    assert method.__requires_auth__ is False


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (5, "5"),
        (1.5, "1.5"),
        (Decimal("1.5"), "1.5"),
        ("5", "5"),
        ("1.500", "1.500"),  # a str is passed through unchanged, not reformatted
    ],
)
async def test_create_invoice_sends_normal_units(
    client: Paysell,
    monkeypatch: pytest.MonkeyPatch,
    amount: object,
    expected: str,
) -> None:
    """`amount=5` must become the literal string "5", not smallest units."""
    captured = {}

    async def fake_request(token, session_client, method):  # noqa: ANN001, ARG001
        captured["amount"] = method.amount

    monkeypatch.setattr(client.session, "request", fake_request)

    await client.create_invoice("TON", amount, order_id="order-1")
    assert captured["amount"] == expected


async def test_create_invoice_rejects_too_many_decimals() -> None:
    from aiopaysell.tools import normalize_amount

    with pytest.raises(ValueError, match="more decimal places"):
        normalize_amount(Decimal("1.1234567891"), "TON")  # 10 decimals > 9


def test_success_response_parses_into_invoice(client: Paysell) -> None:
    method = client.CreateInvoiceMethod(asset="TON", amount="1.5")
    body = """{
        "invoice_id": "abc-123",
        "payment_url": "https://paysell.me/pay/abc-123",
        "address": "UQAvDJp7QDwqRcuNQBiK2GhBt71Xh1_UMYPCzMkQAoBPmZKl",
        "asset": "TON",
        "amount": "1.5",
        "amount_minor": "1500000000",
        "status": "pending",
        "paid": "0",
        "paid_minor": "0",
        "expires_at": "2026-09-06T17:20:55Z",
        "created_at": "2026-09-06T15:20:55Z"
    }"""
    invoice = client.session._check_response(client, method, 201, body, {})  # noqa: SLF001
    assert invoice.invoice_id == "abc-123"
    assert invoice.amount == "1.5"
    assert invoice.amount_minor_int == 1_500_000_000
    assert invoice.paid_minor_int == 0


@pytest.mark.parametrize(
    ("status", "exc"),
    [
        (401, AuthenticationError),
        (404, NotFoundError),
        (422, InvalidRequestError),
    ],
)
def test_object_shaped_error_maps_to_exception(
    client: Paysell,
    status: int,
    exc: type[Exception],
) -> None:
    method = client.GetInvoiceMethod(invoice_id="missing")
    body = '{"detail": {"code": "some_code", "message": "boom"}}'
    with pytest.raises(exc):
        client.session._check_response(client, method, status, body, {})  # noqa: SLF001


def test_list_shaped_validation_error_maps_to_invalid_request(client: Paysell) -> None:
    method = client.CreateInvoiceMethod(asset="TON", amount="5")
    body = (
        '{"detail": [{"type": "string_type", "loc": ["body", "amount"], '
        '"msg": "Input should be a valid string", "input": 5}]}'
    )
    with pytest.raises(InvalidRequestError) as exc_info:
        client.session._check_response(client, method, 422, body, {})  # noqa: SLF001
    assert exc_info.value.code == "validation_error"
    assert exc_info.value.errors is not None
    assert exc_info.value.errors[0]["msg"] == "Input should be a valid string"


def test_string_shaped_error_maps_to_exception(client: Paysell) -> None:
    """/public/invoices raises a bare FastAPI HTTPException, not the core's {code, message}."""
    method = client.GetPublicInvoiceMethod(invoice_id="missing")
    body = '{"detail": "Invoice not found"}'
    with pytest.raises(NotFoundError) as exc_info:
        client.session._check_response(client, method, 404, body, {})  # noqa: SLF001
    assert exc_info.value.code == "not_found"
    assert exc_info.value.message == "Invoice not found"


def test_rate_limit_error_carries_retry_after(client: Paysell) -> None:
    method = client.CreateInvoiceMethod(asset="TON", amount="5")
    body = '{"detail": {"code": "too_many_requests", "message": "slow down"}}'
    with pytest.raises(RateLimitError) as exc_info:
        client.session._check_response(  # noqa: SLF001
            client,
            method,
            429,
            body,
            {"Retry-After": "30"},
        )
    assert exc_info.value.retry_after == 30.0
