"""
Attributes with default values.
"""

from __future__ import annotations

from inspect import signature
from typing import TYPE_CHECKING, final, override

from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.prop import HasProps

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.attr import Attr


class DefaultAttr[
    OwnerT: HasProps,
    GetT,
    SetT,
    DataDefinitionT: DataDefinition = DataDefinition,
](ProxyAttr[OwnerT, GetT, SetT, DataDefinitionT]):
    """
    An attribute with a default value.
    """

    def __init__(
        self,
        proxied: Attr[OwnerT, GetT, SetT, DataDefinitionT],
        default: Callable[[], SetT] | Callable[[OwnerT], SetT],
        /,
    ):

        super().__init__(
            FieldDefinition(
                proxied.field.data,
                label=proxied.field.label,
                description=proxied.field.description,
                omit_load=True,
                omit_dump=self.__omit_dump,
            ),
            proxied=proxied,
        )
        self.__default: Callable[[OwnerT], SetT] = (
            default if len(signature(default).parameters) == 1 else lambda _: default()  # ty:ignore[invalid-assignment, missing-argument]
        )

    def __omit_dump(self, owner: OwnerT, data: GetT) -> bool:
        if data == self.normalize(owner, self.__default(owner)):
            return True
        return self._proxied_field.omit_dump(owner, data)

    @final
    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self.set(owner, self.__default(owner))
