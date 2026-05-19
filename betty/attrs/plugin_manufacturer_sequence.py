"""
Plugin manufacturer sequence properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.attr import ProxyAttr
from betty.attrs.collection_attr import CollectionAttrAttr
from betty.collection.sequence import MutableResolvedSequence
from betty.datas.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.plugin.cls import PluginClsDefinition
from betty.plugin.factory import (
    PluginManufacturer,
    ResolvablePluginManufacturer,
    ResolvablePluginManufacturerSequence,
)
from betty.property import HasProperties

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


@final
class PluginManufacturerSequenceAttr[PluginDefinitionT: PluginClsDefinition, PluginT](
    ProxyAttr[
        HasProperties,
        MutableResolvedSequence[
            PluginManufacturer[PluginDefinitionT, PluginT],
            ResolvablePluginManufacturer[PluginDefinitionT, PluginT],
        ],
        ResolvablePluginManufacturerSequence[PluginDefinitionT, PluginT],
    ]
):
    """
    An attribute containing a sequence of :py:class:`betty.plugin.factory.PluginManufacturer`.
    """

    def __init__(
        self,
        manufacturer: type[PluginManufacturer[PluginDefinitionT, PluginT]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            CollectionAttrAttr(
                PluginManufacturerSequenceDefinition(manufacturer),
                label=label,
                description=description,
            ).setter(manufacturer.resolve_sequence)
        )
