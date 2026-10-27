"""
Reusable definition data.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Self

from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.definition import Definition
from betty.porters.fields import FieldsPorter

if TYPE_CHECKING:
    from betty.data import ResolvableDataPorter


class DefinitionConfigDefinition[DefinitionT: Definition](
    ObjectDefinition[Object[DefinitionT]]
):
    """
    Define definition configuration.
    """

    def __init__(
        self,
        *args: Any,
        porter: ResolvableDataPorter[Self, Object[DefinitionT]] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, porter=porter or FieldsPorter, **kwargs)


class DefinitionConfig[DefinitionT: Definition](
    Object[DefinitionConfigDefinition[DefinitionT]]
):
    """
    Configure a :py:class:`betty.definition.Definition`.
    """

    @abstractmethod
    def new_definition(self) -> DefinitionT:
        """
        Create a new definition from this configuration.
        """
