"""
Entity URL generators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard, final, override

from betty.entity import Entity
from betty.string import camel_case_to_kebab_case
from betty.url_generators._entity import _EntityUrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.url_generators.path import PathUrlGenerator


@final
class EntityUrlGenerator(_EntityUrlGenerator[Entity]):
    """
    Generate URLs for entities.
    """

    def __init__(self, path_url_generator: PathUrlGenerator, /):
        super().__init__(
            path_url_generator, "/{entity_type}/{entity_id}/index{extension}"
        )

    @final
    @override
    def supports(self, resource: Any, /) -> TypeGuard[Entity]:
        return isinstance(resource, Entity)

    @override
    def _pattern_data(self, entity: Entity, /) -> Mapping[str, str]:
        return {
            "entity_type": camel_case_to_kebab_case(entity.plugin().id),
            "entity_id": entity.id,
        }
