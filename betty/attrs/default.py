"""
Attributes with default values.
"""

from collections.abc import Callable
from inspect import signature
from typing import final, override

from betty.attr import ProxyAttr
from betty.attrs.owner import OwnerAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.prop import HasProps


@final
class DefaultAttr[OwnerT: HasProps, GetT, SetT](
    ProxyAttr[OwnerT, GetT, SetT], OwnerAttr[OwnerT, GetT, SetT]
):
    """
    An attribute with a default value.
    """

    def __init__(
        self,
        proxied: OwnerAttr[OwnerT, GetT, SetT],
        default: Callable[[], SetT] | Callable[[OwnerT], SetT],
        /,
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
        self._default: Callable[[OwnerT], SetT] = (
            default if len(signature(default).parameters) == 1 else lambda _: default()  # ty:ignore[invalid-assignment, missing-argument]
        )

    def _omit_dump(self, owner: OwnerT, data: GetT) -> bool:
        if data == self._default(owner):
            return True
        return self._proxied.field.omit_dump(owner, data)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self.set(owner, self._default(owner))
