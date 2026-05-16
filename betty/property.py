"""
The property API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Final, Self, final, overload, override

from betty.importlib import fully_qualified_name

if TYPE_CHECKING:
    from collections.abc import Sequence


class HasProperties:
    """
    An object that has :py:class:`properties <betty.property.Property>`.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        for property in self.__get_properties():  # noqa: A001
            property.init_owner(self)

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

    def init_owner(self, owner: OwnerT, /) -> None:
        """
        Initialize the property on an owner.
        """
        return

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


class PropertyError(Exception):
    """
    Raised for property API errors.
    """

    def __init__(self, _property: Property, message: str, *args: Any, **kwargs: Any):
        super().__init__(message, *args, **kwargs)
        self.property: Final[Property] = _property


class OwnerError(PropertyError, AttributeError):
    """
    Raised for property errors on a specific owner instance.
    """

    def __init__[OwnerT: HasProperties](
        self, _property: Property[OwnerT, Any], owner: OwnerT, message: str, /
    ):
        super().__init__(_property, message, name=_property.property.name, obj=owner)


class ProxyProperty[OwnerT: HasProperties, GetT](Property[OwnerT, GetT]):
    """
    A property that proxies another property.
    """

    def __init__(self, *args: Any, proxied: Property[OwnerT, GetT], **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__proxied_property = proxied

    @override
    def __set_name__(self, owner: type[OwnerT], name: str):
        super().__set_name__(owner, name)
        self.__proxied_property.__set_name__(owner, name)

    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return self.__proxied_property.get(owner)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self.__proxied_property.init_owner(owner)


class SettableProperty[OwnerT: HasProperties, GetT, SetT](Property[OwnerT, GetT]):
    """
    A property whose value can be set.
    """

    def set(self, owner: OwnerT, value: SetT, /) -> None:
        """
        Set the value on the owner.

        :raises NotSettable:
        """
        raise NotSettable(self, owner)

    @final
    def __set__(self, instance: OwnerT, value: SetT | GetT) -> None:
        self.set(instance, value)


class NotSettable(OwnerError):
    """
    Raised when a property is not settable.
    """

    def __init__[OwnerT: HasProperties](
        self, _property: SettableProperty[OwnerT, Any, Any], owner: OwnerT, /
    ):
        super().__init__(
            _property,
            owner,
            f"{fully_qualified_name(type(owner))}.{_property.property.name} is not settable.",
        )
