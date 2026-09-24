"""
Definitions with IDs.
"""

from __future__ import annotations

from typing import Any, Final

from betty.definition import Definition, ResolvableDefinition, resolve_definition
from betty.machine_name import MachineName, ResolvableMachineName


class IdentifiableDefinition(Definition):
    """
    A definition with a unique ID.
    """

    def __init__(
        self,
        *args: Any,
        id: ResolvableMachineName,  # noqa: A002
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.id: Final[MachineName] = MachineName.resolve(id)
        """
        The ID.
        """


type ResolvableId[DefinitionT: IdentifiableDefinition = IdentifiableDefinition] = (
    ResolvableMachineName | ResolvableDefinition[DefinitionT]
)


def resolve_id(id_: ResolvableId, /) -> MachineName:
    """
    Resolve a value to its definition ID.

    :raises ValueError: Raised if the value cannot be resolved to its definition ID.
    """
    if isinstance(id_, str):
        return MachineName.resolve(id_)
    return resolve_definition(id_).id
