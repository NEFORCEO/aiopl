from typing import ClassVar, Generic

from pydantic import BaseModel, ConfigDict

from aiopaysell.types import _PaysellType


class PaysellMethod(BaseModel, Generic[_PaysellType]):
    """Base Paysell API method class."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    __return_type__: ClassVar[type[_PaysellType]]
    __method_name__: ClassVar[str]
    __http_method__: ClassVar[str] = "POST"
    __requires_auth__: ClassVar[bool] = True

    def build_path(self) -> str:
        """Return the request path, with any path parameters filled in."""
        raise NotImplementedError
