"""
Class variables that store data on their owners.
"""

from __future__ import annotations

from typing import final

from betty.classtools.class_var import ClassVar
from betty.operator import Attr


class StoreClassVar[OwnerT, StoreT](ClassVar[OwnerT]):
    """
    A class variable that stores data on its owners.
    """

    __store: Attr[OwnerT, StoreT]

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        super().__set_name__(owner, name)
        self.__store = Attr(f"_betty_class_var_store__{name}")

    @final
    @property
    def _store(self) -> Attr[OwnerT, StoreT]:
        """
        The store.
        """
        return self.__store
