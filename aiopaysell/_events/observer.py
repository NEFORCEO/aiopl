from typing import TYPE_CHECKING

from .handler import HandlerObject

if TYPE_CHECKING:
    from collections.abc import Callable

    from .handler import CallbackType


class EventObserver:
    """Stores handlers for one event type and dispatches to the first match."""

    def __init__(self) -> None:
        self.handlers: list[HandlerObject] = []

    def __call__(
        self,
        *filters: "CallbackType",
    ) -> "Callable[[CallbackType], CallbackType]":
        def wrapper(handler: "CallbackType") -> "CallbackType":
            self.register(handler, *filters)
            return handler

        return wrapper

    def register(self, handler: "CallbackType", *filters: "CallbackType") -> None:
        """Register a handler, optionally guarded by filters (e.g. ``F.status == "paid"``)."""  # noqa: E501
        self.handlers.append(HandlerObject(handler, filters))

    async def trigger(self, event: object, **kwargs: object) -> bool:
        """Run the first matching handler; return whether one matched."""
        for handler in self.handlers:
            matched, data = await handler.check(event)
            if matched:
                await handler.call(event, data | kwargs)
                return True
        return False
