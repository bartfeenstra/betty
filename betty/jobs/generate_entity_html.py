"""
Jobs to generate HTML pages for entities.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.entity import Entity
from betty.jobs.generate_entity import GenerateEntity
from betty.jobs.template import ResourceTemplate

if TYPE_CHECKING:
    from betty.jinja import ResolvableTemplateNames
    from betty.project import Project


@final
class GenerateEntityHtml(ResourceTemplate[Entity]):
    """
    Generate HTML pages for an entity.
    """

    def __init__(self, entity: Entity, /, *, project: Project):
        super().__init__(
            entity,
            Path(entity.definition.id) / entity.id,
            dependencies=[GenerateEntity.id_for(entity)],
            project=project,
        )

    @override
    @classmethod
    def id_prefix(cls, entity: Entity, /) -> str:
        return GenerateEntity.id_for(entity)

    @override
    @classmethod
    def template(cls, entity: Entity, /) -> ResolvableTemplateNames:
        return (
            f"entity/page--{entity.definition.id}.html.j2",
            "entity/page.html.j2",
        )
