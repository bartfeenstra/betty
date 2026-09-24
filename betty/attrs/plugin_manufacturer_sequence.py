"""
Plugin manufacturer sequence attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import CollectionOwnerAttr
from betty.datas.plugin.manufacturer.sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ty_extensions import Intersection

    from betty.attrs.common import CommonAttr
    from betty.collection.sequence import MutableResolvedSequence
    from betty.localizable import ResolvableLocalizable
    from betty.plugin.factory import PluginManufacturer, ResolvablePluginManufacturer
    from betty.prop import HasProps


def new_plugin_manufacturer_sequence_attr[
    DefinitionT: Intersection[PluginDefinition, ClsDefinition],
    PluginManufacturerT: PluginManufacturer,
](
    manufacturer: type[PluginManufacturerT],
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[
    HasProps,
    MutableResolvedSequence[
        PluginManufacturerT,
        ResolvablePluginManufacturer[DefinitionT, PluginManufacturerT],
    ],
    Iterable[ResolvablePluginManufacturer[DefinitionT, PluginManufacturerT]],
]:
    """
    Create an attribute containing a sequence of :py:class:`betty.plugin.factory.PluginManufacturer`.
    """
    return CollectionOwnerAttr(
        PluginManufacturerSequenceDefinition(
            manufacturer,
            label=label,
            description=description,
        )
    ).setter(lambda value: map(manufacturer.resolve, value))
