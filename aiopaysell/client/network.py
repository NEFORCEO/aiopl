from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiopaysell._methods import PaysellMethod


@dataclass(frozen=True)
class Network:
    """Configuration for the Paysell API server."""

    name: str
    """Net name."""
    base: str
    """Base URL."""

    def url(self, method: "PaysellMethod") -> str:
        """Return the full URL for a method."""
        return self.base + method.build_path()


MAINNET = Network(name="MAINNET", base="https://paysell.me/api/merchant/v1")
