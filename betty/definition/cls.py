"""
Class-based definitions.
"""

from typing import Any

from betty.importlib import fully_qualified_name


class ClsDefinition[ClsT = Any]:
    """
    A definition for a Python class.
    """

    def __init__(self, *args: Any, cls: type[ClsT] | None = None, **kwargs: Any):
        self._cls: type[ClsT] | None = None
        if cls is not None:
            self._set_cls(cls)

    @property
    def cls(self) -> type[ClsT]:
        """
        The class.

        :raises ValueError: Raised if the definition was not yet used to decorate a class.
        """
        if self._cls is None:
            raise ValueError("This definition does not yet have a class.")
        assert self._cls is not None
        return self._cls

    def __call__(self, cls: type[ClsT]) -> type[ClsT]:
        """
        Decorate a class and set it on this definition.

        :raises ValueError: Raised if the definition was already used to decorate a class.
        """
        self._set_cls(cls)
        return cls

    def _set_cls(self, cls: type[ClsT]) -> None:
        if self._cls is not None:
            raise ValueError(
                f"This definition already has a class: {fully_qualified_name(self._cls)}."
            )
        assert self._cls is None
        self._cls = cls
