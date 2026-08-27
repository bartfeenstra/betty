"""
Tools to create classes.
"""

from __future__ import annotations

from abc import ABCMeta
from functools import cache
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Final, Self, final, override

from betty.importlib import fully_qualified_name

if TYPE_CHECKING:
    from collections.abc import Iterable


class Singleton:
    """
    A base class for singletons.
    """

    _instance: Self | None = None

    @final
    @override
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


@final
class ObjectNotYetInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.Object` was unexpectedly not yet initialized.
    """

    def __init__(self, object_: Object, /):
        super().__init__(f"{repr(object_)} was unexpectedly not yet initialized")


@final
class ObjectAlreadyInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.Object` was unexpectedly initialized already.
    """

    def __init__(self, object_: Object, /):
        super().__init__(f"{repr(object_)} was unexpectedly initialized already")


class Type(type):
    """
    The metaclass for :py:class:`betty.classtools.Object`.
    """

    def __call__(cls, *args: Any, **kwargs: Any):
        """
        Create a new instance.
        """
        new = cls.__new__(cls, *args, **kwargs)
        assert isinstance(new, Object)
        new._pre_init()
        new.__init__(*args, **kwargs)
        new._post_init()
        new._is_initialized = True
        return new


class Object(metaclass=Type):
    """
    An object that supports cooperative initialization.
    """

    _is_initialized = False

    def _pre_init(self) -> None:
        for class_var in self.init_class_vars():
            class_var.pre_init_owner(self)

    def _post_init(self) -> None:
        for class_var in self.init_class_vars():
            class_var.post_init_owner(self)

    @final
    @property
    def is_initialized(self) -> bool:
        """
        Whether the object is fully initialized.
        """
        return self._is_initialized

    @final
    def assert_initialized(self) -> None:
        """
        Assert that the object is initialized.
        """
        if not self.is_initialized:
            raise ObjectNotYetInitialized(self)

    @final
    def assert_not_initialized(self) -> None:
        """
        Assert that the object is not yet initialized.
        """
        if self.is_initialized:
            raise ObjectAlreadyInitialized(self)

    @final
    @classmethod
    @cache
    def init_class_vars(cls) -> Iterable[ObjectClassVar[Self]]:
        """
        Get all init class variables on this class.
        """
        return tuple(
            member
            for _, member in getmembers(cls)
            if isinstance(member, ObjectClassVar)
        )


class TypeABCMeta(Type, ABCMeta):
    """
    The metaclass for abstract :py:class:`betty.classtools.Object` subclasses.
    """


class ObjectClassVar[OwnerT: Object]:
    """
    A class variable on an :py:class:`betty.classtools.Object`.
    """

    def pre_init_owner(self, owner: OwnerT, /) -> None:
        """
        Pre-initialize the class variable on an owner.
        """
        return

    def post_init_owner(self, owner: OwnerT, /) -> None:
        """
        Pos-initialize the class variable on an owner.
        """
        return


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


class OwnedClassVar[OwnerT]:
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
