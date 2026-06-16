"""Provide Betty's data model API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, final, override

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.json_schema import JsonSchemaReference, String
from betty.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
)
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localize import default_localizer
from betty.machine_name import MachineName
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.prop import HasProps
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )
    from betty.machine_name import ResolvableMachineName
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.requirement import Requires


class Entity(
    LinkedDataDumpableWithSchemaJsonLdObject, Plugin["EntityDefinition"], HasProps
):
    """
    An entity is a uniquely identifiable data container.

    To test your own subclasses, use :py:class:`betty.test_utils.entity.EntityTestBase`.
    """

    def __init__(
        self,
        *args: Any,
        id: ResolvableMachineName | None = None,  # noqa: A002
        **kwargs: Any,
    ):
        self.id: Final[MachineName] = (
            MachineName() if id is None else MachineName.resolve(id)
        )
        """
        The entity ID.

        This MUST be unique per entity type, per ancestry.
        """
        super().__init__(*args, **kwargs)

    @override
    def __hash__(self) -> int:
        return hash((type(self), self.id))

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
            f"betty-static:///{self.plugin().id}/{self.id}/index.json",
            absolute=True,
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
class EntityDefinition(CountableHumanFacingDefinition, PluginClsDefinition[Entity]):
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


type AncestryEntityId = tuple[type[Entity], MachineName]
