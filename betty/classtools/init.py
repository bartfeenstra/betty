"""
Tools to cooperatively initialize objects.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Literal, final, override

from betty.classtools.class_var import ClassVar, ClassVars, HasClassVars
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
    _storage = Attr("_betty_classtools_init")

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
    """

    is_initialized = _IsInitialized()
    """
    Whether the object is fully initialized.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.init_class_vars = ClassVars(cls, InitClassVar)
        original_init = cls.__init__
        for base in cls.__bases__:
            if original_init is base.__init__:
                original_init = None
                break

        def _init[InitT: Init](
            init_self: InitT, *init_args: Any, **init_kwargs: Any
        ) -> None:
            is_initializing_already = init_self.is_initialized is None
            if is_initializing_already is False:
                init_self.is_initialized = None
                init_self.pre_init()
            if original_init is None:
                super(cls, init_self).__init__(*init_args, **init_kwargs)
            else:
                original_init(init_self, *init_args, **init_kwargs)
            if not is_initializing_already:
                init_self.post_init()
                init_self.is_initialized = True

        if original_init is None:
            _init = override(_init)
        else:
            _init = wraps(original_init)(_init)  # ty: ignore[invalid-assignment]

        cls.__init__ = _init

    def pre_init(self) -> None:
        """
        Pre-initialize the object.
        """
        for class_var in self.init_class_vars:
            class_var.pre_init_owner(self)

    def post_init(self) -> None:
        """
        Post-initialize the object.
        """
        for class_var in self.init_class_vars:
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
