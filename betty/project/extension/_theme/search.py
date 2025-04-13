"""
Provide Cotton Candy's search functionality.
"""

from __future__ import annotations

import json
from abc import ABC
from asyncio import gather
from dataclasses import dataclass
from inspect import getmembers
from typing import TYPE_CHECKING, Generic, TypeVar, cast, final

import aiofiles
from typing_extensions import override

from betty.ancestry.file import File
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.locale.localizable import (
    Localizable,
    StaticTranslationsLocalizable,
    StaticTranslationsLocalizableAttr,
)
from betty.model import Entity
from betty.privacy import is_private
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from betty.ancestry import Ancestry
    from betty.jinja2 import Environment
    from betty.job import Context
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
    localizer = await localizers.get(locale)
    search_index = {
        "resultContainerTemplate": result_container_template.localize(localizer),
        "resultsContainerTemplate": results_container_template.localize(localizer),
        "index": [
            {
                "entityTypeId": entry.entity_type_id,
                "text": " ".join(entry.text),
                "result": entry.result,
            }
            for entry in await Index(
                project.ancestry,
                await project.jinja2_environment,
                job_context,
                localizer,
            ).build()
        ],
    }
    search_index_json = json.dumps(search_index)
    async with aiofiles.open(
        project.configuration.localize_www_directory_path(locale) / "search-index.json",
        mode="w",
    ) as f:
        await f.write(search_index_json)


def _static_translations_to_text(
    translations: StaticTranslationsLocalizable,
) -> set[str]:
    return {
        word
        for translation in translations.translations.values()
        for word in translation.strip().lower().split()
    }


class _EntityTypeIndexer(Generic[_EntityT], ABC):
    def text(self, localizer: Localizer, entity: _EntityT) -> set[str]:
        text = {entity.id.lower()}

        # Each note is owner by a single other entity, so index it as part of that entity.
        if isinstance(entity, HasNotes):
            for note in entity.notes:
                text.update(_static_translations_to_text(note.text))

        for attr_name, class_attr_value in getmembers(type(entity)):
            if isinstance(class_attr_value, StaticTranslationsLocalizableAttr):
                text.update(
                    _static_translations_to_text(
                        cast(
                            "StaticTranslationsLocalizable", getattr(entity, attr_name)
                        )
                    )
                )

        return text


class _PersonIndexer(_EntityTypeIndexer[Person]):
    @override
    def text(self, localizer: Localizer, entity: Person) -> set[str]:
        text = super().text(localizer, entity)
        for name in entity.names:
            if name.individual is not None:
                text.update(set(name.individual.lower().split()))
            if name.affiliation is not None:
                text.update(set(name.affiliation.lower().split()))
        return text


class _PlaceIndexer(_EntityTypeIndexer[Place]):
    @override
    def text(self, localizer: Localizer, entity: Place) -> set[str]:
        text = super().text(localizer, entity)
        for name in entity.names:
            text.update(_static_translations_to_text(name.name))
        return text


class _FileIndexer(_EntityTypeIndexer[File]):
    @override
    def text(self, localizer: Localizer, entity: File) -> set[str]:
        text = super().text(localizer, entity)
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
        ancestry: Ancestry,
        jinja2_environment: Environment,
        job_context: Context | None,
        localizer: Localizer,
    ):
        self._ancestry = ancestry
        self._jinja2_environment = jinja2_environment
        self._job_context = job_context
        self._localizer = localizer

    async def build(self) -> Sequence[_Entry]:
        """
        Build the search index.
        """
        return [
            entry
            for entries in await gather(
                self._build_entities(_PersonIndexer(), Person),
                self._build_entities(_PlaceIndexer(), Place),
                self._build_entities(_FileIndexer(), File),
                self._build_entities(_SourceIndexer(), Source),
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
                for entity in self._ancestry[entity_type]
            )
        )

    async def _build_entity(
        self, indexer: _EntityTypeIndexer[_EntityT], entity: _EntityT
    ) -> _Entry | None:
        if is_private(entity):
            return None
        text = indexer.text(self._localizer, entity)
        if not text:
            return None
        return _Entry(entity.plugin_id(), await self._render_entity(entity), text)

    async def _render_entity(self, entity: Entity) -> str:
        return await self._jinja2_environment.select_template(
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
