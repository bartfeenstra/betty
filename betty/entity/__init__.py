"""Provide Betty's data model API."""

from __future__ import annotations

from inspect import signature
from typing import TYPE_CHECKING, Any, Final, Self, final, override

from betty.attrs.privacy import HasPrivacy
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.linked_data import HasLinkedDataAttrs
from betty.linked_data_porters.callback import CallbackLinkedDataPorter
from betty.localizables.gettext import _, ngettext
from betty.machine_name import MachineName
from betty.plugin import PluginTypeDefinition
from betty.plugin.data import DataPlugin, DataPluginDefinition
from betty.privacy import Privacy

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from betty.association import Association
    from betty.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )
    from betty.machine_name import ResolvableMachineName
    from betty.project import Project
    from betty.requirement import Requires


class Entity(HasLinkedDataAttrs, DataPlugin["EntityDefinition"], HasPrivacy):
    """
    An entity is a uniquely identifiable data container.

    To test your own subclasses, use :py:class:`betty.test_utils.entity.EntityTestBase`.
    """

    def __init__(
        self,
        *args: Any,
        id: ResolvableMachineName | None = None,  # noqa: A002
        privacy: Privacy = Privacy.UNDETERMINED,
        **kwargs: Any,
    ):
        self.id: Final[MachineName] = (
            MachineName() if id is None else MachineName.resolve(id)
        )
        """
        The entity ID.

        This MUST be unique per entity type, per ancestry.
        """
        super().__init__(*args, privacy=privacy, **kwargs)

    @final
    @classmethod
    def associations(cls) -> Iterable[Association[Self]]:
        """
        Get all associations on entities of this type.
        """
        from betty.association import Association

        for prop in cls.props():
            if isinstance(prop, Association):
                yield prop

    @override
    def __hash__(self) -> int:
        return hash((type(self), self.id))

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.id == other.id

    @property
    def label(self) -> Localizable:
        """
        The entity's human-readable label.
        """
        return _("{entity_type} {entity_id}").format(
            entity_type=self.plugin().label, entity_id=self.id
        )


@final
@PluginTypeDefinition(
    "entity",
    label=_("Entity"),
    label_plural=_("Entities"),
    label_countable=ngettext("{count} entity", "{count} entities"),
    description=_(
        "Entities represent the information in your ancestry, such as people and places."
    ),
)
class EntityDefinition[EntityT: Entity = Entity](
    CountableHumanFacingDefinition,
    ObjectDefinition[EntityT],
    DataPluginDefinition[EntityT],
):
    """
    .. plugin_type:: entity.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        auto: bool = True,
        description: ResolvableLocalizable | None = None,
        linked_data_type: str = "https://schema.org/Thing",
        public_facing: bool = True,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
            requires=requires,
            linked_data_porter=CallbackLinkedDataPorter(
                self._linked_data_schema, self._dump_linked_data, linked_data_type
            ),
        )
        self.public_facing: Final[bool] = public_facing
        """
        Whether entities of this type are public-facing.
        """


type EntityResolver[EntityT: Entity = Entity] = (
    Callable[[], EntityT] | Callable[[Project], EntityT]
)
type ResolvableEntity[EntityT: Entity = Entity] = EntityT | EntityResolver[EntityT]


def resolve[EntityT: Entity = Entity](
    project: Project, entity: ResolvableEntity[EntityT], /
) -> EntityT:
    """
    Resolve an entity or entity resolver to its entity.
    """
    if isinstance(entity, Entity):
        return entity  # ty:ignore[invalid-return-type]
    match len(signature(entity).parameters):
        case 1:
            return entity(project)  # ty:ignore[too-many-positional-arguments]
        case _:
            return entity()  # ty:ignore[missing-argument]
