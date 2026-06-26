"""
Porters using callbacks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asyncio import ResolvableAwaitable, resolve_await
from betty.linked_data import LinkedData, LinkedDataPorter

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidableType, VoidType


@final
class CallbackLinkedDataPorter[DataClsT](LinkedDataPorter[DataClsT]):
    """
    Make data portable using a separate loader and dumper.
    """

    def __init__(
        self,
        schema: Callable[[Project], ResolvableAwaitable[VoidableType[PortableMapping]]],
        dumper: Callable[
            [Project, DataClsT], ResolvableAwaitable[LinkedData | VoidType]
        ],
        /,
    ):
        self._schema = schema
        self._dumper = dumper

    @override
    async def schema(self, project: Project, /) -> VoidableType[PortableMapping]:
        return await resolve_await(self._schema(project))

    @override
    async def dump(self, project: Project, data: DataClsT) -> LinkedData | VoidType:
        return await resolve_await(self._dumper(project, data))
