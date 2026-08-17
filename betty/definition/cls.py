"""
Class-based definitions.
"""

from __future__ import annotations

from typing import Any, final

from betty.capability import Stage
from betty.definition import Definition
from betty.importlib import fully_qualified_name


@final
class OnSetCls(Stage):
    """
    The capability manufacturer stage for when a class is set on a definition.
    """


type ClsDefinitionCapabilityStage = OnSetCls


class _ClsDefinition[BaseClsT = Any, StageT: Stage = ClsDefinitionCapabilityStage](
    Definition[StageT | ClsDefinitionCapabilityStage]
):
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
        self._init_staged_capabilities(OnSetCls)


class ClsDefinition[BaseClsT = Any, StageT: Stage = ClsDefinitionCapabilityStage](
    _ClsDefinition[BaseClsT, StageT]
):
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


class OptionalClsDefinition[
    BaseClsT = Any,
    StageT: Stage = ClsDefinitionCapabilityStage,
](_ClsDefinition[BaseClsT, StageT]):
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
