"""
The class variable API.
"""

from __future__ import annotations

from inspect import getmembers
from typing import Any, Final, Self, final

from betty.importlib import fully_qualified_name


class ClassVar[OwnerT]:
    """
    A class variable on an object.
    """


@final
class ClassVars[ClassVarT: ClassVar]:
    """
    Expose a class's class variables.
    """

    __slots__ = ("_vars",)

    def __init__(self, cls: type, class_var_cls: type[ClassVarT], /):
        self._vars = tuple(
            member for _, member in getmembers(cls) if isinstance(member, class_var_cls)
        )

    def __get__(self, instance: Any, owner: Any) -> tuple[ClassVarT, ...]:
        return self._vars


class HasClassVars:
    """
    An object that has :py:class:`class variables <betty.classtools.class_var.ClassVar>`.
    """

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.class_vars = ClassVars(cls, ClassVar)


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
