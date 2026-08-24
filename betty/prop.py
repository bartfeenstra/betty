"""
The property API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Final, Never, Self, final, overload

from betty.classtools import Object, ObjectClassVar
from betty.importlib import fully_qualified_name
from betty.objecttools import AttrOperators

if TYPE_CHECKING:
    from collections.abc import Iterable


class HasProps(Object):
    """
    An object that has :py:class:`properties <betty.prop.Prop>`.
    """

    @final
    @classmethod
    def props(cls) -> Iterable[Prop[Self, Any]]:
        """
        Get all properties on this class.
        """
        for class_var in cls.init_class_vars():
            if isinstance(class_var, Prop):
                yield class_var


@final
class PropOwnership[OwnerT: HasProps]:
    """
    The ownership of a property on a class.
    """

    def __init__(self, prop: Prop[OwnerT, Any, Any], owner: type[OwnerT], name: str):
        self.prop: Final[Prop[OwnerT, Any, Any]] = prop
        self.owner: Final[type[OwnerT]] = owner
        self.name: Final[str] = name
        """
        The name of the attribute on the owner the property is assigned to.
        """
        self.fully_qualified_name: Final[str] = f"{fully_qualified_name(owner)}.{name}"
        """
        The fully qualified property name.
        """
        self.storage: Final[AttrOperators] = AttrOperators(f"_betty_prop__{name}")


class Prop[OwnerT: HasProps, GetT, SetT: Any = Never](
    ObjectClassVar[OwnerT], metaclass=ABCMeta
):
    """
    A property.
    """

    __ownership: PropOwnership[OwnerT]

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        self.__ownership = PropOwnership(self, owner, name)

    @final
    @property
    def ownership(self) -> PropOwnership[OwnerT]:
        """
        The property ownership.
        """
        return self.__ownership

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

    @final
    def assert_settable(self, owner: OwnerT, /) -> None:
        """
        Assert that the property is settable for the given owner.

        :raises NotSettable:
        """
        if not self.is_settable(owner):
            raise NotSettable(self, owner)

    def is_settable(self, owner: OwnerT, /) -> bool:
        """
        Check if the property is settable for the given owner.
        """
        return False

    def set(self, owner: OwnerT, value: SetT, /) -> None:
        """
        Set the property value on the owner.

        :raises NotSettable:
        """
        self.assert_settable(owner)

    @final
    def assert_deletable(self, owner: OwnerT, /) -> None:
        """
        Assert that the property is deletable for the given owner.

        :raises NotDeletable:
        """
        if not self.is_deletable(owner):
            raise NotDeletable(self, owner)

    def is_deletable(self, owner: OwnerT, /) -> bool:
        """
        Check if the property is deletable for the given owner.
        """
        return False

    def delete(self, owner: OwnerT, /) -> None:
        """
        Delete the property value from the owner.

        :raises NotDeletable:
        """
        self.assert_deletable(owner)

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
        super().__init__(prop, message, name=prop.ownership.name, obj=owner)


class NotSettable(OwnerError):
    """
    Raised when a property is not settable.
    """

    def __init__[OwnerT: HasProps](self, prop: Prop[OwnerT, Any], owner: OwnerT, /):
        super().__init__(
            prop,
            owner,
            f"{fully_qualified_name(type(owner))}.{prop.ownership.name} is not settable on {repr(owner)}.",
        )


class NotDeletable(OwnerError):
    """
    Raised when a property is not deletable.
    """

    def __init__[OwnerT: HasProps](self, prop: Prop[OwnerT, Any], owner: OwnerT, /):
        super().__init__(
            prop,
            owner,
            f"{fully_qualified_name(type(owner))}.{prop.ownership.name} is not deletable from {repr(owner)}.",
        )
