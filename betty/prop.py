"""
The property API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cache
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Final, Never, Self, final, overload

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

    prop: Prop[OwnerT, Any, Any]
    owner: type[OwnerT]
    name: str
    """
    The name of the attribute on the owner the property is assigned to.
    """

    fully_qualified_name: str = field(init=False)
    """
    The fully qualified property name.
    """

    _owner_attr_name: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self,
            "fully_qualified_name",
            f"{fully_qualified_name(self.owner)}.{self.name}",
        )
        object.__setattr__(self, "_owner_attr_name", f"_betty_prop__{self.name}")

    def hasattr(self, owner: OwnerT, /) -> bool:
        """
        Check if a property value is stored on the owner.
        """
        return hasattr(owner, self._owner_attr_name)

    def getattr(self, owner: OwnerT, /) -> Any:
        """
        Get the property value from the owner, if any.
        """
        return getattr(owner, self._owner_attr_name)

    def setattr(self, owner: OwnerT, value: Any, /) -> None:
        """
        Set the property value on the owner.
        """
        setattr(owner, self._owner_attr_name, value)

    def setattrdefault(self, owner: OwnerT, value: Any, /) -> None:
        """
        Set the property value on the owner, if no value is stored yet.
        """
        if not self.hasattr(owner):
            setattr(owner, self._owner_attr_name, value)

    def delattr(self, owner: OwnerT, /) -> None:
        """
        Delete the property value from the owner, if any.
        """
        delattr(owner, self._owner_attr_name)


class Prop[OwnerT: HasProps, GetT, SetT: Any = Never](ABC):
    """
    A property.
    """

    __prop: PropDefinition[OwnerT]

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        self.__prop = PropDefinition(self, owner, name)

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

    def delete_owner(self, owner: OwnerT, /) -> None:
        """
        Delete the property from an owner.
        """
        return

    @abstractmethod
    def get(self, owner: OwnerT, /) -> GetT:
        """
        Get the property value from the owner.
        """

    def set(self, owner: OwnerT, value: SetT, /) -> None:
        """
        Set the property value on the owner.

        :raises NotSettable:
        """
        raise NotSettable(self, owner)

    def delete(self, owner: OwnerT, /) -> None:
        """
        Delete the property value from the owner.

        :raises NotDeletable:
        """
        raise NotDeletable(self, owner)

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

    @final
    def __set__(self, instance: OwnerT, value: SetT) -> None:
        self.set(instance, value)

    @final
    def __delete__(self, instance: OwnerT) -> None:
        self.delete(instance)


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


class NotSettable(OwnerError):
    """
    Raised when a property is not settable.
    """

    def __init__[OwnerT: HasProps](self, prop: Prop[OwnerT, Any], owner: OwnerT, /):
        super().__init__(
            prop,
            owner,
            f"{fully_qualified_name(type(owner))}.{prop.prop.name} is not settable on {owner}.",
        )


class NotDeletable(OwnerError):
    """
    Raised when a property is not deletable.
    """

    def __init__[OwnerT: HasProps](self, prop: Prop[OwnerT, Any], owner: OwnerT, /):
        super().__init__(
            prop,
            owner,
            f"{fully_qualified_name(type(owner))}.{prop.prop.name} is not deletable from {owner}.",
        )
