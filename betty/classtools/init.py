"""
Tools to cooperatively initialize objects.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Literal, final

from betty.classtools.class_var import ClassVar, HasClassVars
from betty.operator import Attr


@final
class NotYetInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.init.Init` was unexpectedly not yet initialized.
    """

    def __init__(self, object_: Init, /):
        super().__init__(f"{object_!r} was unexpectedly not yet initialized")


@final
class AlreadyInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.init.Init` was unexpectedly initialized already.
    """

    def __init__(self, object_: Init, /):
        super().__init__(f"{object_!r} was unexpectedly initialized already")


@final
class _IsInitialized:
    _storage = Attr("_betty_classtools_init_init")

    def __get__(
        self, instance: Init, owner: type[Init] | None = None, /
    ) -> bool | None:
        return self._storage.get(instance, False)

    def __set__(self, instance: Init, value: Literal[True] | None) -> None:
        instance.assert_not_initialized()
        self._storage.set(instance, value)


class Init(HasClassVars):
    """
    An object that supports cooperative initialization.

    Subclasses MUST set :py:attr:`betty.classtools.init.Init.is_initialized` themselves, and may use
    :py:func:`betty.classtools.init.init` or :py:class:`betty.classtools.init.InitMeta` to achieve that.
    """

    is_initialized = _IsInitialized()
    """
    Whether the object is fully initialized.
    """

    def pre_init(self) -> None:
        """
        Pre-initialize the object.
        """
        for class_var in self.class_vars():
            if isinstance(class_var, InitClassVar):
                class_var.pre_init_owner(self)

    def post_init(self) -> None:
        """
        Post-initialize the object.
        """
        for class_var in self.class_vars():
            if isinstance(class_var, InitClassVar):
                class_var.post_init_owner(self)

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


class InitClassVar[OwnerT: Init](ClassVar):
    """
    A class variable on an :py:class:`betty.classtools.init.Init`.
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


# @todo Can we use Init.__init_subclass__() to decorate the subclass's __init__() instead?
# @todo
# @todo
# @todo
def init[T: Init](cls: type[T]) -> type[T]:
    """
    Make a class cooperatively initializable.

    Subclasses will have to reapply this decorator.
    """
    original_init = cls.__init__
    if not getattr(original_init, "_betty_classtools_init", False):

        @wraps(original_init)
        def _init(self: T, *args: Any, **kwargs: Any) -> None:
            is_initializing_already = self.is_initialized is None
            if not is_initializing_already:
                self.is_initialized = None
                self.pre_init()
            print("::: INIT")
            print(type(self))
            print(original_init)
            print(self.__init__)
            print(args)
            print(kwargs)
            original_init(self, *args, **kwargs)
            if not is_initializing_already:
                self.post_init()
                self.is_initialized = True

        _init._betty_classtools_init = True  # ty: ignore[unresolved-attribute]
        cls.__init__ = _init  # ty: ignore[invalid-assignment]
    return cls


class InitMeta(type):
    """
    A metaclass to force all subclasses to be cooperatively initializable.
    """

    def __new__(
        cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any], /
    ) -> type:
        """
        Create a new class.
        """
        new = super().__new__(cls, name, bases, namespace)
        assert issubclass(new, Init)
        return init(new)
