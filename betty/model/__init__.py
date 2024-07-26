"""Provide Betty's data model API."""

from __future__ import annotations

import functools
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from reprlib import recursive_repr
from typing import (
    TypeVar,
    Generic,
    Iterable,
    Any,
    overload,
    cast,
    Iterator,
    Callable,
    Self,
    TypeAlias,
    TYPE_CHECKING,
)
from uuid import uuid4

from typing_extensions import override

from betty.asyncio import wait_to_thread
from betty.classtools import repr_instance
from betty.functools import Uniquifier
from betty.importlib import import_any
from betty.json.linked_data import LinkedDataDumpable, add_json_ld
from betty.json.schema import ref_json_schema
from betty.locale.localizable import _, Localizable
from betty.plugin import PluginRepository, Plugin
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.machine_name import MachineName
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
            f"schema.json#/definitions/entity/{kebab_case_to_lower_camel_case(self.type.plugin_id())}",
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
    async def linked_data_schema(cls, project: Project) -> DumpMapping[Dump]:
        schema = await super().linked_data_schema(project)
        schema["type"] = "object"
        schema["properties"] = {
            "$schema": ref_json_schema(schema),
            "id": {
                "type": "string",
            },
        }
        schema["required"] = [
            "$schema",
        ]
        schema["additionalProperties"] = False
        add_json_ld(schema)
        return schema


AncestryEntityId: TypeAlias = tuple[type[Entity], str]


class UserFacingEntity:
    """
    A sentinel to mark an entity type as being visible to users (e.g. not internal).
    """

    pass


_EntityT = TypeVar("_EntityT", bound=Entity)
_EntityU = TypeVar("_EntityU", bound=Entity)
_TargetT = TypeVar("_TargetT")
_OwnerT = TypeVar("_OwnerT")
_AssociateT = TypeVar("_AssociateT")
_AssociateU = TypeVar("_AssociateU")
_LeftAssociateT = TypeVar("_LeftAssociateT")
_RightAssociateT = TypeVar("_RightAssociateT")


