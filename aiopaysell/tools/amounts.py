from decimal import Decimal
from typing import TYPE_CHECKING

from aiopaysell.enums import ASSET_DECIMALS, Asset

if TYPE_CHECKING:
    from aiopaysell.enums import LiteralAsset


def _to_decimal(amount: "int | float | Decimal | str") -> Decimal:
    # str(x) round-trips a float exactly; Decimal(x) on a float would
    # inherit its binary rounding error instead.
    return Decimal(str(amount)) if isinstance(amount, float) else Decimal(amount)


def _decimals_for(asset: "Asset | LiteralAsset | str") -> tuple[str, int]:
    key = asset.value if isinstance(asset, Asset) else str(asset)
    try:
        return key, ASSET_DECIMALS[key]
    except KeyError:
        msg = f"Unknown asset {key!r}; can't infer its decimals."
        raise ValueError(msg) from None


def normalize_amount(
    amount: "int | float | Decimal | str",
    asset: "Asset | LiteralAsset | str",
) -> str:
    """
    Format a human-readable amount as the plain decimal string the API expects.

    :meth:`aiopaysell.Paysell.create_invoice` calls this for you whenever
    ``amount`` isn't already a :class:`str` — ``5`` becomes ``"5"``,
    ``Decimal("1.5")`` becomes ``"1.5"``. A string is returned unchanged,
    so it never mangles a value you've already formatted correctly.

    :param amount: amount in the coin's normal units, e.g. ``5`` or ``Decimal("1.5")``.
    :param asset: ``"TON"`` or ``"USDT_TON"``.
    :return: ``amount`` as a plain decimal string (``^[0-9]+(\\.[0-9]+)?$``).
    :raise ValueError: unknown asset, or ``amount`` has more decimal places
        than the asset supports.
    """
    if isinstance(amount, str):
        return amount
    key, decimals = _decimals_for(asset)
    dec = _to_decimal(amount)
    exponent = dec.as_tuple().exponent
    if isinstance(exponent, int) and -exponent > decimals:
        msg = f"{amount} has more decimal places than {key} supports ({decimals})."
        raise ValueError(msg)
    return format(dec, "f")


def to_smallest_units(
    amount: "int | float | Decimal | str",
    asset: "Asset | LiteralAsset | str",
) -> str:
    """
    Convert a human-readable amount (e.g. ``5`` TON) to the smallest-unit
    string the API returns as ``amount_minor`` (e.g. ``"5000000000"``).

    Requests no longer need this — :meth:`aiopaysell.Paysell.create_invoice`
    takes normal units directly (see :func:`normalize_amount`), and every
    response already carries ``amount_minor``/``paid_minor``. Reach for this
    when you need the smallest-unit value for something the response
    doesn't give you, e.g. building your own ``ton://transfer`` link from
    an amount a user typed.

    :param amount: amount in whole coins, e.g. ``5`` or ``Decimal("1.5")``.
        A :class:`float` is converted via its exact decimal string form
        (``Decimal(str(amount))``, not ``Decimal(amount)``) so it doesn't
        inherit the float's binary rounding error.
    :param asset: ``"TON"`` or ``"USDT_TON"``.
    :return: the amount in the asset's smallest unit, as a string.
    :raise ValueError: unknown asset, or ``amount`` has more precision than
        the asset supports.
    """
    key, decimals = _decimals_for(asset)
    dec = _to_decimal(amount)
    scaled = dec.scaleb(decimals)
    if scaled != scaled.to_integral_value():
        msg = f"{amount} has more precision than {key} supports ({decimals} decimals)."
        raise ValueError(msg)
    return str(int(scaled))
