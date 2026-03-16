"""
The entity card content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.locale.localizable.gettext import _
from betty.model.reference import EntityReference
from betty.plugins.content.template import Template, TemplateBuild
from betty.service.factory import DataManufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from betty.ancestry import Ancestry
    from betty.document import Document
    from betty.jinja import Environment
    from betty.project import Project


@final
@ContentDefinition("raspberry-mint-entity-card", label=_("Entity card"))
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
    @require_project
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
        ], {"entity": entity}
