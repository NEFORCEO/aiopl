from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel, ConfigDict, PrivateAttr

if TYPE_CHECKING:
    from aiopaysell.client.client import Paysell


class PaysellObject(BaseModel):
    """Base class for API objects, bound to the client that fetched them."""

    _client: "Paysell" = PrivateAttr()

    model_config = ConfigDict(extra="allow")

    def model_post_init(self, context: object) -> None:
        """Bind the owning client, if one was passed as validation context."""
        if isinstance(context, dict) and "client" in context:
            self._client = context["client"]


_PaysellType = TypeVar("_PaysellType", bound="PaysellObject")
