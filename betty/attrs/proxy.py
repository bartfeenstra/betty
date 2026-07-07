"""
Proxy properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attr import Attr
from betty.data import DataDefinition
from betty.prop import HasProps
from betty.props.proxy import ProxyProp

if TYPE_CHECKING:
    from betty.datas.aggregate.record import ResolvableFieldDefinition


class ProxyAttr[OwnerT: HasProps, GetT, SetT, DataDefinitionT: DataDefinition](
    ProxyProp[OwnerT, GetT, SetT], Attr[OwnerT, GetT, SetT, DataDefinitionT]
):
    """
    An attribute that proxies another attribute.
    """

    def __init__(
        self,
        field: ResolvableFieldDefinition[OwnerT, GetT, DataDefinitionT] | None = None,
        *args: Any,
        proxied: Attr[OwnerT, GetT, SetT, DataDefinitionT],
        **kwargs: Any,
    ):
        super().__init__(
            proxied.field if field is None else field, *args, proxied=proxied, **kwargs
        )
        self._proxied_field = proxied.field
