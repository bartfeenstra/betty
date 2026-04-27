"""
Provide search functionality.
"""

from __future__ import annotations

import json
from asyncio import gather, to_thread
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, final, override

from betty.entity import Entity
from betty.entity.has_notes import HasNotes
from betty.file import write
from betty.plugins.entity.file import File
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.media_type.html import HTML
from betty.privacy import is_private

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from babel import Locale

    from betty.job import Context
    from betty.locale.localizable import Localizable
    from betty.locale.localize import Localizer
    from betty.machine_name import MachineName
    from betty.project import Project


async def generate_search_index(
    project: Project,
    result_container_template: Localizable,
    results_container_template: Localizable,
    *,
    context: Context,
) -> None:
    await gather(
        *(
            _generate_search_index_for_locale(
                project,
                result_container_template,
                results_container_template,
                locale,
                context=context,
            )
            for locale in project.locales.keys()  # noqa: SIM118
        )
    )


async def _generate_search_index_for_locale(
    project: Project,
    result_container_template: Localizable,
    results_container_template: Localizable,
    locale: Locale,
    *,
    context: Context,
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
            for entry in await Index(project, context, localizer).build()
        ],
    }
    search_index_json = json.dumps(search_index)
    www_directory = project.localize_www_directory(locale)
    await to_thread(www_directory.mkdir, exist_ok=True, parents=True)
    await write(www_directory / "search-index.json", search_index_json)


_EntityTypeIndexerEntityT = TypeVar(
    "_EntityTypeIndexerEntityT", bound=Entity, default=Entity, covariant=True
)


class EntityTypeIndexer[EntityTypeIndexerEntityT: Entity = Entity]:
    def __init__(self, project: Project, /):
        self._project = project

    async def text(
        self, localizer: Localizer, entity: _EntityTypeIndexerEntityT
    ) -> set[str]:
        text = {entity.id.lower()}

        # Each note is owned by a single other entity, so index it as part of that entity.
        if isinstance(entity, HasNotes):
            for note in entity.notes:
                text.update(note.text.localize(localizer).lower().split())

        return text


class _FallbackIndexer(EntityTypeIndexer[Entity]):
    @override
    async def text(self, localizer: Localizer, entity: Entity) -> set[str]:
        text = await super().text(localizer, entity)
        text.update(entity.label.localize(localizer))
        return text


class _PersonIndexer(EntityTypeIndexer[Person]):
    @override
    async def text(self, localizer: Localizer, entity: Person) -> set[str]:
        text = await super().text(localizer, entity)
        for name in entity.names:
            if name.individual is not None:
                text.update(set(name.individual.lower().split()))
            if name.affiliation is not None:
                text.update(set(name.affiliation.lower().split()))
        return text


class _PlaceIndexer(EntityTypeIndexer[Place]):
    @override
    async def text(self, localizer: Localizer, entity: Place) -> set[str]:
        text = await super().text(localizer, entity)
        for name in entity.names:
            text.update(name.name.localize(localizer).lower().split())
        return text


class _FileIndexer(EntityTypeIndexer[File]):
    @override
    async def text(self, localizer: Localizer, entity: File) -> set[str]:
        text = await super().text(localizer, entity)
        text.update(entity.path.name.strip().lower().split())
        if entity.description:
            text.update(entity.description.localize(localizer).strip().lower().split())
        return text


@final
@dataclass(frozen=True)
class _Entry:
    entity_type_id: MachineName
    result: str
    text: set[str]


class Index:
    """
    Build search indexes.
    """

    def __init__(
        self,
        project: Project,
        context: Context | None,
        localizer: Localizer,
    ):
        self._project = project
        self._context = context
        self._localizer = localizer

    async def build(self) -> Sequence[_Entry]:
        """
        Build the search index.
        """
        specialized_indexers: Mapping[type[Entity], EntityTypeIndexer[Entity]] = {
            File: _FileIndexer(self._project),
            Person: _PersonIndexer(self._project),
            Place: _PlaceIndexer(self._project),
        }
        return [
            entry
            for entries in await gather(
                *[
                    self._build_entities(indexer, entity_type)
                    for entity_type, indexer in specialized_indexers.items()
                ],
                *[
                    self._build_entities(
                        _FallbackIndexer(self._project), entity_type.cls
                    )
                    for entity_type in self._project.upstream.entity_types
                    if entity_type.public_facing
                    and entity_type.cls not in specialized_indexers
                ],
            )
            for entry in entries
            if entry is not None
        ]

    async def _build_entities[EntityT: Entity](
        self, indexer: EntityTypeIndexer[EntityT], entity_type: type[EntityT]
    ) -> Iterable[_Entry | None]:
        return await gather(
            *(
                self._build_entity(indexer, entity)
                for entity in self._project.ancestry[entity_type]
            )
        )

    async def _build_entity[EntityT: Entity](
        self, indexer: EntityTypeIndexer[EntityT], entity: EntityT
    ) -> _Entry | None:
        if is_private(entity):
            return None
        text = await indexer.text(self._localizer, entity)
        if not text:
            return None
        return _Entry(entity.plugin().id, await self._render_entity(entity), text)

    async def _render_entity(self, entity: Entity) -> str:
        jinja = await self._project.jinja
        return await jinja.select_template([
            f"search/result--{entity.plugin().id}.html.j2",
            "search/result.html.j2",
        ]).render_async(
            document=await self._project.new_document(
                HTML,
                context=self._context,
                localizer=self._localizer,
            ),
            entity=entity,
        )
