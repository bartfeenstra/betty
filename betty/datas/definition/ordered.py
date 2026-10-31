"""
Ordered definition data.
"""

from __future__ import annotations

from operator import not_
from typing import TYPE_CHECKING, Any

from betty.attrs.owner import CollectionOwnerAttr
from betty.datas.aggregate.collection.list import ListDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.definition.id import IdentifiableDefinitionConfig
from betty.definition.id import resolve_id
from betty.definition.ordered import OrderedDefinition
from betty.localizables.gettext import _
from betty.machine_name import MachineName
from betty.porters.omit_field import OmitFieldPorter

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ty_extensions import Intersection

    from betty.definition.id import ResolvableId


class OrderedDefinitionConfig[
    DefinitionT: Intersection[
        OrderedDefinition, ObjectDefinition[OrderedDefinitionConfig]
    ]
](IdentifiableDefinitionConfig[DefinitionT]):
    """
    Configure a :py:class:`betty.definition.ordered.OrderedDefinition`.

    .. data:: betty.datas.definition.ordered:OrderedDefinitionConfig
    """

    after = CollectionOwnerAttr(
        FieldDefinition(
            ListDefinition(label=_("After"), value=MachineName),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
    )
    before = CollectionOwnerAttr(
        FieldDefinition(
            ListDefinition(label=_("Before"), value=MachineName),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
    )

    def __init__(
        self,
        after: Iterable[ResolvableId] = (),
        before: Iterable[ResolvableId] = (),
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.after = map(resolve_id, after)
        self.before = map(resolve_id, before)
