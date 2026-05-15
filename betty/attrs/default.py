"""
Attributes with default values.
"""

from collections.abc import Callable
from typing import final, override

from betty.attrs.owner import OwnerAttr, ProxyOwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.property import HasProperties


@final
class DefaultAttr[OwnerT: HasProperties, GetT, SetT](
    ProxyOwnerAttr[OwnerT, GetT, SetT]
):
    """
    An attribute with a default value.
    """

    def __init__(
        self, proxied: OwnerAttr[OwnerT, GetT, SetT], default: Callable[[], SetT], /
    ):

        super().__init__(
            proxied,
            field=FieldDefinition(
                proxied.field.data,
                label=proxied.field.label,
                description=proxied.field.description,
                omit_load=True,
                omit_dump=self._omit_dump,
            ),
        )
        self._proxied = proxied
        self._default = default

    def _omit_dump(self, data: GetT) -> bool:
        if data == self._default():
            return True
        return self._proxied.field.omit_dump(data)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self.set(owner, self._default())
