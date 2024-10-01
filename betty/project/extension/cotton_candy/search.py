"""
Provide Cotton Candy's search functionality.
"""

from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, TypeVar, Generic

from typing_extensions import override

from betty.ancestry.file import File
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.asyncio import gather
from betty.model import Entity
from betty.privacy import is_private
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project
    from betty.locale.localizer import Localizer
    from betty.job import Context
    from collections.abc import Mapping, Iterable, Sequence

_EntityT = TypeVar("_EntityT", bound=Entity)


class _EntityTypeIndexer(Generic[_EntityT], ABC):
    @abstractmethod
    def text(self, entity: _EntityT) -> str | None:
        pass


class _PersonIndexer(_EntityTypeIndexer[Person]):
    @override
    def text(self, entity: Person) -> str | None:
        names = []
        for name in entity.names:
            if name.individual is not None:
                names.append(name.individual.lower())
            if name.affiliation is not None:
                names.append(name.affiliation.lower())
        if not names:
            return None
        return " ".join(names)


class _PlaceIndexer(_EntityTypeIndexer[Place]):
    @override
    def text(self, entity: Place) -> str | None:
        return " ".join(
            translation.lower()
            for name in entity.names
            for translation in name.name.translations.values()
        )


class _FileIndexer(_EntityTypeIndexer[File]):
    @override
    def text(self, entity: File) -> str | None:
        if not entity.description:
            return None
        return " ".join(
            description.lower()
            for description in entity.description.translations.values()
        )


@internal
class Index:
    """
    Build search indexes.
    """

    def __init__(
        self,
        project: Project,
        job_context: Context | None,
        localizer: Localizer,
    ):
        self._project = project
        self._job_context = job_context
        self._localizer = localizer

    async def build(self) -> Sequence[Mapping[str, str]]:
        """
        Build the search index.
        """
        return [
            entry
            for entries in await gather(
                self._build_entities(_PersonIndexer(), Person),
                self._build_entities(_PlaceIndexer(), Place),
                self._build_entities(_FileIndexer(), File),
            )
            for entry in entries
            if entry is not None
        ]

    async def _build_entities(
        self, indexer: _EntityTypeIndexer[_EntityT], entity_type: type[_EntityT]
    ) -> Iterable[Mapping[str, str] | None]:
        return await gather(
            *(
                self._build_entity(indexer, entity)
                for entity in self._project.ancestry[entity_type]
            )
        )

    async def _build_entity(
        self, indexer: _EntityTypeIndexer[_EntityT], entity: _EntityT
    ) -> Mapping[str, str] | None:
        if is_private(entity):
            return None
        text = indexer.text(entity)
        if text is None:
            return None
        return {
            "text": text,
            "result": await self._render_entity(entity),
        }

    async def _render_entity(self, entity: Entity) -> str:
        return await self._project.jinja2_environment.select_template(
            [
                f"search/result--{entity.plugin_id()}.html.j2",
                "search/result.html.j2",
            ]
        ).render_async(
            {
                "job_context": self._job_context,
                "localizer": self._localizer,
                "entity": entity,
            }
        )
