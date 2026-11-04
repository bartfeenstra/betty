"""
Jobs to generate HTML pages for entity types.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.definition import ResolvableDefinition, resolve_definition
from betty.jobs.generate_entity_type import GenerateEntityType
from betty.jobs.template import CollectionResourceTemplate

if TYPE_CHECKING:
    from betty.entity import EntityDefinition
    from betty.jinja import ResolvableTemplateNames
    from betty.project import Project


@final
class GenerateEntityTypeHtml(CollectionResourceTemplate):
    """
    Generate HTML pages for an entity type.
    """

    def __init__(
        self,
        entity_type: ResolvableDefinition[EntityDefinition],
        /,
        *,
        project: Project,
    ):
        entity_type = resolve_definition(entity_type)
        super().__init__(
            entity_type,
            Path(entity_type.id),
            *(entity for entity in project.ancestry[entity_type] if entity.public),
            dependencies=[GenerateEntityType.id_for(entity_type)],
            project=project,
        )

    @override
    @classmethod
    def id_prefix(cls, entity_type: ResolvableDefinition[EntityDefinition], /) -> str:
        return GenerateEntityType.id_for(entity_type)

    @override
    @classmethod
    def template(
        cls, entity_type: ResolvableDefinition[EntityDefinition], /
    ) -> ResolvableTemplateNames:
        return (
            f"entity/page-list--{resolve_definition(entity_type).id}.html.j2",
            "entity/page-list.html.j2",
        )
