"""Provide Betty's data model API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final, override
from uuid import uuid4

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.hashid import hashid
from betty.linked_data import LinkedDataDumpableWithSchema
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    import builtins

    from betty.json_schema import Schema
    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )
    from betty.machine_name import ResolvableMachineName
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.requirement import Requires


class NonPersistentId(str):
    """
    A randomly generated ID that is not persistent.

    Entities must have IDs for identification. However, not all entities can be provided with an ID that exists in the
    original data set (such as a third-party family tree loaded into Betty).

    Non-persistent IDs are helpful in case there is no external ID that can be used. However, as they do not persist
    when reloading an ancestry, they *MUST NOT* be in contexts where persistent identifiers are expected, such as in
    URLs.
    """

    __slots__ = ()

    def __new__(cls, entity_id: str | None = None, /):  # noqa: D102
        return super().__new__(cls, entity_id or str(uuid4()))


class Entity(LinkedDataDumpableWithSchema, Plugin["EntityDefinition"]):
    """
    An entity is a uniquely identifiable data container.

    To test your own subclasses, use :py:class:`betty.test_utils.entity.EntityTestBase`.
    """

    def __init__(
        self,
        id: str | None = None,  # noqa: A002
        *args: Any,
        **kwargs: Any,
    ):
        self._id = NonPersistentId() if id is None else id
        self._public_id = self._id if id is None else hashid(id)
        super().__init__(*args, **kwargs)

    @override
    def __hash__(self) -> int:
        return hash(self.ancestry_id)

    @property
    def id(self) -> str:
        """
        The entity ID.

        This MUST be unique per entity type, per ancestry.
        """
        return self._id

    @property
    def public_id(self) -> str:
        """
        The public entity ID.

        This MUST be unique per entity type, per ancestry.

        A public ID consists of alphanumeric characters only, and can therefore safely be used across file systems.
        """
        return self._public_id

    @property
    def ancestry_id(self) -> tuple[builtins.type[Self], str]:
        """
        The ancestry ID.

        This MUST be unique per ancestry.
        """
        return type(self), self.id

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

        if persistent_id(self) and self.plugin().public_facing:
            url_generator = await project.url_generator
            portable["@id"] = url_generator.generate(
                f"betty-static:///{self.plugin().id}/{self.id}/index.json",
                absolute=True,
            )
        portable["id"] = self.id

        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> Schema:
        schema = await super().linked_data_schema(project)
        schema._def_name = f"{kebab_case_to_lower_camel_case(cls.plugin().id)}Entity"
        schema.title = cls.plugin().label.localize(DEFAULT_LOCALIZER)
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
        self._public_facing = public_facing

    @property
    def public_facing(self) -> bool:
        """
        Whether entities of this type are public-facing.
        """
        return self._public_facing


type AncestryEntityId = tuple[type[Entity], str]


def persistent_id(entity_or_id: Entity | str, /) -> bool:
    """
    Test if an entity ID is persistent.

    See :py:class:`betty.entity.NonPersistentId`.
    """
    return not isinstance(
        entity_or_id if isinstance(entity_or_id, str) else entity_or_id.id,
        NonPersistentId,
    )
