"""
The entity card content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.ancestry.has_file_references import HasFileReferences
from betty.content import ContentDefinition
from betty.image import is_supported_media_type
from betty.locale.localizable.gettext import _
from betty.model.reference import EntityReference
from betty.plugins.asset.raspberry_mint import RaspberryMint
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.extension._theme import associated_file_references
from betty.project import Project
from betty.requirement import require
from betty.service.factory import DataManufacturable

if TYPE_CHECKING:
    from betty.ancestry import Ancestry
    from betty.document import Document
    from betty.jinja import Environment
    from betty.model import Entity
    from betty.plugins.entity.file_reference import FileReference


@final
@ContentDefinition(
    "raspberry-mint-entity-card", label=_("Entity card"), requires={RaspberryMint}
)
class EntityCard(Template, DataManufacturable[EntityReference]):
    """
    A card featuring an entity.

    .. plugin:: content:raspberry-mint-entity-card
    """

    def __init__(
        self, *, ancestry: Ancestry, entity: EntityReference, jinja: Environment
    ):
        super().__init__(jinja=jinja)
        self._entity = entity
        self._ancestry = ancestry

    @override
    @classmethod
    def new_data_cls(cls) -> type[EntityReference]:
        return EntityReference

    @override
    @classmethod
    @require(Project)
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
