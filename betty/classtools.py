"""
Tools to create classes.
"""

from __future__ import annotations

from abc import ABCMeta
from typing import TYPE_CHECKING, Any, Self, cast, final

from betty.class_var import ClassVar, HasClassVars

if TYPE_CHECKING:
    from collections.abc import Iterable


@final
class ObjectNotYetInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.Object` was unexpectedly not yet initialized.
    """

    def __init__(self, object_: Object, /):
        super().__init__(f"{object_!r} was unexpectedly not yet initialized")


@final
class ObjectAlreadyInitialized(RuntimeError):
    """
    An :py:class:`betty.classtools.Object` was unexpectedly initialized already.
    """

    def __init__(self, object_: Object, /):
        super().__init__(f"{object_!r} was unexpectedly initialized already")


class Type(type):
    """
    The metaclass for :py:class:`betty.classtools.Object`.
    """

    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        *,
        slots: bool = False,
    ) -> type:
        """
        Create a new class.
        """
        new = cast("type[Object]", super().__new__(cls, name, bases, namespace))
        if slots:
            new_slots = tuple(new._slots())
            if hasattr(new, "__slots__"):
                if isinstance(new.__slots__, str):
                    new_slots += (new.__slots__,)
                else:
                    new_slots += cast(tuple[str, ...], new.__slots__)
            new.__slots__ = new_slots  # ty: ignore[unresolved-attribute]
        return new

    def __call__(cls, *args: Any, **kwargs: Any):
        """
        Create a new instance.
        """
        new = cls.__new__(cls, *args, **kwargs)  # ty: ignore[invalid-argument-type]
        assert isinstance(new, Object)
        new._pre_init()
        new.__init__(*args, **kwargs)
        new._post_init()
        new._is_initialized = True
        return new


class Object(HasClassVars, metaclass=Type):
    """
    An object that supports cooperative initialization.
    """

    # @todo Refactor into a slottable class var?
    _is_initialized = False

    @final
    @classmethod
    def object_class_vars(cls) -> Iterable[ObjectClassVar[Self]]:
        """
        Get all object class variables on this class.
        """
        for class_var in cls.class_vars():
            if isinstance(class_var, ObjectClassVar):
                yield class_var

    @classmethod
    def _slots(cls) -> Iterable[str]:
        for class_var in cls.object_class_vars():
            yield from class_var.slots()

    def _pre_init(self) -> None:
        for class_var in self.object_class_vars():
            class_var.pre_init_owner(self)

    def _post_init(self) -> None:
        for class_var in self.object_class_vars():
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


class TypeABCMeta(Type, ABCMeta):
    """
    The metaclass for abstract :py:class:`betty.classtools.Object` subclasses.
    """


class ObjectClassVar[OwnerT: Object](ClassVar):
    """
    A class variable on an :py:class:`betty.classtools.Object`.
    """

    def slots(self) -> Iterable[str]:
        """
        Declare the slots this class variable needs to be present on the owner.
        """
        return ()

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
