"""
Plugin definition configurations attributes.
"""

from __future__ import annotations

from operator import not_
from typing import TYPE_CHECKING

from betty.attrs.owner import CollectionOwnerAttr
from betty.collection.catalog import MutableCatalog
from betty.collections.catalog.dict import DictCatalog
from betty.datas.aggregate.collection.catalog import CatalogDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.plugin.definition import PluginDefinitionConfig
from betty.definition.id import ResolvableId
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.porters.omit_field import OmitFieldPorter

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ty_extensions import Intersection

    from betty.attrs.common import CommonAttr
    from betty.localizer import AnyLocalizable
    from betty.prop import HasProps


def new_plugin_definition_datas_attr[
    DefinitionT: Intersection[PluginDefinition, ObjectDefinition]
](
    plugin_type: type[DefinitionT],
    item: type[PluginDefinitionConfig[DefinitionT]],
    *,
    label: AnyLocalizable | None = None,
    description: AnyLocalizable | None = None,
) -> CommonAttr[
    HasProps,
    MutableCatalog[
        MachineName,
        ResolvableId[DefinitionT],
        PluginDefinitionConfig[DefinitionT],
        PluginDefinitionConfig[DefinitionT],
    ],
    Iterable[PluginDefinitionConfig[DefinitionT]],
]:
    """
    Create attribute containing a :py:class:`betty.collection.catalog.Catalog` of :py:class:`betty.datas.plugin.definition.PluginDefinitionConfig`.
    """
    return CollectionOwnerAttr(
        FieldDefinition(
            CatalogDefinition[
                MutableCatalog[
                    MachineName,
                    ResolvableId[DefinitionT],
                    PluginDefinitionConfig[DefinitionT],
                    PluginDefinitionConfig[DefinitionT],
                ],
                PluginDefinitionConfig[DefinitionT],
            ](
                value=item,  # ty: ignore[invalid-argument-type]
                label=plugin_type.definition.label_plural,
                manufacturer=lambda values: DictCatalog(
                    lambda item: item.id, values or ()
                ),
            ),
            label=label,
            description=description,
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
    )
