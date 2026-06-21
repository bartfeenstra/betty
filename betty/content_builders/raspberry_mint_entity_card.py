"""
The entity card content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.datas.entity_reference import EntityReference
from betty.entity.has_file_references import HasFileReferences
from betty.extensions._theme import associated_file_references
from betty.factory import DataManufacturable
from betty.image import is_supported_media_type
from betty.locale.localizable.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document
    from betty.entities.file_reference import FileReference
    from betty.entity import Entity
    from betty.entity.collection.pool import EntityPool
    from betty.jinja import Environment


@final
@ContentBuilderDefinition(
    "raspberry-mint-entity-card",
    label=_("Entity card"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class EntityCard(Template, DataManufacturable[EntityReference]):
    """
    A card featuring an entity.

    .. plugin:: content-builder:raspberry-mint-entity-card
    """

    def __init__(
        self, *, ancestry: EntityPool, entity: EntityReference, jinja: Environment
    ):
        super().__init__(jinja=jinja)
        self._entity = entity
        self._ancestry = ancestry

    @override
    @classmethod
    def new_data_cls(cls) -> type[EntityReference]:
        return EntityReference

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: EntityReference, /) -> Self:
        return cls(
            ancestry=project.ancestry,
            entity=data,
            jinja=await project.jinja,
        )

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        entity = self._ancestry[self._entity.type][self._entity.id]
        return [
            "entity/card--" + entity.plugin().id + ".html.j2",
            "entity/card.html.j2",
        ], {
            "entity": entity,
            "entity_image_reference": self._get_image_reference(entity),
        }

    def _get_image_reference(self, entity: Entity) -> FileReference | None:
        if isinstance(entity, HasFileReferences):
            for file_reference in associated_file_references(entity):
                if file_reference.file.private:
                    continue
                if file_reference.file.media_type is None:
                    continue
                if not is_supported_media_type(file_reference.file.media_type):
                    continue
                return file_reference
        return None
