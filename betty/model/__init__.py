"""Provide Betty's data model API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, TypeAlias, TypeVar, final
from uuid import uuid4

from typing_extensions import override

from betty.hashid import hashid
from betty.json.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
)
from betty.json.schema import JsonSchemaReference, String
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.mutability import Mutable
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.human_facing import CountableHumanFacingPluginDefinition
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    import builtins

    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        LocalizableLike,
    )
    from betty.machine_name import MachineName
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


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

    def __new__(cls, entity_id: str | None = None, /):  # noqa D102
        return super().__new__(cls, entity_id or str(uuid4()))


class Entity(
    LinkedDataDumpableWithSchemaJsonLdObject, Mutable, Plugin["EntityDefinition"]
):
    """
    An entity is a uniquely identifiable data container.

    Read more about :doc:`/development/plugin/entity-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.model.EntityTestBase`.
    """

    def __init__(
        self,
        id: str | None = None,  # noqa A002
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
    async def dump_linked_data(self, project: Project, /) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)

        if persistent_id(self) and self.plugin().public_facing:
            url_generator = await project.url_generator
            dump["@id"] = url_generator.generate(
                f"betty-static:///{self.plugin().id}/{self.id}/index.json",
                absolute=True,
            )
        dump["id"] = self.id

        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema._def_name = f"{kebab_case_to_lower_camel_case(cls.plugin().id)}Entity"
        schema.title = cls.plugin().label.localize(DEFAULT_LOCALIZER)
        schema.add_property("$schema", JsonSchemaReference())
        schema.add_property("id", String(title="Entity ID"), False)

        return schema


@final
@PluginTypeDefinition(
    "entity",
    Entity,
    _("Entity"),
    _("Entities"),
    ngettext("{count} entity", "{count} entities"),
    discovery=EntryPointDiscovery("betty.entity_type"),
)
class EntityDefinition(CountableHumanFacingPluginDefinition[Entity]):
    """
    An entity definition.
    """

    def __init__(
        self,
        plugin_id: MachineName,
        *,
        label: LocalizableLike,
        label_plural: LocalizableLike,
        label_countable: CountableLocalizable,
        description: LocalizableLike | None = None,
        public_facing: bool = True,
    ):
        super().__init__(
            plugin_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
        )
        self._public_facing = public_facing

    @property
    def public_facing(self) -> bool:
        """
        Whether entities of this type are public-facing.
        """
        return self._public_facing


AncestryEntityId: TypeAlias = tuple[type[Entity], str]


def persistent_id(entity_or_id: Entity | str, /) -> bool:
    """
    Test if an entity ID is persistent.

    See :py:class:`betty.model.NonPersistentId`.
    """
    return not isinstance(
        entity_or_id if isinstance(entity_or_id, str) else entity_or_id.id,
        NonPersistentId,
    )


_EntityT = TypeVar("_EntityT", bound=Entity)
