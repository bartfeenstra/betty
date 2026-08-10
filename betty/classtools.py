"""
Tools to create classes.
"""

from __future__ import annotations

from abc import ABCMeta
from functools import cache
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Self, final, override

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
class NotYetInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.Init` was unexpectedly not yet initialized.
    """

    def __init__(self, init: Init, /):
        super().__init__(f"{repr(init)} was unexpectedly not yet initialized")


@final
class AlreadyInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.Init` was unexpectedly initialized already.
    """

    def __init__(self, init: Init, /):
        super().__init__(f"{repr(init)} was unexpectedly initialized already")


class InitMeta(type):
    """
    The metaclass for :py:class:`betty.classtools.Init`.
    """

    def __call__(cls, *args: Any, **kwargs: Any):
        """
        Create a new instance.
        """
        new = cls.__new__(cls, *args, **kwargs)
        assert isinstance(new, Init)
        new._pre_init()
        new.__init__(*args, **kwargs)
        new._post_init()
        new._is_initialized = True
        return new


class Init(metaclass=InitMeta):
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
            raise NotYetInitialized(self)

    @final
    def assert_not_initialized(self) -> None:
        """
        Assert that the object is not yet initialized.
        """
        if self.is_initialized:
            raise AlreadyInitialized(self)

    @final
    @classmethod
    @cache
    def init_class_vars(cls) -> Iterable[InitClassVar[Self]]:
        """
        Get all init class variables on this class.
        """
        return tuple(
            member for _, member in getmembers(cls) if isinstance(member, InitClassVar)
        )


class InitABCMeta(InitMeta, ABCMeta):
    """
    The metaclass for abstract :py:class:`betty.classtools.Init` subclasses.
    """


class InitClassVar[OwnerT: Init]:
    """
    A class variable on an :py:class:`betty.classtools.Init`.
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
