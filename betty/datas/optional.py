"""
Optional data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Never, final, override

from betty.data import DataDefinition
from betty.definition.cls import OnSetCls
from betty.portable import Porter
from betty.porters.data_proxy import DataDefinitionProxyPorter
from betty.porters.optional import OptionalPorter
from betty.sample import Sample, Size
from betty.search import Field, FieldIndexer, Index, Indexer, RecordIndexer

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.localized import LocalizedStr
    from betty.localizer import Localizer
    from betty.project import Project


@final
class _OptionalFieldIndexer[DataT](FieldIndexer[DataT | None]):
    def __init__(self, proxied: FieldIndexer[DataT], /):
        self.__proxied = proxied

    @override
    async def index(
        self, data: DataT | None, /, *, localizer: Localizer, project: Project
    ) -> LocalizedStr | None:
        if data is None:
            return None
        return await self.__proxied.index(data, localizer=localizer, project=project)


@final
class _OptionalRecordIndexer[DataT](RecordIndexer[DataT | None]):
    def __init__(self, proxied: RecordIndexer[DataT], /):
        self.__proxied = proxied

    @override
    def fields(self) -> Mapping[str, Field]:
        return self.__proxied.fields()

    @override
    async def index(
        self, data: DataT | None, /, *, localizer: Localizer, project: Project
    ) -> Index:
        if data is None:
            return {}
        return await self.__proxied.index(data, localizer=localizer, project=project)


@final
class OptionalDefinition[DataT](
    DataDefinition[DataT | None, Never, Porter[DataT | None], Indexer[DataT | None]]
):
    """
    Wrap another data definition to make it optional, e.g. allow ``None``.
    """

    def __init__(self, proxied: DataDefinition[DataT, Never, Porter[DataT]], /):
        super().__init__(
            label=proxied.label,
            description=proxied.description,
            indexer=OnSetCls(
                lambda definition: (
                    None
                    if definition.try_indexer is None
                    else _OptionalFieldIndexer(definition.indexer)
                    if isinstance(definition.indexer, FieldIndexer)
                    else _OptionalRecordIndexer(definition.indexer)
                )
            ),
            porter=OptionalPorter(DataDefinitionProxyPorter(proxied)),
            samples=[
                lambda: Sample(None, label="Minimal", size=Size.MINIMAL),
                proxied.samples,
            ],
        )
