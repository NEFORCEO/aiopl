from enum import Enum
from typing import Literal


class Asset(str, Enum):
    """Cryptocurrency accepted by an invoice."""

    TON = "TON"
    USDT_TON = "USDT_TON"


LiteralAsset = Literal["TON", "USDT_TON"]

ASSET_DECIMALS: dict[str, int] = {
    "TON": 9,
    "USDT_TON": 6,
}
"""
Smallest-unit decimals per asset.

1.5 TON is ``"1500000000"``, 1.5 USDT_TON is ``"1500000"``.
"""
