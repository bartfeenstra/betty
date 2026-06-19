"""
Entity type URL generators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard, final, override

from betty.entity import Entity, EntityDefinition
from betty.plugin.resolve import resolve_plugin_definition
from betty.string import camel_case_to_kebab_case
from betty.url_generators._entity import _EntityUrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.url_generators.path import PathUrlGenerator


@final
class EntityTypeUrlGenerator(_EntityUrlGenerator[EntityDefinition | type[Entity]]):
    """
    Generate URLs for entity types.
    """

    def __init__(self, path_url_generator: PathUrlGenerator, /):
        super().__init__(path_url_generator, "/{entity_type}/index{extension}")

    @final
    @override
    def supports(self, resource: Any, /) -> TypeGuard[EntityDefinition | type[Entity]]:
        return (
            isinstance(resource, EntityDefinition)
            or isinstance(resource, type)
            and issubclass(resource, Entity)
        )

    @override
    def _pattern_data(
        self, entity_type: EntityDefinition | type[Entity], /
    ) -> Mapping[str, str]:
        return {
            "entity_type": camel_case_to_kebab_case(
                resolve_plugin_definition(entity_type).id
            ),
        }
