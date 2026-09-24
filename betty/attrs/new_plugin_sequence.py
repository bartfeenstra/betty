"""
Plugin manufacturer sequence attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.attrs.owner import CollectionOwnerAttr
from betty.datas.plugin.manufacturer.sequence import (
    NewPluginSequenceDefinition,
)
from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ty_extensions import Intersection

    from betty.attrs.common import CommonAttr
    from betty.collection.sequence import MutableResolvedSequence
    from betty.localizable import ResolvableLocalizable
    from betty.plugin.cls import (
        NewPlugin,
        ResolvablePluginManufacturer,
    )
    from betty.prop import HasProps


def new_new_plugin_sequence_attr[
    DefinitionT: Intersection[PluginDefinition, ClsDefinition],
    NewPluginT: NewPlugin,
](
    manufacturer: type[NewPluginT],
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[
    HasProps,
    MutableResolvedSequence[
        NewPluginT,
        ResolvablePluginManufacturer[DefinitionT, NewPluginT],
    ],
    Iterable[ResolvablePluginManufacturer[DefinitionT, NewPluginT]],
]:
    """
    Create an attribute containing a sequence of :py:class:`betty.plugin.cls.factory.NewPlugin`.
    """
    return CollectionOwnerAttr(
        NewPluginSequenceDefinition(
            manufacturer,
            label=label,
            description=description,
        )
    ).setter(lambda value: map(manufacturer.resolve, value))
