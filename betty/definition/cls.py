"""
Class-based definitions.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, final, override

from betty.definition import Definition, DefinitionClassVar, HasDefinition

if TYPE_CHECKING:
    from ty_extensions import Intersection


class _ClsDefinition[BaseClsT = Any](Definition, metaclass=ABCMeta):
    @abstractmethod
    def __call__[ClsT](
        self, cls: type[Intersection[ClsT, BaseClsT]]
    ) -> type[Intersection[ClsT]]:
        """
        Decorate a class and set it on this definition.
        """


class _ClsDefinitionBase[BaseClsT = Any](_ClsDefinition[BaseClsT]):
    def __init__(self, *args: Any, cls: type[BaseClsT] | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._cls: type[BaseClsT] | None = None
        if cls:
            self._set_cls(cls)

    @final
    @override
    def __call__[ClsT](
        self, cls: type[Intersection[ClsT, BaseClsT]]
    ) -> type[Intersection[ClsT]]:
        self._set_cls(cls)
        return cls

    def _set_cls(self, cls: type[BaseClsT], /) -> None:
        if self._cls is not None:
            raise ValueError(f"This definition already decorates {self._cls!r}.")
        if issubclass(cls, HasDefinition):
            if hasattr(cls, "definition"):
                raise ValueError(
                    f"{cls!r} has already been decorated with {cls.definition}."
                )
            cls.definition = DefinitionClassVar(self)
        self._cls = cls


class ClsDefinition[BaseClsT = Any](_ClsDefinition[BaseClsT]):
    """
    A definition with a Python class.
    """

    @property
    @abstractmethod
    def cls(self) -> type[BaseClsT]:
        """
        The class.

        :raises ValueError: Raised if the definition was not yet used to decorate a class.
        """


class ClsDefinitionBase[BaseClsT = Any](
    _ClsDefinitionBase[BaseClsT], ClsDefinition[BaseClsT]
):
    """
    A base class for :py:class:`betty.definition.cls.ClsDefinition`.
    """

    @final
    @override
    @property
    def cls(self) -> type[BaseClsT]:
        if self._cls is None:
            raise ValueError("This definition does not yet have a class.")
        return self._cls


class OptionalClsDefinition[BaseClsT = Any](_ClsDefinition[BaseClsT]):
    """
    A definition with an optional Python class.
    """

    @property
    @abstractmethod
    def cls(self) -> type[BaseClsT] | None:
        """
        The class.
        """


class OptionalClsDefinitionBase[BaseClsT = Any](
    _ClsDefinitionBase[BaseClsT], OptionalClsDefinition[BaseClsT]
):
    """
    A base class for :py:class:`betty.definition.cls.OptionalClsDefinition`.
    """

    @final
    @override
    @property
    def cls(self) -> type[BaseClsT] | None:
        return self._cls
