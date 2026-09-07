"""
Class-based definitions.
"""

from __future__ import annotations

from typing import Any, final

from betty.importlib import fully_qualified_name


class _ClsDefinition[BaseClsT = Any]:
    def __init__(self, *args: Any, cls: type[BaseClsT] | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._cls: type[BaseClsT] | None = None
        if cls is not None:
            self._set_cls(cls)

    @final
    def __call__[ClsT](self, cls: type[ClsT]) -> type[ClsT]:
        """
        Decorate a class and set it on this definition.

        :raises ValueError: Raised if the definition was already used to decorate a class.
        """
        self._set_cls(cls)
        return cls

    def _set_cls(self, cls: type[BaseClsT], /) -> None:
        if self._cls is not None:
            raise ValueError(
                f"This definition already has a class: {fully_qualified_name(self._cls)}."
            )
        self._cls = cls


class ClsDefinition[BaseClsT = Any](_ClsDefinition[BaseClsT]):
    """
    A definition with a Python class.
    """

    @final
    @property
    def cls(self) -> type[BaseClsT]:
        """
        The class.

        :raises ValueError: Raised if the definition was not yet used to decorate a class.
        """
        if self._cls is None:
            raise ValueError("This definition does not yet have a class.")
        return self._cls


class OptionalClsDefinition[BaseClsT = Any](_ClsDefinition[BaseClsT]):
    """
    A definition with an optional Python class.
    """

    @final
    @property
    def cls(self) -> type[BaseClsT] | None:
        """
        The class.
        """
        return self._cls
