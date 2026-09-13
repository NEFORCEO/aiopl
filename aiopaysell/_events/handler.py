import inspect
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from magic_filter import MagicFilter

CallbackType = Callable[..., Any]


@dataclass(slots=True)
class HandlerObject:
    """A registered event handler together with its filters."""

    handler: CallbackType
    filters: tuple["MagicFilter | CallbackType", ...]

    async def check(self, event: object) -> tuple[bool, dict[str, Any]]:
        """Check whether this handler should run for the given event."""
        data: dict[str, Any] = {}
        for f in self.filters:
            check: object
            if isinstance(f, MagicFilter):
                check = f.resolve(event)
            elif inspect.iscoroutinefunction(f):
                check = await f(event)
            else:
                check = f(event)
            if not check:
                return False, data
            if isinstance(check, dict):
                data.update(check)
        return True, data

    async def call(self, event: object, data: dict[str, Any] | None = None) -> None:
        """Call the handler with the event and any extra data it accepts."""
        data = data or {}
        spec = inspect.getfullargspec(self.handler)
        is_async = inspect.iscoroutinefunction(self.handler)
        bound = partial(
            self.handler,
            event,
            **(
                data
                if spec.varkw is not None
                else {k: v for k, v in data.items() if k in spec.args}
            ),
        )
        if is_async:
            await bound()
        else:
            bound()
