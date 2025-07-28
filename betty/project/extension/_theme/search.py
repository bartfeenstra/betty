"""
Provide search functionality.
"""

from __future__ import annotations

import json
from abc import ABC
from asyncio import gather
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar, final

import aiofiles
from typing_extensions import override

from betty.ancestry.file import File
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.model import Entity
from betty.privacy import is_private
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from betty.job import Context
    from betty.locale.localizable import Localizable
    from betty.locale.localizer import Localizer
    from betty.machine_name import MachineName
    from betty.project import Project

_EntityT = TypeVar("_EntityT", bound=Entity)


async def generate_search_index(
    project: Project,
    result_container_template: Localizable,
    results_container_template: Localizable,
    *,
    job_context: Context,
) -> None:
    await gather(
        *(
            _generate_search_index_for_locale(
                project,
                result_container_template,
                results_container_template,
                locale,
                job_context=job_context,
            )
            for locale in project.configuration.locales
        )
    )


async def _generate_search_index_for_locale(
    project: Project,
    result_container_template: Localizable,
    results_container_template: Localizable,
    locale: str,
    *,
    job_context: Context,
) -> None:
    localizers = await project.localizers
    localizer = localizers.get(locale)
    search_index = {
        "resultContainerTemplate": result_container_template.localize(localizer),
        "resultsContainerTemplate": results_container_template.localize(localizer),
        "index": [
            {
                "entityTypeId": entry.entity_type_id,
                "text": " ".join(entry.text),
                "result": entry.result,
            }
            for entry in await Index(project, job_context, localizer).build()
        ],
    }
    search_index_json = json.dumps(search_index)
    async with aiofiles.open(
        project.configuration.localize_www_directory_path(locale) / "search-index.json",
        mode="w",
    ) as f:
        await f.write(search_index_json)


class _EntityTypeIndexer(Generic[_EntityT], ABC):
    def __init__(self, project: Project):
        self._project = project

    async def text(self, localizer: Localizer, entity: _EntityT) -> set[str]:
        text = {entity.id.lower()}

        # Each note is owned by a single other entity, so index it as part of that entity.
        if isinstance(entity, HasNotes):
            for note in entity.notes:
                text.update(note.text.localize(localizer).lower().split())

        return text


class _PersonIndexer(_EntityTypeIndexer[Person]):
    def __init__(self, project: Project):
        self._project = project

    @override
    async def text(self, localizer: Localizer, entity: Person) -> set[str]:
        text = await super().text(localizer, entity)
        for name in entity.names:
            if name.individual is not None:
                text.update(set(name.individual.lower().split()))
            if name.affiliation is not None:
                text.update(set(name.affiliation.lower().split()))
        return text


class _PlaceIndexer(_EntityTypeIndexer[Place]):
    @override
    async def text(self, localizer: Localizer, entity: Place) -> set[str]:
        text = await super().text(localizer, entity)
        for name in entity.names:
            text.update(name.name.localize(localizer).lower().split())
        return text


class _FileIndexer(_EntityTypeIndexer[File]):
    @override
    async def text(self, localizer: Localizer, entity: File) -> set[str]:
        text = await super().text(localizer, entity)
        text.update(entity.path.name.strip().lower().split())
        if entity.description:
            text.update(entity.description.localize(localizer).strip().lower().split())
        return text


class _SourceIndexer(_EntityTypeIndexer[Source]):
    pass


@final
@dataclass(frozen=True)
class _Entry:
    entity_type_id: MachineName
    result: str
    text: set[str]


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

    async def build(self) -> Sequence[_Entry]:
        """
        Build the search index.
        """
        return [
            entry
            for entries in await gather(
                self._build_entities(_PersonIndexer(self._project), Person),
                self._build_entities(_PlaceIndexer(self._project), Place),
                self._build_entities(_FileIndexer(self._project), File),
                self._build_entities(_SourceIndexer(self._project), Source),
            )
            for entry in entries
            if entry is not None
        ]

    async def _build_entities(
        self, indexer: _EntityTypeIndexer[_EntityT], entity_type: type[_EntityT]
    ) -> Iterable[_Entry | None]:
        return await gather(
            *(
                self._build_entity(indexer, entity)
                for entity in self._project.ancestry[entity_type]
            )
        )

    async def _build_entity(
        self, indexer: _EntityTypeIndexer[_EntityT], entity: _EntityT
    ) -> _Entry | None:
        if is_private(entity):
            return None
        text = await indexer.text(self._localizer, entity)
        if not text:
            return None
        return _Entry(entity.plugin_id(), await self._render_entity(entity), text)

    async def _render_entity(self, entity: Entity) -> str:
        jinja2_environment = await self._project.jinja2_environment
        return await jinja2_environment.select_template(
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
