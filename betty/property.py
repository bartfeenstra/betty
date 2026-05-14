"""
The property API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Self, final, overload

if TYPE_CHECKING:
    from collections.abc import Sequence


class HasProperties:
    """
    An object that has :py:class:`properties <betty.property.Property>`.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        for property in self.__get_properties():  # noqa: A001
            property.init_property_owner(self)

    @classmethod
    @cache
    def __get_properties(cls) -> Sequence[Property[Self, Any]]:
        return tuple(
            member for _, member in getmembers(cls) if isinstance(member, Property)
        )


@final
@dataclass(frozen=True)
class PropertyDefinition[OwnerT: HasProperties]:
    """
    The definition of a property on a class.
    """

    owner: type[OwnerT]
    name: str

    @property
    def id(self) -> str:
        """
        The global property ID.
        """
        return f"{self.owner.__name__}.{self.name}"


class Property[OwnerT: HasProperties, GetT](ABC):
    """
    A property.
    """

    __property: PropertyDefinition[OwnerT]

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        self.__property = PropertyDefinition(owner, name)

    @final
    @property
    def property(self) -> PropertyDefinition[OwnerT]:
        """
        The property definition.
        """
        return self.__property

    def init_property_owner(self, owner: OwnerT, /) -> None:  # noqa: B027
        """
        Initialize the property on an owner.
        """

    @overload
    def __get__(self, instance: None, owner: type[OwnerT], /) -> Self:
        pass

    @overload
    def __get__(self, instance: OwnerT, owner: type[OwnerT] | None = None, /) -> GetT:
        pass

    @final
    def __get__(self, instance, owner=None, /):
        if instance is None:
            return self
        return self.get(instance)

    @abstractmethod
    def get(self, owner: OwnerT, /) -> GetT:
        """
        Get the property value from the owner.
        """
