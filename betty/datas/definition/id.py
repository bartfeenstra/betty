"""
Reusable data for plugin definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from betty.attrs.machine_name import new_machine_name_attr
from betty.datas.definition import DefinitionConfig, DefinitionConfigDefinition
from betty.definition.id import IdentifiableDefinition
from betty.localizables.gettext import _
from betty.porters.fields import FieldsPorter
from betty.porters.keyed_mapping import KeyedMappingPorter

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.data import ResolvableDataPorter
    from betty.datas.aggregate.record.object import Object, ObjectDefinition
    from betty.machine_name import ResolvableMachineName


class IdentifiableDefinitionConfigDefinition[
    DefinitionT: Intersection[
        IdentifiableDefinition, ObjectDefinition[IdentifiableDefinitionConfig]
    ]
](DefinitionConfigDefinition[DefinitionT]):
    """
    Define identifiable definition configuration.
    """

    def __init__(
        self,
        *args: Any,
        porter: ResolvableDataPorter[Self, Object[DefinitionT]] | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            *args,
            porter=porter
            or (lambda definition: KeyedMappingPorter("id", FieldsPorter(definition))),
            **kwargs,
        )


class IdentifiableDefinitionConfig[
    DefinitionT: Intersection[
        IdentifiableDefinition, ObjectDefinition[IdentifiableDefinitionConfig]
    ]
](DefinitionConfig[DefinitionT]):
    """
    Configure a :py:class:`betty.definition.IdentifiableDefinition`.
    """

    id = new_machine_name_attr(label=_("ID"))
    """
    The ID.
    """

    def __init__(
        self,
        *,
        id: ResolvableMachineName,  # noqa: A002
    ):
        super().__init__()
        self.id = id