class EntityCollection(Generic[_TargetT], ABC):
    """
    Provide a collection of entities.
    """

    __slots__ = ()

    def __init__(self):
        super().__init__()

    def _on_add(self, *entities: _TargetT & Entity) -> None:
        pass

    def _on_remove(self, *entities: _TargetT & Entity) -> None:
        pass

    @property
    def view(self) -> list[_TargetT & Entity]:
        """
        A view of the entities at the time of calling.
        """
        return [*self]

    @abstractmethod
    def add(self, *entities: _TargetT & Entity) -> None:
        """
        Add the given entities.
        """
        pass

    @abstractmethod
    def remove(self, *entities: _TargetT & Entity) -> None:
        """
        Remove the given entities.
        """
        pass

    def replace(self, *entities: _TargetT & Entity) -> None:
        """
        Replace all entities with the given ones.
        """
        self.remove(*(entity for entity in self if entity not in entities))
        self.add(*entities)

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all entities from the collection.
        """
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[_TargetT & Entity]:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @overload
    def __getitem__(self, index: int) -> _TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[_TargetT & Entity]:
        pass

    @abstractmethod
    def __getitem__(
        self, key: int | slice
    ) -> _TargetT & Entity | list[_TargetT & Entity]:
        pass

    @abstractmethod
    def __delitem__(self, key: _TargetT & Entity) -> None:
        pass

    @abstractmethod
    def __contains__(self, value: Any) -> bool:
        pass

    def _known(self, *entities: _TargetT & Entity) -> Iterable[_TargetT & Entity]:
        for entity in Uniquifier(entities):
            if entity in self:
                yield entity

    def _unknown(self, *entities: _TargetT & Entity) -> Iterable[_TargetT & Entity]:
        for entity in Uniquifier(entities):
            if entity not in self:
                yield entity


_EntityCollectionT = TypeVar("_EntityCollectionT", bound=EntityCollection[_EntityT])


class _EntityTypeAssociation(Generic[_OwnerT, _AssociateT], ABC):
    def __init__(
        self,
        owner_type: type[_OwnerT],
        owner_attr_name: str,
        associate_type_name: str,
    ):
        self._owner_type = owner_type
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f"_{owner_attr_name}"
        self._associate_type_name = associate_type_name

    def __hash__(self) -> int:
        return hash(
            (
                self._owner_type,
                self._owner_attr_name,
                self._associate_type_name,
            )
        )

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self,
            owner_type=self._owner_type,
            owner_attr_name=self._owner_attr_name,
            associate_type_name=self._associate_type_name,
        )

    @property
    def owner_type(self) -> type[_OwnerT]:
        return self._owner_type

    @property
    def owner_attr_name(self) -> str:
        return self._owner_attr_name

    @property
    def associate_type(self) -> type[_AssociateT]:
        return cast(
            type[_AssociateT],
            import_any(self._associate_type_name),
        )

    def register(  # type: ignore[misc]
        self: ToAny[_OwnerT, _AssociateT],
    ) -> None:
        EntityTypeAssociationRegistry._register(self)

        original_init = self._owner_type.__init__

        @functools.wraps(original_init)
        def _init(owner: _OwnerT & Entity, *args: Any, **kwargs: Any) -> None:
            self.initialize(owner)
            original_init(owner, *args, **kwargs)

        self._owner_type.__init__ = _init  # type: ignore[assignment, method-assign]

    @abstractmethod
    def initialize(self, owner: _OwnerT & Entity) -> None:
        pass

    def finalize(self, owner: _OwnerT & Entity) -> None:
        self.delete(owner)
        delattr(owner, self._owner_private_attr_name)

    @abstractmethod
    def delete(self, owner: _OwnerT & Entity) -> None:
        pass

    @abstractmethod
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        pass

    @abstractmethod
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        pass


class BidirectionalEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT], _EntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A bidirectional entity type association.
    """

    def __init__(
        self,
        owner_type: type[_OwnerT],
        owner_attr_name: str,
        associate_type_name: str,
        associate_attr_name: str,
    ):
        super().__init__(
            owner_type,
            owner_attr_name,
            associate_type_name,
        )
        self._associate_attr_name = associate_attr_name

    def __hash__(self) -> int:
        return hash(
            (
                self._owner_type,
                self._owner_attr_name,
                self._associate_type_name,
                self._associate_attr_name,
            )
        )

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self,
            owner_type=self._owner_type,
            owner_attr_name=self._owner_attr_name,
            associate_type_name=self._associate_type_name,
            associate_attr_name=self._associate_attr_name,
        )

    @property
    def associate_attr_name(self) -> str:
        """
        The association's attribute name on the associate type.
        """
        return self._associate_attr_name

    def inverse(self) -> BidirectionalEntityTypeAssociation[_AssociateT, _OwnerT]:
        """
        Get the inverse association.
        """
        association = EntityTypeAssociationRegistry.get_association(
            self.associate_type, self.associate_attr_name
        )
        assert isinstance(association, BidirectionalEntityTypeAssociation)
        return association


class ToOneEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT], _EntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-one entity type association.
    """

    @override
    def register(self) -> None:
        super().register()
        setattr(
            self.owner_type,
            self.owner_attr_name,
            property(
                self.get,
                self.set,
                self.delete,
            ),
        )

    @override
    def initialize(self, owner: _OwnerT & Entity) -> None:
        setattr(owner, self._owner_private_attr_name, None)

    def get(self, owner: _OwnerT & Entity) -> _AssociateT & Entity | None:
        """
        Get the associate from the given owner.
        """
        return getattr(owner, self._owner_private_attr_name)  # type: ignore[no-any-return]

    def set(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity | None
    ) -> None:
        """
        Set the associate for the given owner.
        """
        setattr(owner, self._owner_private_attr_name, associate)

    @override
    def delete(self, owner: _OwnerT & Entity) -> None:
        self.set(owner, None)

    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.set(owner, associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        if associate == self.get(owner):
            self.delete(owner)


class ToManyEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT], _EntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A to-many entity type association.
    """

    @override
    def register(self) -> None:
        super().register()
        setattr(
            self.owner_type,
            self.owner_attr_name,
            property(
                self.get,
                self.set,
                self.delete,
            ),
        )

    def get(self, owner: _OwnerT & Entity) -> EntityCollection[_AssociateT & Entity]:
        """
        Get the associates from the given owner.
        """
        return cast(
            EntityCollection["_AssociateT & Entity"],
            getattr(owner, self._owner_private_attr_name),
        )

    def set(
        self, owner: _OwnerT & Entity, entities: Iterable[_AssociateT & Entity]
    ) -> None:
        """
        Set the associates on the given owner.
        """
        self.get(owner).replace(*entities)

    @override
    def delete(self, owner: _OwnerT & Entity) -> None:
        self.get(owner).clear()

    @override
    def associate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.get(owner).add(associate)

    @override
    def disassociate(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity
    ) -> None:
        self.get(owner).remove(associate)


class BidirectionalToOneEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT],
    ToOneEntityTypeAssociation[_OwnerT, _AssociateT],
    BidirectionalEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-one entity type association.
    """

    @override
    def set(
        self, owner: _OwnerT & Entity, associate: _AssociateT & Entity | None
    ) -> None:
        previous_associate = self.get(owner)
        if previous_associate == associate:
            return
        super().set(owner, associate)
        if previous_associate is not None:
            self.inverse().disassociate(previous_associate, owner)
        if associate is not None:
            self.inverse().associate(associate, owner)


class BidirectionalToManyEntityTypeAssociation(
    Generic[_OwnerT, _AssociateT],
    ToManyEntityTypeAssociation[_OwnerT, _AssociateT],
    BidirectionalEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional *-to-many entity type association.
    """

    @override
    def initialize(self, owner: _OwnerT & Entity) -> None:
        setattr(
            owner,
            self._owner_private_attr_name,
            _BidirectionalAssociateCollection(
                owner,
                self,
            ),
        )


