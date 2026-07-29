"""
Provide search functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import gather
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any, Final, final

from betty.localized import LocalizedStr

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.data import (
        DataDefinition,
        ResolvableDataDefinition,
    )
    from betty.datas.aggregate.record import FieldOperator, RecordDefinition
    from betty.job import Context
    from betty.localizer import Localizer
    from betty.machine_name import MachineName
    from betty.project import Project
    from betty.typing import Number

type Index = Mapping[str, LocalizedStr]


class FieldIndexer[DataT](ABC):
    """
    Index data.
    """

    @abstractmethod
    async def index(self, data: DataT, /, *, localizer: Localizer) -> LocalizedStr:
        """
        Index the data.
        """


@final
class Field:
    """
    A searchable data field.
    """

    def __init__(self, *, importance: Number = 1):
        self.importance: Final[Number] = importance


class RecordIndexer[DataT](ABC):
    """
    Index record data built up from multiple fields.
    """

    @abstractmethod
    def fields(self) -> Mapping[str, Field]:
        """
        The searchable data type's fields.
        """

    @abstractmethod
    async def index(self, data: DataT, /, *, localizer: Localizer) -> Index:
        """
        Index the data.
        """


type Indexer[DataT] = FieldIndexer[DataT] | RecordIndexer[DataT]


class Searcher[DataT](RecordIndexer[DataT]):
    """
    Make a data type searchable.
    """

    @property
    @abstractmethod
    def data(self) -> RecordDefinition[DataT, FieldOperator]:
        """
        The definition of the searchable data type.
        """

    @abstractmethod
    async def datas(self) -> Iterable[DataT]:
        """
        The searchable data objects.
        """

    @abstractmethod
    async def render_result(
        self, data: DataT, /, *, localizer: Localizer, context: Context | None
    ) -> str:
        """
        Render the search result.
        """


@final
@dataclass(frozen=True, slots=True)
class Entry:
    """
    A search entry.
    """

    index: Index
    result: str


@final
class Search:
    """
    The search.
    """

    def __init__(
        self,
        datas: Mapping[MachineName, ResolvableDataDefinition],
        /,
        *,
        project: Project,
    ):
        from betty.data import resolve_data_definition

        self._datas: Mapping[MachineName, DataDefinition[Any, Any, Any, Searcher]] = {
            searcher_id: searcher_data
            for searcher_id, resolvable_searcher_data in datas.items()
            if (searcher_data := resolve_data_definition(resolvable_searcher_data))
            and isinstance(searcher_data.try_indexer, Searcher)
        }
        self._project = project

    async def build(
        self, *, localizer: Localizer, context: Context | None
    ) -> Iterable[Entry]:
        """
        Build the search entries.
        """
        return chain(
            *await gather(*[
                self._build_entries(data, context, localizer)
                for data in self._datas.values()
            ])
        )

    async def _build_entries(
        self,
        data: DataDefinition[Any, Any, Any, Searcher],
        context: Context | None,
        localizer: Localizer,
    ) -> Iterable[Entry]:
        searcher = data.indexer
        return await gather(*[
            self._build_entry(searcher, data, context, localizer)
            for data in await searcher.datas()
        ])

    async def _build_entry[DataT](
        self,
        searcher: Searcher[DataT],
        data: DataT,
        context: Context | None,
        localizer: Localizer,
    ) -> Entry:
        return Entry(
            await searcher.index(data, localizer=localizer),
            await searcher.render_result(data, context=context, localizer=localizer),
        )
