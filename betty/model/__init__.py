"""Provide Betty's data model API."""

from __future__ import annotations

from abc import abstractmethod
from reprlib import recursive_repr
from typing import (
    TypeVar,
    Any,
    Self,
    TypeAlias,
    TYPE_CHECKING,
)
from uuid import uuid4

from typing_extensions import override

from betty.classtools import repr_instance
from betty.json.linked_data import LinkedDataDumpable, JsonLdObject
from betty.json.schema import (
    JsonSchemaReference,
    Array,
    String,
    Object,
)
from betty.locale.localizable import _, Localizable
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginRepository, Plugin
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.project import Project
    from betty.serde.dump import DumpMapping, Dump
    import builtins


ENTITY_TYPE_REPOSITORY: PluginRepository[Entity] = EntryPointPluginRepository(
    "betty.entity_type"
)
"""
The entity type plugin repository.

Read more about :doc:`/development/plugin/entity-type`.
"""


class GeneratedEntityId(str):
    """
    Generate a unique entity ID.

    Entities must have IDs for identification. However, not all entities can be provided with an ID that exists in the
    original data set (such as a third-party family tree loaded into Betty), so IDs can be generated.
    """

    __slots__ = ()

    def __new__(cls, entity_id: str | None = None):  # noqa D102
        return super().__new__(cls, entity_id or str(uuid4()))


class Entity(LinkedDataDumpable[Object], Plugin):
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
        self._id = GeneratedEntityId() if id is None else id
        super().__init__(*args, **kwargs)

    def __hash__(self) -> int:
        return hash(self.ancestry_id)

    @classmethod
    @abstractmethod
    def plugin_label_plural(cls) -> Localizable:
        """
        The human-readable entity type label, plural.
        """
        pass

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, id=self._id)

    @property
    def type(self) -> builtins.type[Self]:
        """
        The entity type.
        """
        return self.__class__

    @property
    def id(self) -> str:
        """
        The entity ID.

        This MUST be unique per entity type, per ancestry.
        """
        return self._id

    @property
    def ancestry_id(self) -> tuple[builtins.type[Self], str]:
        """
        The ancestry ID.

        This MUST be unique per ancestry.
        """
        return self.type, self.id

    @property
    def label(self) -> Localizable:
        """
        The entity's human-readable label.
        """
        return _("{entity_type} {entity_id}").format(
            entity_type=self.plugin_label(), entity_id=self.id
        )

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)

        if not isinstance(self.id, GeneratedEntityId):
            dump["@id"] = project.static_url_generator.generate(
                f"/{kebab_case_to_lower_camel_case(self.type.plugin_id())}/{self.id}/index.json",
                absolute=True,
            )
            dump["id"] = self.id

        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = JsonLdObject(
            def_name=f"{kebab_case_to_lower_camel_case(cls.plugin_id())}Entity",
            title=cls.plugin_label().localize(DEFAULT_LOCALIZER),
        )
        schema.add_property("$schema", JsonSchemaReference())
        schema.add_property("id", String(title="Entity ID"), False)
        return schema


AncestryEntityId: TypeAlias = tuple[type[Entity], str]


class UserFacingEntity:
    """
    A sentinel to mark an entity type as being visible to users (e.g. not internal).
    """

    pass


_EntityT = TypeVar("_EntityT", bound=Entity)


class EntityReferenceSchema(String):
    """
    A schema for a reference to another entity resource.
    """

    def __init__(self, entity_type: type[Entity], *, title: str | None = None):
        super().__init__(
            def_name=f"{kebab_case_to_lower_camel_case(entity_type.plugin_id())}EntityReference",
            title=title,
            description=f"A reference to the JSON resource for a {entity_type.plugin_label().localize(DEFAULT_LOCALIZER)} entity.",
            format=String.Format.URI,
        )


class EntityReferenceCollectionSchema(Array):
    """
    A schema for a collection of references to other entity resources.
    """

    def __init__(self, entity_type: type[Entity], *, title: str | None = None):
        super().__init__(
            EntityReferenceSchema(entity_type),
            title=title,
            description=f"References to the JSON resources for {entity_type.plugin_label().localize(DEFAULT_LOCALIZER)} entities.",
            def_name=f"{kebab_case_to_lower_camel_case(entity_type.plugin_id())}EntityReferenceCollection",
        )
