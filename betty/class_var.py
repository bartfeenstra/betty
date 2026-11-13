"""
The class variable API.
"""

from __future__ import annotations

from functools import cache
from inspect import getmembers
from typing import TYPE_CHECKING, Final, Self, final

from betty.importlib import fully_qualified_name

if TYPE_CHECKING:
    from collections.abc import Iterable


class ClassVar[OwnerT]:
    """
    A class variable on an object.
    """


class HasClassVars:
    """
    An object that has :py:class:`class variables <betty.class_var.ClassVar>`.
    """

    @final
    @classmethod
    @cache
    def class_vars(cls) -> Iterable[ClassVar[Self]]:
        """
        Get all class variables on this class.
        """
        return tuple(
            member for _, member in getmembers(cls) if isinstance(member, ClassVar)
        )


@final
class ClassVarOwnership[OwnerT, ClassVarT]:
    """
    The ownership of a class var on an owner class.
    """

    def __init__(self, owner: type[OwnerT], name: str, var: ClassVarT, /):
        self.var: Final[ClassVarT] = var
        self.owner: Final[type[OwnerT]] = owner
        self.name: Final[str] = name
        """
        The name of the attribute on the owner the class var is assigned to.
        """
        self.fully_qualified_name: Final[str] = f"{fully_qualified_name(owner)}.{name}"
        """
        The fully qualified class var name.
        """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {fully_qualified_name(type(self.var))} @ {self.fully_qualified_name}>"


class OwnedClassVar[OwnerT](ClassVar):
    """
    A class var with access to its owner.
    """

    __ownership: ClassVarOwnership[OwnerT, Self]

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        self.__ownership = ClassVarOwnership(owner, name, self)

    @final
    @property
    def ownership(self) -> ClassVarOwnership[OwnerT, Self]:
        """
        The class var ownership.
        """
        return self.__ownership
