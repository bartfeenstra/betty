"""
Attributes with default values.
"""

from __future__ import annotations

from inspect import signature
from typing import TYPE_CHECKING, final, override

from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.porters.omit_field import OmitFieldPorter
from betty.prop import HasProps

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.attr import Attr
    from betty.typing import Intersection


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
        proxied: Attr[
            OwnerT, GetT, SetT, Intersection[DataDefinitionT, DataDefinition[GetT]]
        ],
        default: Callable[[], SetT] | Callable[[OwnerT], SetT],
        /,
    ):
        super().__init__(
            FieldDefinition(
                proxied.field.data,
                label=proxied.field.label,
                description=proxied.field.description,
                optional=True,
                porter=OmitFieldPorter[OwnerT, GetT].new(
                    lambda owner, field, data: (
                        data == self.normalize(owner, self.__default(owner))
                    )
                ),
            ),
            proxied=proxied,
        )
        self.__default: Callable[[OwnerT], SetT] = (
            default if len(signature(default).parameters) == 1 else lambda _: default()  # ty:ignore[invalid-assignment, missing-argument]
        )

    @final
    @override
    def _pre_init_owner(self, owner: OwnerT, /) -> None:
        super()._pre_init_owner(owner)
        self.set(owner, self.__default(owner))
