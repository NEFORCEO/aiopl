from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .observer import EventObserver


class BaseRouter:
    """Base router: holds named event observers and can nest sub-routers."""

    def __init__(self, *, name: str | None = None) -> None:
        self.name = name or hex(id(self))
        self.observers: dict[str, EventObserver] = {}
        self.parent: BaseRouter | None = None
        self.sub_routers: list[BaseRouter] = []

    def include_router(self, router: "Self") -> None:
        """Attach a sub-router of the same kind to this one."""
        if not isinstance(self, type(router)):
            msg = f"Router {router} is not a {type(self).__name__!r} instance"
            raise TypeError(msg)
        if router is self:
            msg = "Router cannot include self"
            raise ValueError(msg)
        if router.parent is not None:
            msg = f"Router is already attached to {router.parent}"
            raise RuntimeError(msg)
        parent = self.parent
        while parent is not None:
            if parent is router:
                msg = f"Circular inclusion between {self} and {router}"
                raise RuntimeError(msg)
            parent = parent.parent
        router.parent = self
        self.sub_routers.append(router)

    def include_routers(self, *routers: "Self") -> None:
        """Attach multiple sub-routers at once."""
        for router in routers:
            self.include_router(router)

    async def propagate_event(
        self,
        event: object,
        event_type: str,
        **kwargs: object,
    ) -> bool:
        """Dispatch ``event`` to the matching observer, then to every sub-router."""
        is_handled = False
        observer = self.observers.get(event_type)
        if observer is not None:
            is_handled = await observer.trigger(event, **kwargs)
        for router in self.sub_routers:
            if await router.propagate_event(event, event_type, **kwargs):
                is_handled = True
        return is_handled

    def __str__(self) -> str:
        return f"{type(self).__name__} {self.name}"

    def __repr__(self) -> str:
        return f"<{self}>"
