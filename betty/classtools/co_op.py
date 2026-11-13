"""
Tools to cooperatively create classes and objects.
"""

from __future__ import annotations

from abc import ABCMeta
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal, Self, final

from betty.classtools.class_var import ClassVar, HasClassVars
from betty.operator import Attr

if TYPE_CHECKING:
    from collections.abc import Iterable


@final
class NotYetInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.co_op.CoOp` was unexpectedly not yet initialized.
    """

    def __init__(self, object_: CoOp, /):
        super().__init__(f"{object_!r} was unexpectedly not yet initialized")


@final
class AlreadyInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.co_op.CoOp` was unexpectedly initialized already.
    """

    def __init__(self, object_: CoOp, /):
        super().__init__(f"{object_!r} was unexpectedly initialized already")


@final
class _IsInitialized:
    _storage = Attr("_betty_classtools_co_op_init")

    def __get__(
        self, instance: CoOp, owner: type[CoOp] | None = None, /
    ) -> bool | None:
        return self._storage.get(instance, False)

    def __set__(self, instance: CoOp, value: Literal[True] | None) -> None:
        instance.assert_not_initialized()
        self._storage.set(instance, value)


class CoOp(HasClassVars):
    """
    An object that supports cooperative initialization.
    """

    is_initialized = _IsInitialized()
    """
    Whether the object is fully initialized.
    """

    @final
    @classmethod
    def init_class_vars(cls) -> Iterable[CoOpClassVar[Self]]:
        """
        Get all init class variables on this class.
        """
        for class_var in cls.class_vars():
            if isinstance(class_var, CoOpClassVar):
                yield class_var

    def _pre_init(self) -> None:
        for class_var in self.init_class_vars():
            class_var.pre_init_owner(self)

    def _post_init(self) -> None:
        for class_var in self.init_class_vars():
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


class CoOpClassVar[OwnerT: CoOp](ClassVar):
    """
    A class variable on an :py:class:`betty.classtools.co_op.CoOp`.
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


def co_op[T: CoOp](cls: type[T]) -> type[T]:
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
                self._pre_init()
            original_init(self, *args, **kwargs)
            if not is_initializing_already:
                self._post_init()
                self.is_initialized = True

        _init._betty_classtools_init = True  # ty: ignore[unresolved-attribute]
        cls.__init__ = _init  # ty: ignore[invalid-assignment]
    return cls


class CoOpMeta(type):
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
        assert issubclass(new, CoOp)
        return co_op(new)


class CoOpABCMeta(CoOpMeta, ABCMeta):
    """
    The metaclass for abstract :py:class:`betty.classtools.co_op.CoOp` subclasses.
    """