class ToOne(
    Generic[_OwnerT, _AssociateT], ToOneEntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-one entity type association.
    """

    pass


class OneToOne(
    Generic[_OwnerT, _AssociateT],
    BidirectionalToOneEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional one-to-one entity type association.
    """

    pass


class ManyToOne(
    Generic[_OwnerT, _AssociateT],
    BidirectionalToOneEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional many-to-one entity type association.
    """

    pass


class ToMany(
    Generic[_OwnerT, _AssociateT], ToManyEntityTypeAssociation[_OwnerT, _AssociateT]
):
    """
    A unidirectional to-many entity type association.
    """

    @override
    def initialize(self, owner: _OwnerT & Entity) -> None:
        setattr(
            owner,
            self._owner_private_attr_name,
            SingleTypeEntityCollection[_AssociateT](self.associate_type),
        )


class OneToMany(
    Generic[_OwnerT, _AssociateT],
    BidirectionalToManyEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional one-to-many entity type association.
    """

    pass


class ManyToMany(
    Generic[_OwnerT, _AssociateT],
    BidirectionalToManyEntityTypeAssociation[_OwnerT, _AssociateT],
):
    """
    A bidirectional many-to-many entity type association.
    """

    pass


ToAny: TypeAlias = (
    ToOneEntityTypeAssociation[_OwnerT, _AssociateT]
    | ToManyEntityTypeAssociation[_OwnerT, _AssociateT]
)


def to_one(
    owner_attr_name: str,
    associate_type_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a unidirectional to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ToOne(
            owner_type,
            owner_attr_name,
            associate_type_name,
        ).register()
        return owner_type

    return _decorator


def one_to_one(
    owner_attr_name: str,
    associate_type_name: str,
    associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional one-to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        OneToOne(
            owner_type,
            owner_attr_name,
            associate_type_name,
            associate_attr_name,
        ).register()
        return owner_type

    return _decorator


def many_to_one(
    owner_attr_name: str,
    associate_type_name: str,
    associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional many-to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ManyToOne(
            owner_type,
            owner_attr_name,
            associate_type_name,
            associate_attr_name,
        ).register()
        return owner_type

    return _decorator


def to_many(
    owner_attr_name: str,
    associate_type_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a unidirectional to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ToMany(
            owner_type,
            owner_attr_name,
            associate_type_name,
        ).register()
        return owner_type

    return _decorator


def one_to_many(
    owner_attr_name: str,
    associate_type_name: str,
    associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional one-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        OneToMany(
            owner_type,
            owner_attr_name,
            associate_type_name,
            associate_attr_name,
        ).register()
        return owner_type

    return _decorator


def many_to_many(
    owner_attr_name: str,
    associate_type_name: str,
    associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional many-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ManyToMany(
            owner_type,
            owner_attr_name,
            associate_type_name,
            associate_attr_name,
        ).register()
        return owner_type

    return _decorator


def many_to_one_to_many(
    left_associate_type_name: str,
    left_associate_attr_name: str,
    left_owner_attr_name: str,
    right_owner_attr_name: str,
    right_associate_type_name: str,
    right_associate_attr_name: str,
) -> Callable[[type[_OwnerT]], type[_OwnerT]]:
    """
    Add a bidirectional many-to-one-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[_OwnerT]) -> type[_OwnerT]:
        ManyToOne(
            owner_type,
            left_owner_attr_name,
            left_associate_type_name,
            left_associate_attr_name,
        ).register()
        ManyToOne(
            owner_type,
            right_owner_attr_name,
            right_associate_type_name,
            right_associate_attr_name,
        ).register()
        return owner_type

    return _decorator


class EntityTypeAssociationRegistry:
    """
    Inspect any known entity type associations.
    """

    _associations = set[ToAny[Any, Any]]()

    @classmethod
    def get_all_associations(cls, owner: type | object) -> set[ToAny[Any, Any]]:
        """
        Get all associations for an owner.
        """
        owner_type = owner if isinstance(owner, type) else type(owner)
        return {
            association
            for association in cls._associations
            if association.owner_type in owner_type.__mro__
        }

    @classmethod
    def get_association(
        cls, owner: type[_OwnerT] | _OwnerT & Entity, owner_attr_name: str
    ) -> ToAny[_OwnerT, Any]:
        """
        Get the association for a given owner and attribute name.
        """
        for association in cls.get_all_associations(owner):
            if association.owner_attr_name == owner_attr_name:
                return association
        raise ValueError(
            f"No association exists for {owner if isinstance(owner, type) else owner.__class__}.{owner_attr_name}."
        )

    @classmethod
    def get_associates(
        cls, owner: _EntityT, association: ToAny[_EntityT, _AssociateT]
    ) -> Iterable[_AssociateT]:
        """
        Get the associates for a given owner and association.
        """
        associates: _AssociateT | None | Iterable[_AssociateT] = getattr(
            owner, f"_{association.owner_attr_name}"
        )
        if isinstance(association, ToOneEntityTypeAssociation):
            if associates is None:
                return
            yield cast(_AssociateT, associates)
            return
        yield from cast(Iterable[_AssociateT], associates)

    @classmethod
    def _register(cls, association: ToAny[Any, Any]) -> None:
        cls._associations.add(association)

    @classmethod
    def initialize(cls, *owners: Entity) -> None:
        """
        Initialize the given owners' associations.
        """
        for owner in owners:
            for association in cls.get_all_associations(owner):
                association.initialize(owner)

    @classmethod
    def finalize(cls, *owners: Entity) -> None:
        """
        Finalize all associations from the given owners.
        """
        for owner in owners:
            for association in cls.get_all_associations(owner):
                association.finalize(owner)


class SingleTypeEntityCollection(Generic[_TargetT], EntityCollection[_TargetT]):
    """
    Collect entities of a single type.
    """

    __slots__ = "_entities", "_target_type"

    def __init__(
        self,
        target_type: type[_TargetT],
    ):
        super().__init__()
        self._entities: list[_TargetT & Entity] = []
        self._target_type = target_type

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, target_type=self._target_type, length=len(self))

    @override
    def add(self, *entities: _TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self._entities.append(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: _TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self._entities.remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    @override
    def clear(self) -> None:
        self.remove(*self)

    @override
    def __iter__(self) -> Iterator[_TargetT & Entity]:
        return self._entities.__iter__()

    @override
    def __len__(self) -> int:
        return len(self._entities)

    @overload
    def __getitem__(self, index: int) -> _TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[_TargetT & Entity]:
        pass

    @overload
    def __getitem__(self, entity_id: str) -> _TargetT & Entity:
        pass

    @override
    def __getitem__(
        self, key: int | slice | str
    ) -> _TargetT & Entity | list[_TargetT & Entity]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        return self._getitem_by_entity_id(key)

    def _getitem_by_index(self, index: int) -> _TargetT & Entity:
        return self._entities[index]

    def _getitem_by_indices(self, indices: slice) -> list[_TargetT & Entity]:
        return self.view[indices]

    def _getitem_by_entity_id(self, entity_id: str) -> _TargetT & Entity:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(
            f'Cannot find a {self._target_type} entity with ID "{entity_id}".'
        )

    @override
    def __delitem__(self, key: str | _TargetT & Entity) -> None:
        if isinstance(key, self._target_type):
            return self._delitem_by_entity(cast("_TargetT & Entity", key))
        if isinstance(key, str):
            return self._delitem_by_entity_id(key)
        raise TypeError(f"Cannot find entities by {repr(key)}.")

    def _delitem_by_entity(self, entity: _TargetT & Entity) -> None:
        self.remove(entity)

    def _delitem_by_entity_id(self, entity_id: str) -> None:
        for entity in self._entities:
            if entity_id == entity.id:
                self.remove(entity)
                return

    @override
    def __contains__(self, value: Any) -> bool:
        if isinstance(value, self._target_type):
            return self._contains_by_entity(cast("_TargetT & Entity", value))
        if isinstance(value, str):
            return self._contains_by_entity_id(value)
        return False

    def _contains_by_entity(self, other_entity: _TargetT & Entity) -> bool:
        return any(other_entity is entity for entity in self._entities)

    def _contains_by_entity_id(self, entity_id: str) -> bool:
        return any(entity.id == entity_id for entity in self._entities)


SingleType_EntityCollectionT = TypeVar(
    "SingleType_EntityCollectionT", bound=SingleTypeEntityCollection[_AssociateT]
)


class MultipleTypesEntityCollection(Generic[_TargetT], EntityCollection[_TargetT]):
    """
    Collect entities of multiple types.
    """

    __slots__ = "_collections"

    def __init__(self):
        super().__init__()
        self._collections: dict[type[Entity], SingleTypeEntityCollection[Entity]] = {}

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(
            self,
            entity_types=", ".join(
                entity_type.plugin_id() for entity_type in self._collections
            ),
            length=len(self),
        )

    def _get_collection(
        self, entity_type: type[_EntityT]
    ) -> SingleTypeEntityCollection[_EntityT]:
        assert issubclass(entity_type, Entity), f"{entity_type} is not an entity type."
        try:
            return cast(
                SingleTypeEntityCollection[_EntityT], self._collections[entity_type]
            )
        except KeyError:
            self._collections[entity_type] = SingleTypeEntityCollection(entity_type)
            return cast(
                SingleTypeEntityCollection[_EntityT], self._collections[entity_type]
            )

    @overload
    def __getitem__(self, index: int) -> _TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[_TargetT & Entity]:
        pass

    @overload
    def __getitem__(
        self, entity_type_id: MachineName
    ) -> SingleTypeEntityCollection[Entity]:
        pass

    @overload
    def __getitem__(
        self, entity_type: type[_EntityT]
    ) -> SingleTypeEntityCollection[_EntityT]:
        pass

    @override
    def __getitem__(
        self,
        key: int | slice | str | type[_EntityT],
    ) -> (
        _TargetT & Entity
        | SingleTypeEntityCollection[Entity]
        | SingleTypeEntityCollection[_EntityT]
        | list[_TargetT & Entity]
    ):
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_type_id(key)
        return self._getitem_by_entity_type(key)

    def _getitem_by_entity_type(
        self, entity_type: type[_EntityT]
    ) -> SingleTypeEntityCollection[_EntityT]:
        return self._get_collection(entity_type)

    def _getitem_by_entity_type_id(
        self, entity_type_id: MachineName
    ) -> SingleTypeEntityCollection[Entity]:
        return self._get_collection(
            wait_to_thread(ENTITY_TYPE_REPOSITORY.get(entity_type_id)),
        )

    def _getitem_by_index(self, index: int) -> _TargetT & Entity:
        return self.view[index]

    def _getitem_by_indices(self, indices: slice) -> list[_TargetT & Entity]:
        return self.view[indices]

    @override
    def __delitem__(
        self, key: str | type[_TargetT & Entity] | _TargetT & Entity
    ) -> None:
        if isinstance(key, type):
            return self._delitem_by_type(
                key,
            )
        if isinstance(key, Entity):
            return self._delitem_by_entity(
                key,  # type: ignore[arg-type]
            )
        return self._delitem_by_entity_type_id(key)

    def _delitem_by_type(self, entity_type: type[_TargetT & Entity]) -> None:
        removed_entities = [*self._get_collection(entity_type)]
        self._get_collection(entity_type).clear()
        if removed_entities:
            self._on_remove(*removed_entities)

    def _delitem_by_entity(self, entity: _TargetT & Entity) -> None:
        self.remove(entity)

    def _delitem_by_entity_type_id(self, entity_type_id: MachineName) -> None:
        self._delitem_by_type(
            wait_to_thread(ENTITY_TYPE_REPOSITORY.get(entity_type_id)),  # type: ignore[arg-type]
        )

    @override
    def __iter__(self) -> Iterator[_TargetT & Entity]:
        for collection in self._collections.values():
            for entity in collection:
                yield cast("_TargetT & Entity", entity)

    @override
    def __len__(self) -> int:
        return sum(map(len, self._collections.values()))

    @override
    def __contains__(self, value: Any) -> bool:
        if isinstance(value, Entity):
            return self._contains_by_entity(value)
        return False

    def _contains_by_entity(self, other_entity: Any) -> bool:
        return any(other_entity is entity for entity in self)

    @override
    def add(self, *entities: _TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self[entity.type].add(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: _TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self[entity.type].remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    @override
    def clear(self) -> None:
        removed_entities = (*self,)
        for collection in self._collections.values():
            collection.clear()
        if removed_entities:
            self._on_remove(*removed_entities)


class _BidirectionalAssociateCollection(
    Generic[_AssociateT, _OwnerT], SingleTypeEntityCollection[_AssociateT]
):
    __slots__ = "__owner", "_association"

    def __init__(
        self,
        owner: _OwnerT & Entity,
        association: BidirectionalEntityTypeAssociation[_OwnerT, _AssociateT],
    ):
        super().__init__(association.associate_type)
        self._association = association
        self.__owner = weakref.ref(owner)

    @property
    def _owner(self) -> _OwnerT & Entity:
        owner = self.__owner()
        if owner is None:
            raise RuntimeError(
                "This associate collection's owner no longer exists in memory."
            )
        return owner

    @override
    def _on_add(self, *entities: _AssociateT & Entity) -> None:
        super()._on_add(*entities)
        for associate in entities:
            self._association.inverse().associate(associate, self._owner)

    @override
    def _on_remove(self, *entities: _AssociateT & Entity) -> None:
        super()._on_remove(*entities)
        for associate in entities:
            self._association.inverse().disassociate(associate, self._owner)


class AliasedEntity(Generic[_EntityT]):
    """
    An aliased entity wraps an entity and gives aliases its ID.

    Aliases are used when deserializing ancestries from sources where intermediate IDs
    are used to declare associations between entities. By wrapping an entity in an alias,
    the alias can use the intermediate ID, allowing it to be inserted into APIs such as
    :py:class:`betty.model.EntityGraphBuilder` who will use the alias ID to finalize
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


_EntityGraphBuilderEntities: TypeAlias = dict[
    type[Entity], dict[str, AliasableEntity[Entity]]
]


_EntityGraphBuilderAssociations: TypeAlias = dict[
    type[Entity],  # The owner entity type.
    dict[
        str,  # The owner attribute name.
        dict[str, list[AncestryEntityId]],  # The owner ID.  # The associate IDs.
    ],
]


class _EntityGraphBuilder:
    def __init__(self):
        self._entities: _EntityGraphBuilderEntities = defaultdict(dict)
        self._associations: _EntityGraphBuilderAssociations = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self._built = False

    def _assert_unbuilt(self) -> None:
        if self._built:
            raise RuntimeError("This entity graph has been built already.")

    def _iter(self) -> Iterator[AliasableEntity[Entity]]:
        for entity_type in self._entities:
            yield from self._entities[entity_type].values()

    def _build_associations(self) -> None:
        for owner_type, owner_attrs in self._associations.items():
            for owner_attr_name, owner_associations in owner_attrs.items():
                association = EntityTypeAssociationRegistry.get_association(
                    owner_type, owner_attr_name
                )
                for owner_id, associate_ancestry_ids in owner_associations.items():
                    associates = [
                        unalias(self._entities[associate_type][associate_id])
                        for associate_type, associate_id in associate_ancestry_ids
                    ]
                    owner = unalias(self._entities[owner_type][owner_id])
                    if isinstance(association, ToOneEntityTypeAssociation):
                        association.set(owner, associates[0])
                    else:
                        association.set(owner, associates)

    def build(self) -> Iterator[Entity]:
        self._assert_unbuilt()
        self._built = True

        unaliased_entities = list(
            map(
                unalias,
                self._iter(),
            )
        )

        EntityTypeAssociationRegistry.initialize(*unaliased_entities)
        self._build_associations()

        yield from unaliased_entities


class EntityGraphBuilder(_EntityGraphBuilder):
    """
    Assemble entities and their associations.

    (De)serializing data often means that special care must be taken with the associations,
    relationships, or links between data points, as those form a graph, a network, a tangled
    web of data. When deserializing entity A with an association to entity B, that association
    cannot be finalized until entity B is parsed as well. But, if entity B subsequently has
    an association with entity A (the association is bidirectional), this results in an endless
    cycle.

    This class prevents the problem by letting you add entities and associations separately.
    Associations are finalized when you are done adding, avoiding cycle errors.
    """

    def add_entity(self, *entities: AliasableEntity[Entity]) -> None:
        """
        Add entities to the graph.
        """
        self._assert_unbuilt()

        for entity in entities:
            self._entities[entity.type][entity.id] = entity

    def add_association(
        self,
        owner_type: type[Entity],
        owner_id: str,
        owner_attr_name: str,
        associate_type: type[Entity],
        associate_id: str,
    ) -> None:
        """
        Add an association between two entities to the graph.
        """
        self._assert_unbuilt()

        self._associations[owner_type][owner_attr_name][owner_id].append(
            (associate_type, associate_id)
        )


@contextmanager
def record_added(
    entities: EntityCollection[_EntityT],
) -> Iterator[MultipleTypesEntityCollection[_EntityT]]:
    """
    Record all entities that are added to a collection.
    """
    original = [*entities]
    added = MultipleTypesEntityCollection[_EntityT]()
    yield added
    added.add(*[entity for entity in entities if entity not in original])
