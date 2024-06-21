"""Provide Betty's data model API."""

from __future__ import annotations

import functools
import weakref
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

from betty.classtools import repr_instance
from betty.functools import Uniquifier
from betty.importlib import import_any, fully_qualified_type_name
from betty.json.linked_data import LinkedDataDumpable, add_json_ld
from betty.json.schema import ref_json_schema
from betty.locale import Str, Localizable
from betty.string import camel_case_to_kebab_case, upper_camel_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.serde.dump import DictDump, Dump
    import builtins
    from betty.app import App


T = TypeVar("T")


class GeneratedEntityId(str):
    """
    Generate a unique entity ID.

    Entities must have IDs for identification. However, not all entities can be provided with an ID that exists in the
    original data set (such as a third-party family tree loaded into Betty), so IDs can be generated.
    """

    __slots__ = ()

    def __new__(cls, entity_id: str | None = None):  # noqa D102
        return super().__new__(cls, entity_id or str(uuid4()))


class Entity(LinkedDataDumpable):
    """
    An entity is a uniquely identifiable data container.
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
    def entity_type_label(cls) -> Localizable:
        """
        The human-readable entity type label, singular.
        """
        raise NotImplementedError(repr(cls))

    @classmethod
    def entity_type_label_plural(cls) -> Localizable:
        """
        The human-readable entity type label, plural.
        """
        raise NotImplementedError(repr(cls))

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
        return Str._(
            "{entity_type} {entity_id}",
            entity_type=self.entity_type_label(),
            entity_id=self.id,
        )

    @override
    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)

        entity_type_name = get_entity_type_name(self.type)
        dump["$schema"] = app.static_url_generator.generate(
            f"schema.json#/definitions/entity/{upper_camel_case_to_lower_camel_case(entity_type_name)}",
            absolute=True,
        )

        if not isinstance(self.id, GeneratedEntityId):
            dump["@id"] = app.static_url_generator.generate(
                f"/{camel_case_to_kebab_case(entity_type_name)}/{self.id}/index.json",
                absolute=True,
            )
            dump["id"] = self.id

        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
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


class EntityTypeProvider:
    """
    Provide additional entity types.
    """

    async def entity_types(self) -> set[type[Entity]]:
        """
        The entity types.
        """
        raise NotImplementedError(repr(self))


EntityT = TypeVar("EntityT", bound=Entity)
EntityU = TypeVar("EntityU", bound=Entity)
TargetT = TypeVar("TargetT")
OwnerT = TypeVar("OwnerT")
AssociateT = TypeVar("AssociateT")
AssociateU = TypeVar("AssociateU")
LeftAssociateT = TypeVar("LeftAssociateT")
RightAssociateT = TypeVar("RightAssociateT")


def get_entity_type_name(entity_type_definition: type[Entity] | Entity) -> str:
    """
    Get the entity type name for an entity or entity type.
    """
    if isinstance(entity_type_definition, Entity):
        entity_type = entity_type_definition.type
    else:
        entity_type = entity_type_definition

    if entity_type.__module__.startswith("betty.model.ancestry"):
        return entity_type.__name__
    return f"{entity_type.__module__}.{entity_type.__name__}"


def get_entity_type(entity_type_name: str) -> type[Entity]:
    """
    Get the entity type for an entity type name.
    """
    try:
        return import_any(entity_type_name)  # type: ignore[no-any-return]
    except ImportError:
        try:
            return import_any(f"betty.model.ancestry.{entity_type_name}")  # type: ignore[no-any-return]
        except ImportError:
            raise EntityTypeImportError(entity_type_name) from None


class EntityTypeError(ValueError):
    """
    A error occurred when trying to determine and import an entity type.
    """

    pass


class EntityTypeImportError(EntityTypeError, ImportError):
    """
    Raised when an alleged entity type cannot be imported.
    """

    def __init__(self, entity_type_name: str):
        super().__init__(
            f'Cannot find and import an entity with name "{entity_type_name}".'
        )


class EntityTypeInvalidError(EntityTypeError, ImportError):
    """
    Raised for types that are not valid entity types.
    """

    def __init__(self, entity_type: type):
        super().__init__(
            f"{entity_type.__module__}.{entity_type.__name__} is not an entity type class. Entity types must extend {Entity.__module__}.{Entity.__name__} directly."
        )


class EntityCollection(Generic[TargetT]):
    """
    Provide a collection of entities.
    """

    __slots__ = ()

    def __init__(self):
        super().__init__()

    def _on_add(self, *entities: TargetT & Entity) -> None:
        pass

    def _on_remove(self, *entities: TargetT & Entity) -> None:
        pass

    @property
    def view(self) -> list[TargetT & Entity]:
        """
        A view of the entities at the time of calling.
        """
        return [*self]

    def add(self, *entities: TargetT & Entity) -> None:
        """
        Add the given entities.
        """
        raise NotImplementedError(repr(self))

    def remove(self, *entities: TargetT & Entity) -> None:
        """
        Remove the given entities.
        """
        raise NotImplementedError(repr(self))

    def replace(self, *entities: TargetT & Entity) -> None:
        """
        Replace all entities with the given ones.
        """
        self.remove(*(entity for entity in self if entity not in entities))
        self.add(*entities)

    def clear(self) -> None:
        """
        Clear all entities from the collection.
        """
        raise NotImplementedError(repr(self))

    def __iter__(self) -> Iterator[TargetT & Entity]:
        raise NotImplementedError(repr(self))

    def __len__(self) -> int:
        raise NotImplementedError(repr(self))

    @overload
    def __getitem__(self, index: int) -> TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[TargetT & Entity]:
        pass

    def __getitem__(
        self, key: int | slice
    ) -> TargetT & Entity | list[TargetT & Entity]:
        raise NotImplementedError(repr(self))

    def __delitem__(self, key: TargetT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def __contains__(self, value: Any) -> bool:
        raise NotImplementedError(repr(self))

    def _known(self, *entities: TargetT & Entity) -> Iterable[TargetT & Entity]:
        for entity in Uniquifier(entities):
            if entity in self:
                yield entity

    def _unknown(self, *entities: TargetT & Entity) -> Iterable[TargetT & Entity]:
        for entity in Uniquifier(entities):
            if entity not in self:
                yield entity


EntityCollectionT = TypeVar("EntityCollectionT", bound=EntityCollection[EntityT])


class _EntityTypeAssociation(Generic[OwnerT, AssociateT]):
    def __init__(
        self,
        owner_type: type[OwnerT],
        owner_attr_name: str,
        associate_type_name: str,
    ):
        self._owner_type = owner_type
        self._owner_attr_name = owner_attr_name
        self._owner_private_attr_name = f"_{owner_attr_name}"
        self._associate_type_name = associate_type_name
        self._associate_type: type[AssociateT] | None = None

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
    def owner_type(self) -> type[OwnerT]:
        return self._owner_type

    @property
    def owner_attr_name(self) -> str:
        return self._owner_attr_name

    @property
    def associate_type(self) -> type[AssociateT]:
        if self._associate_type is None:
            self._associate_type = import_any(self._associate_type_name)
        return self._associate_type

    def register(  # type: ignore[misc]
        self: ToAny[OwnerT, AssociateT],
    ) -> None:
        EntityTypeAssociationRegistry._register(self)

        original_init = self._owner_type.__init__

        @functools.wraps(original_init)
        def _init(owner: OwnerT & Entity, *args: Any, **kwargs: Any) -> None:
            self.initialize(owner)
            original_init(owner, *args, **kwargs)

        self._owner_type.__init__ = _init  # type: ignore[assignment, method-assign]

    def initialize(self, owner: OwnerT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def finalize(self, owner: OwnerT & Entity) -> None:
        self.delete(owner)
        delattr(owner, self._owner_private_attr_name)

    def delete(self, owner: OwnerT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def associate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        raise NotImplementedError(repr(self))

    def disassociate(
        self, owner: OwnerT & Entity, associate: AssociateT & Entity
    ) -> None:
        raise NotImplementedError(repr(self))


class BidirectionalEntityTypeAssociation(
    Generic[OwnerT, AssociateT], _EntityTypeAssociation[OwnerT, AssociateT]
):
    """
    A bidirectional entity type association.
    """

    def __init__(
        self,
        owner_type: type[OwnerT],
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

    def inverse(self) -> BidirectionalEntityTypeAssociation[AssociateT, OwnerT]:
        """
        Get the inverse association.
        """
        association = EntityTypeAssociationRegistry.get_association(
            self.associate_type, self.associate_attr_name
        )
        assert isinstance(association, BidirectionalEntityTypeAssociation)
        return association


class ToOneEntityTypeAssociation(
    Generic[OwnerT, AssociateT], _EntityTypeAssociation[OwnerT, AssociateT]
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
    def initialize(self, owner: OwnerT & Entity) -> None:
        setattr(owner, self._owner_private_attr_name, None)

    def get(self, owner: OwnerT & Entity) -> AssociateT & Entity | None:
        """
        Get the associate from the given owner.
        """
        return getattr(owner, self._owner_private_attr_name)  # type: ignore[no-any-return]

    def set(
        self, owner: OwnerT & Entity, associate: AssociateT & Entity | None
    ) -> None:
        """
        Set the associate for the given owner.
        """
        setattr(owner, self._owner_private_attr_name, associate)

    @override
    def delete(self, owner: OwnerT & Entity) -> None:
        self.set(owner, None)

    @override
    def associate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        self.set(owner, associate)

    @override
    def disassociate(
        self, owner: OwnerT & Entity, associate: AssociateT & Entity
    ) -> None:
        if associate == self.get(owner):
            self.delete(owner)


class ToManyEntityTypeAssociation(
    Generic[OwnerT, AssociateT], _EntityTypeAssociation[OwnerT, AssociateT]
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

    def get(self, owner: OwnerT & Entity) -> EntityCollection[AssociateT & Entity]:
        """
        Get the associates from the given owner.
        """
        return cast(
            EntityCollection["AssociateT & Entity"],
            getattr(owner, self._owner_private_attr_name),
        )

    def set(
        self, owner: OwnerT & Entity, entities: Iterable[AssociateT & Entity]
    ) -> None:
        """
        Set the associates on the given owner.
        """
        self.get(owner).replace(*entities)

    @override
    def delete(self, owner: OwnerT & Entity) -> None:
        self.get(owner).clear()

    @override
    def associate(self, owner: OwnerT & Entity, associate: AssociateT & Entity) -> None:
        self.get(owner).add(associate)

    @override
    def disassociate(
        self, owner: OwnerT & Entity, associate: AssociateT & Entity
    ) -> None:
        self.get(owner).remove(associate)


class BidirectionalToOneEntityTypeAssociation(
    Generic[OwnerT, AssociateT],
    ToOneEntityTypeAssociation[OwnerT, AssociateT],
    BidirectionalEntityTypeAssociation[OwnerT, AssociateT],
):
    """
    A bidirectional *-to-one entity type association.
    """

    @override
    def set(
        self, owner: OwnerT & Entity, associate: AssociateT & Entity | None
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
    Generic[OwnerT, AssociateT],
    ToManyEntityTypeAssociation[OwnerT, AssociateT],
    BidirectionalEntityTypeAssociation[OwnerT, AssociateT],
):
    """
    A bidirectional *-to-many entity type association.
    """

    @override
    def initialize(self, owner: OwnerT & Entity) -> None:
        setattr(
            owner,
            self._owner_private_attr_name,
            _BidirectionalAssociateCollection(
                owner,
                self,
            ),
        )


class ToOne(
    Generic[OwnerT, AssociateT], ToOneEntityTypeAssociation[OwnerT, AssociateT]
):
    """
    A unidirectional to-one entity type association.
    """

    pass


class OneToOne(
    Generic[OwnerT, AssociateT],
    BidirectionalToOneEntityTypeAssociation[OwnerT, AssociateT],
):
    """
    A bidirectional one-to-one entity type association.
    """

    pass


class ManyToOne(
    Generic[OwnerT, AssociateT],
    BidirectionalToOneEntityTypeAssociation[OwnerT, AssociateT],
):
    """
    A bidirectional many-to-one entity type association.
    """

    pass


class ToMany(
    Generic[OwnerT, AssociateT], ToManyEntityTypeAssociation[OwnerT, AssociateT]
):
    """
    A unidirectional to-many entity type association.
    """

    @override
    def initialize(self, owner: OwnerT & Entity) -> None:
        setattr(
            owner,
            self._owner_private_attr_name,
            SingleTypeEntityCollection[AssociateT](self.associate_type),
        )


class OneToMany(
    Generic[OwnerT, AssociateT],
    BidirectionalToManyEntityTypeAssociation[OwnerT, AssociateT],
):
    """
    A bidirectional one-to-many entity type association.
    """

    pass


class ManyToMany(
    Generic[OwnerT, AssociateT],
    BidirectionalToManyEntityTypeAssociation[OwnerT, AssociateT],
):
    """
    A bidirectional many-to-many entity type association.
    """

    pass


ToAny: TypeAlias = (
    ToOneEntityTypeAssociation[OwnerT, AssociateT]
    | ToManyEntityTypeAssociation[OwnerT, AssociateT]
)


def to_one(
    owner_attr_name: str,
    associate_type_name: str,
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    """
    Add a unidirectional to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    """
    Add a bidirectional one-to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    """
    Add a bidirectional many-to-one association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    """
    Add a unidirectional to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    """
    Add a bidirectional one-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    """
    Add a bidirectional many-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
) -> Callable[[type[OwnerT]], type[OwnerT]]:
    """
    Add a bidirectional many-to-one-to-many association to an entity or entity mixin.
    """

    def _decorator(owner_type: type[OwnerT]) -> type[OwnerT]:
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
        cls, owner: type[OwnerT] | OwnerT & Entity, owner_attr_name: str
    ) -> ToAny[OwnerT, Any]:
        """
        Get the association for a given owner and attribute name.
        """
        for association in cls.get_all_associations(owner):
            if association.owner_attr_name == owner_attr_name:
                return association
        raise ValueError(
            f"No association exists for {fully_qualified_type_name(owner if isinstance(owner, type) else owner.__class__)}.{owner_attr_name}."
        )

    @classmethod
    def get_associates(
        cls, owner: EntityT, association: ToAny[EntityT, AssociateT]
    ) -> Iterable[AssociateT]:
        """
        Get the associates for a given owner and association.
        """
        associates: AssociateT | None | Iterable[AssociateT] = getattr(
            owner, f"_{association.owner_attr_name}"
        )
        if isinstance(association, ToOneEntityTypeAssociation):
            if associates is None:
                return
            yield cast(AssociateT, associates)
            return
        yield from cast(Iterable[AssociateT], associates)

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


class SingleTypeEntityCollection(Generic[TargetT], EntityCollection[TargetT]):
    """
    Collect entities of a single type.
    """

    __slots__ = "_entities", "_target_type"

    def __init__(
        self,
        target_type: type[TargetT],
    ):
        super().__init__()
        self._entities: list[TargetT & Entity] = []
        self._target_type = target_type

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, target_type=self._target_type, length=len(self))

    @override
    def add(self, *entities: TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self._entities.append(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: TargetT & Entity) -> None:
        removed_entities = [*self._known(*entities)]
        for entity in removed_entities:
            self._entities.remove(entity)
        if removed_entities:
            self._on_remove(*removed_entities)

    @override
    def clear(self) -> None:
        self.remove(*self)

    @override
    def __iter__(self) -> Iterator[TargetT & Entity]:
        return self._entities.__iter__()

    @override
    def __len__(self) -> int:
        return len(self._entities)

    @overload
    def __getitem__(self, index: int) -> TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[TargetT & Entity]:
        pass

    @overload
    def __getitem__(self, entity_id: str) -> TargetT & Entity:
        pass

    @override
    def __getitem__(
        self, key: int | slice | str
    ) -> TargetT & Entity | list[TargetT & Entity]:
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        return self._getitem_by_entity_id(key)

    def _getitem_by_index(self, index: int) -> TargetT & Entity:
        return self._entities[index]

    def _getitem_by_indices(self, indices: slice) -> list[TargetT & Entity]:
        return self.view[indices]

    def _getitem_by_entity_id(self, entity_id: str) -> TargetT & Entity:
        for entity in self._entities:
            if entity_id == entity.id:
                return entity
        raise KeyError(
            f'Cannot find a {self._target_type} entity with ID "{entity_id}".'
        )

    @override
    def __delitem__(self, key: str | TargetT & Entity) -> None:
        if isinstance(key, self._target_type):
            return self._delitem_by_entity(cast("TargetT & Entity", key))
        if isinstance(key, str):
            return self._delitem_by_entity_id(key)
        raise TypeError(f"Cannot find entities by {repr(key)}.")

    def _delitem_by_entity(self, entity: TargetT & Entity) -> None:
        self.remove(entity)

    def _delitem_by_entity_id(self, entity_id: str) -> None:
        for entity in self._entities:
            if entity_id == entity.id:
                self.remove(entity)
                return

    @override
    def __contains__(self, value: Any) -> bool:
        if isinstance(value, self._target_type):
            return self._contains_by_entity(cast("TargetT & Entity", value))
        if isinstance(value, str):
            return self._contains_by_entity_id(value)
        return False

    def _contains_by_entity(self, other_entity: TargetT & Entity) -> bool:
        return any(other_entity is entity for entity in self._entities)

    def _contains_by_entity_id(self, entity_id: str) -> bool:
        return any(entity.id == entity_id for entity in self._entities)


SingleTypeEntityCollectionT = TypeVar(
    "SingleTypeEntityCollectionT", bound=SingleTypeEntityCollection[AssociateT]
)


class MultipleTypesEntityCollection(Generic[TargetT], EntityCollection[TargetT]):
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
            entity_types=", ".join(map(get_entity_type_name, self._collections.keys())),
            length=len(self),
        )

    def _get_collection(
        self, entity_type: type[EntityT]
    ) -> SingleTypeEntityCollection[EntityT]:
        assert issubclass(entity_type, Entity), f"{entity_type} is not an entity type."
        try:
            return cast(
                SingleTypeEntityCollection[EntityT], self._collections[entity_type]
            )
        except KeyError:
            self._collections[entity_type] = SingleTypeEntityCollection(entity_type)
            return cast(
                SingleTypeEntityCollection[EntityT], self._collections[entity_type]
            )

    @overload
    def __getitem__(self, index: int) -> TargetT & Entity:
        pass

    @overload
    def __getitem__(self, indices: slice) -> list[TargetT & Entity]:
        pass

    @overload
    def __getitem__(self, entity_type_name: str) -> SingleTypeEntityCollection[Entity]:
        pass

    @overload
    def __getitem__(
        self, entity_type: type[EntityT]
    ) -> SingleTypeEntityCollection[EntityT]:
        pass

    @override
    def __getitem__(
        self,
        key: int | slice | str | type[EntityT],
    ) -> (
        TargetT & Entity
        | SingleTypeEntityCollection[Entity]
        | SingleTypeEntityCollection[EntityT]
        | list[TargetT & Entity]
    ):
        if isinstance(key, int):
            return self._getitem_by_index(key)
        if isinstance(key, slice):
            return self._getitem_by_indices(key)
        if isinstance(key, str):
            return self._getitem_by_entity_type_name(key)
        return self._getitem_by_entity_type(key)

    def _getitem_by_entity_type(
        self, entity_type: type[EntityT]
    ) -> SingleTypeEntityCollection[EntityT]:
        return self._get_collection(entity_type)

    def _getitem_by_entity_type_name(
        self, entity_type_name: str
    ) -> SingleTypeEntityCollection[Entity]:
        return self._get_collection(
            get_entity_type(entity_type_name),
        )

    def _getitem_by_index(self, index: int) -> TargetT & Entity:
        return self.view[index]

    def _getitem_by_indices(self, indices: slice) -> list[TargetT & Entity]:
        return self.view[indices]

    @override
    def __delitem__(self, key: str | type[TargetT & Entity] | TargetT & Entity) -> None:
        if isinstance(key, type):
            return self._delitem_by_type(
                key,
            )
        if isinstance(key, Entity):
            return self._delitem_by_entity(
                key,  # type: ignore[arg-type]
            )
        return self._delitem_by_entity_type_name(key)

    def _delitem_by_type(self, entity_type: type[TargetT & Entity]) -> None:
        removed_entities = [*self._get_collection(entity_type)]
        self._get_collection(entity_type).clear()
        if removed_entities:
            self._on_remove(*removed_entities)

    def _delitem_by_entity(self, entity: TargetT & Entity) -> None:
        self.remove(entity)

    def _delitem_by_entity_type_name(self, entity_type_name: str) -> None:
        self._delitem_by_type(
            get_entity_type(entity_type_name),  # type: ignore[arg-type]
        )

    @override
    def __iter__(self) -> Iterator[TargetT & Entity]:
        for collection in self._collections.values():
            for entity in collection:
                yield cast("TargetT & Entity", entity)

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
    def add(self, *entities: TargetT & Entity) -> None:
        added_entities = [*self._unknown(*entities)]
        for entity in added_entities:
            self[entity.type].add(entity)
        if added_entities:
            self._on_add(*added_entities)

    @override
    def remove(self, *entities: TargetT & Entity) -> None:
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
    Generic[AssociateT, OwnerT], SingleTypeEntityCollection[AssociateT]
):
    __slots__ = "__owner", "_association"

    def __init__(
        self,
        owner: OwnerT & Entity,
        association: BidirectionalEntityTypeAssociation[OwnerT, AssociateT],
    ):
        super().__init__(association.associate_type)
        self._association = association
        self.__owner = weakref.ref(owner)

    @property
    def _owner(self) -> OwnerT & Entity:
        owner = self.__owner()
        if owner is None:
            raise RuntimeError(
                "This associate collection's owner no longer exists in memory."
            )
        return owner

    @override
    def _on_add(self, *entities: AssociateT & Entity) -> None:
        super()._on_add(*entities)
        for associate in entities:
            self._association.inverse().associate(associate, self._owner)

    @override
    def _on_remove(self, *entities: AssociateT & Entity) -> None:
        super()._on_remove(*entities)
        for associate in entities:
            self._association.inverse().disassociate(associate, self._owner)


class AliasedEntity(Generic[EntityT]):
    """
    An aliased entity wraps an entity and gives aliases its ID.

    Aliases are used when deserializing ancestries from sources where intermediate IDs
    are used to declare associations between entities. By wrapping an entity in an alias,
    the alias can use the intermediate ID, allowing it to be inserted into APIs such as
    :py:class:`betty.model.EntityGraphBuilder` who will use the alias ID to finalize
    associations before the original entities are returned.
    """

    def __init__(self, original_entity: EntityT, aliased_entity_id: str | None = None):
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

    def unalias(self) -> EntityT:
        """
        Get the original entity.
        """
        return self._entity


AliasableEntity: TypeAlias = EntityT | AliasedEntity[EntityT]


def unalias(entity: AliasableEntity[EntityT]) -> EntityT:
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
    entities: EntityCollection[EntityT],
) -> Iterator[MultipleTypesEntityCollection[EntityT]]:
    """
    Record all entities that are added to a collection.
    """
    original = [*entities]
    added = MultipleTypesEntityCollection[EntityT]()
    yield added
    added.add(*[entity for entity in entities if entity not in original])
