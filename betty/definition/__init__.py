"""
The definition API.
"""

from __future__ import annotations

from typing import ClassVar, final

from typing_extensions import disjoint_base


@disjoint_base
class Definition:
    """
    A definition.
    """


@final
class DefinitionClassVar[DefinitionT: Definition]:
    """
    A class var that exposes its owner's definition.
    """

    __slots__ = ("_definition",)

    def __init__(self, definition: DefinitionT, /):
        self._definition = definition

    def __get__(
        self,
        instance: HasDefinition[DefinitionT] | None,
        owner: type[HasDefinition[DefinitionT]],
        /,
    ) -> DefinitionT:
        return self._definition


class HasDefinition[DefinitionT: Definition = Definition]:
    """
    A class that exposes its definition.
    """

    __slots__ = ()

    definition: ClassVar[DefinitionClassVar]


type ResolvableDefinition[DefinitionT: Definition = Definition] = (
    DefinitionT | type[HasDefinition[DefinitionT]]
)


def resolve_definition[DefinitionT: Definition](
    definition: ResolvableDefinition[DefinitionT], /
) -> DefinitionT:
    """
    Resolve a value to its definition.

    :raises ValueError: Raised if the value cannot be resolved to its definition.
    """
    if isinstance(definition, Definition):
        return definition
    if isinstance(definition, type) and issubclass(definition, HasDefinition):
        return definition.definition
    raise ValueError(f"{definition!r} cannot be resolved to its plugin definition.")
