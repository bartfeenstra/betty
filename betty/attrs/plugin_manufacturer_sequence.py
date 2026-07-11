"""
Plugin manufacturer sequence attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import CollectionOwnerAttr
from betty.datas.plugin.manufacturer.sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.plugin.cls import PluginClsDefinition

if TYPE_CHECKING:
    from betty.attr import Object
    from betty.attrs.common import CommonAttr
    from betty.collection.sequence import MutableResolvedSequence
    from betty.localizable import ResolvableLocalizable
    from betty.plugin.factory import (
        PluginManufacturer,
        ResolvablePluginManufacturer,
        ResolvablePluginManufacturerSequence,
    )


def new_plugin_manufacturer_sequence_attr[
    PluginDefinitionT: PluginClsDefinition,
    PluginT,
](
    manufacturer: type[PluginManufacturer[PluginDefinitionT, PluginT]],
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[
    Object,
    MutableResolvedSequence[
        PluginManufacturer[PluginDefinitionT, PluginT],
        ResolvablePluginManufacturer[PluginDefinitionT, PluginT],
    ],
    ResolvablePluginManufacturerSequence[PluginDefinitionT, PluginT],
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
    ).setter(manufacturer.resolve_sequence)
