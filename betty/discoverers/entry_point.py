"""
Discover definitions through Python package entry points.
"""

from __future__ import annotations

from importlib import metadata
from types import ModuleType
from typing import TYPE_CHECKING, final

from betty.definition import Definition, HasDefinition
from betty.definition.cls import ClsDefinition
from betty.discoverers.module import (
    DefinitionDiscoverer,
    HasDefinitionDiscoverer,
    SubmoduleHasDefinitionDiscoverer,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.definition.discover import Discovery
    from betty.service_level import ServiceLevel


@final
class EntryPointDiscoverer[DefinitionT: Definition]:
    """
    Discover definitions through Python package entry points.
    """

    def __init__(self, type_: type[DefinitionT], group: str, /):
        self._type = type_
        self._group = group

    def __call__(self, services: ServiceLevel, /) -> Iterator[Discovery[DefinitionT]]:
        """
        Discover the definitions.
        """
        for entry_point_metadata in metadata.entry_points(group=f"betty.{self._group}"):
            entry_point = entry_point_metadata.load()
            if isinstance(entry_point, ModuleType):
                if issubclass(self._type, ClsDefinition):
                    yield HasDefinitionDiscoverer(self._type, entry_point.__name__)  # ty: ignore[invalid-yield]
                    yield SubmoduleHasDefinitionDiscoverer(
                        self._type, entry_point.__name__
                    )  # ty: ignore[invalid-yield]
                else:
                    yield DefinitionDiscoverer(self._type, entry_point.__name__)
            elif isinstance(entry_point, type) and issubclass(
                entry_point, HasDefinition
            ):
                yield entry_point.definition
            else:
                yield entry_point
