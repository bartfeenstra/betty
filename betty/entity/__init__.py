"""Provide Betty's data model API."""

from __future__ import annotations

from inspect import signature
from typing import TYPE_CHECKING, Any, Final, final, override

from betty.association import HasAssociations
from betty.attrs.privacy import HasPrivacy
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.json_schema import JsonSchemaReference, String
from betty.linked_data import JsonLdObject, LinkedDataDumpableWithSchemaJsonLdObject
from betty.localizables.gettext import _, ngettext
from betty.localizer import default_localizer
from betty.machine_name import MachineName
from betty.media_types.json_ld import JSON_LD
from betty.plugin import PluginTypeDefinition
from betty.plugin.data import DataPlugin, DataPluginDefinition
from betty.privacy import Privacy
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )
    from betty.machine_name import ResolvableMachineName
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.requirement import Requires


class Entity(
    LinkedDataDumpableWithSchemaJsonLdObject,
    DataPlugin["EntityDefinition"],
    HasPrivacy,
    HasAssociations,
):
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

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        url_generator = await project.url_generator
        portable["@id"] = url_generator.generate(
            self, media_type=JSON_LD, absolute=True
        )
        portable["id"] = self.id

        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema._def_name = f"{kebab_case_to_lower_camel_case(cls.plugin().id)}Entity"
        schema.title = cls.plugin().label.localize(default_localizer)
        schema.add_property("$schema", JsonSchemaReference())
        schema.add_property("id", String(title="Entity ID"), False)
        schema.add_property("public_id", String(title="Public entity ID"), False)

        return schema


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
