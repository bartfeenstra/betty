"""
Entity search indexers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entity import Entity, EntityDefinition
from betty.media_types.html import HTML
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.search import Field, Index, Searcher

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.job import Context
    from betty.localizer import Localizer
    from betty.project import Project


@final
class EntitySearcher[EntityT: Entity = Entity](Searcher[EntityT]):
    """
    Make an entity type searchable.
    """

    def __init__(
        self, entity_type: ResolvablePluginDefinition[EntityDefinition[EntityT]], /
    ):
        self._entity_type = resolve_plugin_definition(entity_type)

    @override
    @property
    def data(self) -> EntityDefinition[EntityT]:
        return self._entity_type

    @override
    async def datas(self, project: Project) -> Iterable[EntityT]:
        return project.ancestry[self._entity_type]

    # @todo We need scaffolding that does this for any RecordDefinition data.
    # @todo Make it easy to override the importance (or any part of the field config?), and perhaps to disable
    # @todo search for a field that provides its own search support? Do this through FieldDefinition?
    # @todo
    # @todo
    # @todo new_localizable_attr() should provide a default Indexer.
    # @todo
    # @todo How to name shared fields?
    # @todo - Fields that belong to a single entity type are easy: prefix with entity type ID.
    # @todo - How even to determine that a field is shared, and shared by what?
    # @todo - Entity.id should become "entity.id"
    # @todo - Entity.label should become "entity.label"
    # @todo - File.path should become "file.path"
    # @todo - HasDescription.description should become..... what?
    # @todo
    # @todo
    @override
    def fields(self) -> Mapping[str, Field]:
        # @todo This is where we want a generic RecordDefinition-based indexer.
        raise NotImplementedError
        return {
            "entity.id": Field(),
            "entity.label": Field(importance=2),
            "entity.description": Field(),
            "entity.notes": Field(importance=0.1),
        }

    @override
    async def index(
        self, entity: EntityT, /, *, localizer: Localizer, project: Project
    ) -> Index:
        # @todo This is where we want a generic RecordDefinition-based indexer.
        raise NotImplementedError

    @override
    async def render_result(
        self,
        entity: EntityT,
        /,
        *,
        localizer: Localizer,
        context: Context | None,
        project: Project,
    ) -> str:
        jinja = await project.jinja
        return await jinja.select_template([
            # @todo Now that we support other searchable data types besides entities, we should namespace these
            # @todo templates, perhaps? Maybe move them into the entity namespace (instead of the search)?
            # @todo
            f"search/result--{entity.plugin().id}.html.j2",
            "search/result.html.j2",
        ]).render_async(
            document=await project.new_document(
                HTML,
                context=context,
                localizer=localizer,
            ),
            entity=entity,
        )
