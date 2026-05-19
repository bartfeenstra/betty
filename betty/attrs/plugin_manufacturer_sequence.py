"""
Plugin manufacturer sequence attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.collection_attr import CollectionAttrAttr
from betty.datas.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.plugin.cls import PluginClsDefinition

if TYPE_CHECKING:
    from betty.attrs.owner import OwnerAttr
    from betty.collection.sequence import MutableResolvedSequence
    from betty.locale.localizable import ResolvableLocalizable
    from betty.plugin.factory import (
        PluginManufacturer,
        ResolvablePluginManufacturer,
        ResolvablePluginManufacturerSequence,
    )
    from betty.property import HasProperties


def new_plugin_manufacturer_sequence_attr[
    PluginDefinitionT: PluginClsDefinition,
    PluginT,
](
    manufacturer: type[PluginManufacturer[PluginDefinitionT, PluginT]],
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> OwnerAttr[
    HasProperties,
    MutableResolvedSequence[
        PluginManufacturer[PluginDefinitionT, PluginT],
        ResolvablePluginManufacturer[PluginDefinitionT, PluginT],
    ],
    ResolvablePluginManufacturerSequence[PluginDefinitionT, PluginT],
]:
    """
    Create an attribute containing a sequence of :py:class:`betty.plugin.factory.PluginManufacturer`.
    """
    return CollectionAttrAttr(
        PluginManufacturerSequenceDefinition(manufacturer),
        label=label,
        description=description,
    ).setter(manufacturer.resolve_sequence)
