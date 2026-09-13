from decimal import Decimal

import pytest

from aiopaysell import to_smallest_units
from aiopaysell.tools import normalize_amount


@pytest.mark.parametrize(
    ("amount", "asset", "expected"),
    [
        (5, "TON", "5000000000"),
        (1.5, "TON", "1500000000"),
        (Decimal("1.5"), "TON", "1500000000"),
        (5, "USDT_TON", "5000000"),
        (5.000000, "USDT_TON", "5000000"),
        (0.1, "USDT_TON", "100000"),  # the classic float trap, done via Decimal(str(x))
    ],
)
def test_to_smallest_units_matches_docs_examples(
    amount: int | float | Decimal,
    asset: str,
    expected: str,
) -> None:
    assert to_smallest_units(amount, asset) == expected


def test_too_much_precision_raises() -> None:
    with pytest.raises(ValueError, match="more precision"):
        to_smallest_units(Decimal("1.1234567891"), "TON")  # 10 decimals > 9


def test_unknown_asset_raises() -> None:
    with pytest.raises(ValueError, match="Unknown asset"):
        to_smallest_units(5, "BTC")


@pytest.mark.parametrize(
    ("amount", "asset", "expected"),
    [
        (5, "TON", "5"),
        (1.5, "TON", "1.5"),
        (Decimal("1.5"), "USDT_TON", "1.5"),
        (100, "TON", "100"),
        ("5", "TON", "5"),  # str passes through unchanged, unvalidated
        ("not-a-number", "TON", "not-a-number"),
    ],
)
def test_normalize_amount(
    amount: int | float | Decimal | str,
    asset: str,
    expected: str,
) -> None:
    assert normalize_amount(amount, asset) == expected


def test_normalize_amount_rejects_too_many_decimals() -> None:
    with pytest.raises(ValueError, match="more decimal places"):
        normalize_amount(Decimal("1.1234567891"), "TON")  # 10 decimals > 9
    with pytest.raises(ValueError, match="more decimal places"):
        normalize_amount(Decimal("1.1234567"), "USDT_TON")  # 7 decimals > 6


def test_normalize_amount_unknown_asset_raises() -> None:
    with pytest.raises(ValueError, match="Unknown asset"):
        normalize_amount(5, "BTC")
