"""
Optional data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.data import DataDefinition
from betty.linked_data_porters.callback import CallbackLinkedDataPorter
from betty.porters.optional import OptionalPorter
from betty.sample import Sample, Size
from betty.typing import Void, Voidable, VoidableType, VoidType

if TYPE_CHECKING:
    from betty.linked_data import LinkedData
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class OptionalDefinition[DataClsT](DataDefinition[DataClsT | None]):
    """
    Wrap another data definition to make it optional, e.g. allow ``None``.
    """

    def __init__(self, proxied: DataDefinition[DataClsT], /):
        super().__init__(
            label=proxied.label,
            description=proxied.description,
            porter=OptionalPorter(proxied.porter),
            linked_data_porter=CallbackLinkedDataPorter(
                self._linked_data_schema, self._dump_linked_data
            ),
            samples=[
                lambda: Sample(None, label="Minimal", size=Size.MINIMAL),
                proxied.samples,
            ],
        )
        self._proxied = proxied

    async def _linked_data_schema(
        self, project: Project, /
    ) -> VoidableType[PortableMapping]:
        schema = await self._proxied.linked_data_porter.schema(project)
        if isinstance(schema, Voidable):
            return schema
        return Voidable(schema)

    async def _dump_linked_data(
        self, project: Project, data: DataClsT | None, /
    ) -> LinkedData | VoidType:
        if data is None:
            return Void
        return await self._proxied.linked_data_porter.dump(project, data)
