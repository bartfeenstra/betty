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
    from collections.abc import Iterable


class HasProps:
    """
    An object that has :py:class:`properties <betty.prop.Prop>`.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        for prop in self.props():
            prop.init_owner(self)

    @final
    @classmethod
    @cache
    def props(cls) -> Iterable[Prop[Self, Any]]:
        """
        Get all properties on this class.
        """
        return tuple(
            member for _, member in getmembers(cls) if isinstance(member, Prop)
        )


@final
@dataclass(frozen=True)
class PropDefinition[OwnerT: HasProps]:
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


class Prop[OwnerT: HasProps, GetT](ABC):
    """
    A property.
    """

    __prop: PropDefinition[OwnerT]

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        self.__prop = PropDefinition(owner, name)

    @final
    @property
    def prop(self) -> PropDefinition[OwnerT]:
        """
        The property definition.
        """
        return self.__prop

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


class PropError(Exception):
    """
    Raised for property API errors.
    """

    def __init__(self, prop: Prop, message: str, *args: Any, **kwargs: Any):
        super().__init__(message, *args, **kwargs)
        self.prop: Final[Prop] = prop


class OwnerError(PropError, AttributeError):
    """
    Raised for property errors on a specific owner instance.
    """

    def __init__[OwnerT: HasProps](
        self, prop: Prop[OwnerT, Any], owner: OwnerT, message: str, /
    ):
        super().__init__(prop, message, name=prop.prop.name, obj=owner)


class ProxyProp[OwnerT: HasProps, GetT](Prop[OwnerT, GetT]):
    """
    A property that proxies another property.
    """

    def __init__(self, *args: Any, proxied: Prop[OwnerT, GetT], **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__proxied = proxied

    @override
    def __set_name__(self, owner: type[OwnerT], name: str):
        super().__set_name__(owner, name)
        self.__proxied.__set_name__(owner, name)

    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return self.__proxied.get(owner)

    @override
    def init_owner(self, owner: OwnerT, /) -> None:
        super().init_owner(owner)
        self.__proxied.init_owner(owner)


class SettableProp[OwnerT: HasProps, GetT, SetT](Prop[OwnerT, GetT]):
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

    def __init__[OwnerT: HasProps](
        self, prop: SettableProp[OwnerT, Any, Any], owner: OwnerT, /
    ):
        super().__init__(
            prop,
            owner,
            f"{fully_qualified_name(type(owner))}.{prop.prop.name} is not settable.",
        )
