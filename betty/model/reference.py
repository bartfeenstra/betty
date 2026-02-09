"""
Entity references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.assertion import assert_option
from betty.data import Data, Sample
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Property
from betty.data.str import StrDefinition
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.model import EntityDefinition
from betty.plugin import resolve_id
from betty.plugin.data import PluginIdDefinition
from betty.service.hydrate import Hydratable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from betty.plugin import ResolvableId
    from betty.project import Project


@final
@ObjectDefinition(
    label=_("Entity reference"),
    samples=[
        lambda: Sample(EntityReference("person", "123"), label="Default"),
    ],
)
class EntityReference(Data, Hydratable):
    """
    A reference to an entity of any type.

    The reference is validated during hydration.

    .. data:: betty.model.reference:EntityReference
    """

    type = Property(PluginIdDefinition(EntityDefinition), label=_("Entity type"))
    """
    The type of the referenced entity. 
    """

    id = Property(StrDefinition(label=_("Entity ID")))
    """
    The ID of the referenced entity.
    """

    def __init__(
        self,
        /,
        type: ResolvableId[EntityDefinition],  # noqa: A002
        id: str,  # noqa: A002
    ):
        super().__init__()
        self.type = resolve_id(type)
        self.id = id

    @override
    @require_project
    async def hydrate(self, project: Project, /) -> None:
        assert_option(await project.plugin.plugins(EntityDefinition).ids())(self.type)
        try:
            project.ancestry[self.type][self.id]
        except KeyError:
            raise HumanFacingException(
                _(
                    'No {entity_type} with ID "{entity_id}" exists in your ancestry.'
                ).format(entity_type=self.type, entity_id=self.id)
            ) from None
