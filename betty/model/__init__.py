"""Provide Betty's data model API."""

from __future__ import annotations

from abc import abstractmethod
from reprlib import recursive_repr
from typing import (
    TypeVar,
    Generic,
    Any,
    Self,
    TypeAlias,
    TYPE_CHECKING,
)
from uuid import uuid4

from typing_extensions import override

from betty.classtools import repr_instance
from betty.json.linked_data import (
    add_json_ld,
    LinkedDataDumpable,
)
from betty.json.schema import Schema, JsonSchemaReference
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


class Entity(LinkedDataDumpable, Plugin):
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

        dump["$schema"] = project.static_url_generator.generate(
            f"schema.json#/definitions/{kebab_case_to_lower_camel_case(self.plugin_id())}Entity",
            absolute=True,
        )

        if not isinstance(self.id, GeneratedEntityId):
            dump["@id"] = project.static_url_generator.generate(
                f"/{kebab_case_to_lower_camel_case(self.type.plugin_id())}/{self.id}/index.json",
                absolute=True,
            )
            dump["id"] = self.id

        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = Schema(name=f"{kebab_case_to_lower_camel_case(cls.plugin_id())}Entity")
        schema.schema["type"] = "object"
        schema.schema["title"] = cls.plugin_label().localize(DEFAULT_LOCALIZER)
        schema.schema["properties"] = {
            "$schema": JsonSchemaReference().embed(schema),
            "id": {
                "type": "string",
            },
        }
        schema.schema["additionalProperties"] = False
        add_json_ld(schema)
        return schema


AncestryEntityId: TypeAlias = tuple[type[Entity], str]


class UserFacingEntity:
    """
    A sentinel to mark an entity type as being visible to users (e.g. not internal).
    """

    pass


_EntityT = TypeVar("_EntityT", bound=Entity)


class AliasedEntity(Generic[_EntityT]):
    """
    An aliased entity wraps an entity and gives aliases its ID.

    Aliases are used when deserializing ancestries from sources where intermediate IDs
    are used to declare associations between entities. By wrapping an entity in an alias,
    the alias can use the intermediate ID, allowing it to be inserted into APIs such as
    :py:class:`betty.model.graph.EntityGraphBuilder` which will use the alias ID to finalize
    associations before the original entities are returned.
    """

    def __init__(self, original_entity: _EntityT, aliased_entity_id: str | None = None):
        self._entity = original_entity
        self._id = (
            GeneratedEntityId() if aliased_entity_id is None else aliased_entity_id
        )

    @override
    def __repr__(self) -> str:
        return repr_instance(self, id=self.id)

    @property
    def type(self) -> builtins.type[Entity]:
        """
        The type of the aliased entity.
        """
        return self._entity.type

    @property
    def id(self) -> str:
        """
        The alias entity ID.
        """
        return self._id

    def unalias(self) -> _EntityT:
        """
        Get the original entity.
        """
        return self._entity


AliasableEntity: TypeAlias = _EntityT | AliasedEntity[_EntityT]


def unalias(entity: AliasableEntity[_EntityT]) -> _EntityT:
    """
    Unalias a potentially aliased entity.
    """
    if isinstance(entity, AliasedEntity):
        return entity.unalias()
    return entity
