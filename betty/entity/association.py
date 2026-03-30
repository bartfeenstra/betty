"""
Entity associations.
"""

from __future__ import annotations

import weakref
from abc import abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Self, cast, final, overload, override
from urllib.parse import quote

from betty.entity import Entity, persistent_id
from betty.entity.collection import EntityCollection
from betty.entity.collection.multiple import MultipleTypesEntityCollection
from betty.entity.collection.single import SingleTypeEntityCollection
from betty.entity.reference import EntityReference
from betty.entity.schema import ToManySchema, ToZeroOrOneSchema
from betty.importlib import fully_qualified_name, import_any
from betty.json.linked_data import LinkedDataDumper
from betty.json.schema import Array, Null, OneOf, Schema
from betty.locale.localizable import resolve_localizable

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableData
    from betty.project import Project


async def _generate_associate_url(project: Project, associate: Entity, /) -> str | None:
    if not persistent_id(associate):
        return None
    if not associate.plugin().public_facing:
        return None
    url_generator = await project.url_generator
    return url_generator.generate(
        f"betty-static:///{associate.plugin().id}/{quote(associate.id)}/index.json"
    )


class AssociationRequired[OwnerT: Entity](RuntimeError):
    """
    Raised when an operation cannot be performed because the association in question is required.
    """

    def __init__(self, association: _Association[OwnerT, Any], owner: OwnerT, /):
        super().__init__(
            f"Association {fully_qualified_name(association.owner_type)}.{association.owner_attr_name} is required, but missing for {owner}."
        )


class _Association[OwnerT: Entity, AssociateT: Entity](LinkedDataDumper[OwnerT]):
    _owner_type: type[OwnerT]
    _owner_attr_name: str
    _internal_owner_attr_name: str

    def __init__(
        self,
        associate_type_name: str,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        linked_data_embedded: bool = False,
    ):
        self._associate_type_name = associate_type_name
        self._linked_data_embedded = linked_data_embedded
        self._label = resolve_localizable(label)
        self._description = (
            None if description is None else resolve_localizable(description)
        )

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        self._owner_type = owner
        self._owner_attr_name = name
        self._internal_owner_attr_name = f"_{name}"
        AssociationRegistry._register(self)

    @override
    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self._owner_type,
                self._owner_attr_name,
                self._associate_type_name,
                self._linked_data_embedded,
                self._label,
                self._description,
            )
        )

    @property
    def owner_type(self) -> type[OwnerT]:
        """
        The type of the owning entity that contains this association.

        This may be an abstract class.
        """
        return self._owner_type

    @property
    def owner_attr_name(self) -> str:
        """
        The name of the attribute on the owning entity that contains this association.
        """
        return self._owner_attr_name

    @property
    def associate_type(self) -> type[AssociateT]:
        """
        The type of any associate entities.

        This may be an abstract class.
        """
        return cast(
            "type[AssociateT]",
            import_any(self._associate_type_name),
        )

    @abstractmethod
    def resolve(self, owner: OwnerT, /) -> None:
        """
        Resolve any associates the owner may have for this association.
        """

    @abstractmethod
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        """
        Associate two entities.
        """

    @abstractmethod
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        """
        Disassociate two entities.

        :raises AssociationRequired: Raised if the association is required and the disassociation would leave it without
            any associates.
        """

    @abstractmethod
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        """
        Get the associates for the given owner.
        """


class _ToOneAssociation[OwnerT: Entity, AssociateT: Entity](
    _Association[OwnerT, AssociateT]
):
    @override
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self.__set__(owner, associate)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        setattr(owner, self._internal_owner_attr_name, None)

    @overload
    def __get__(self, instance: None, owner: type[OwnerT]) -> Self:
        pass

    @overload
    def __get__(self, instance: OwnerT, owner: type[OwnerT]) -> AssociateT:
        pass

    def __get__(self, instance: OwnerT | None, owner: type[OwnerT]):
        if instance is None:
            return self
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            raise AssociationRequired(self, instance) from None
        else:
            if value is None:
                raise AssociationRequired(self, instance)
            assert not isinstance(value, EntityReference)
            return cast(AssociateT, value)

    def __set__(self, instance: OwnerT, value: Associate[AssociateT]) -> None:
        setattr(instance, self._internal_owner_attr_name, value)

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        yield self.__get__(owner, type(owner))

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        if self._linked_data_embedded:
            return await self.associate_type.linked_data_schema(project)
        # We must allow for the associate to be missing, for example if it has a generated entity ID and the linked data
        # is not embedded, no URL can be generated.
        return ToZeroOrOneSchema(
            title=self._label,
            description=None if self._description is None else self._description,
        )

    @override
    async def dump_linked_data_for(
        self, project: Project, target: Intersection[OwnerT, Entity], /
    ) -> PortableData:
        associate = self.__get__(target, type(target))
        if self._linked_data_embedded:
            return await associate.dump_linked_data(project)
        return await _generate_associate_url(project, associate)


class _ToZeroOrOneAssociation[OwnerT: Entity, AssociateT: Entity](
    _Association[OwnerT, AssociateT]
):
    @override
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self.__set__(owner, associate)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        if associate == self.__get__(owner, type(owner)):
            self.__delete__(owner)

    @overload
    def __get__(self, instance: None, owner: type[OwnerT]) -> Self:
        pass

    @overload
    def __get__(self, instance: OwnerT, owner: type[OwnerT]) -> AssociateT | None:
        pass

    def __get__(self, instance: OwnerT | None, owner: type[OwnerT]):
        if instance is None:
            return self
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            setattr(instance, self._internal_owner_attr_name, None)
            return None
        else:
            assert not isinstance(value, EntityReference)
            return cast(AssociateT | None, value)

    def __set__(self, instance: OwnerT, value: Associate[AssociateT] | None) -> None:
        setattr(instance, self._internal_owner_attr_name, value)

    def __delete__(self, instance: OwnerT) -> None:
        self.__set__(instance, None)

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        associate = self.__get__(owner, type(owner))
        if associate is not None:
            yield associate

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        if self._linked_data_embedded:
            return OneOf(
                await self.associate_type.linked_data_schema(project),
                Null(),
                title=self._label,
                description=None if self._description is None else self._description,
            )
        return ToZeroOrOneSchema(
            title=self._label,
            description=None if self._description is None else self._description,
        )

    @override
    async def dump_linked_data_for(
        self, project: Project, target: Intersection[OwnerT, Entity], /
    ) -> PortableData:
        associate = self.__get__(target, type(target))
        if associate is None:
            return None
        if self._linked_data_embedded:
            return await associate.dump_linked_data(project)
        return await _generate_associate_url(project, associate)


class _ToManyAssociation[
    OwnerT: Entity,
    AssociateT: Entity,
    EntityCollectionT: EntityCollection[Any],
](
    _Association[OwnerT, AssociateT],
):
    @abstractmethod
    def _new_collection(self, instance: OwnerT, /) -> EntityCollectionT:
        pass

    @overload
    def __get__(self, instance: None, owner: type[OwnerT]) -> Self:
        pass

    @overload
    def __get__(self, instance: OwnerT, owner: type[OwnerT]) -> EntityCollectionT:
        pass

    def __get__(self, instance: OwnerT | None, owner: type[OwnerT]):
        if instance is None:
            return self
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            value = self._new_collection(instance)
            setattr(instance, self._internal_owner_attr_name, value)
            return value
        else:
            assert not isinstance(value, EntityReference)
            return cast(EntityCollectionT, value)

    def __set__(self, instance: OwnerT, value: Associates[AssociateT]) -> None:
        if isinstance(value, EntityReference):
            setattr(instance, self._internal_owner_attr_name, value)
        else:
            self.__get__(instance, type(instance)).replace(*value)

    def __delete__(self, instance: OwnerT) -> None:
        self.__get__(instance, type(instance)).clear()

    @override
    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self.__get__(owner, type(owner)).add(associate)

    @override
    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        self.__get__(owner, type(owner)).remove(associate)

    @override
    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        yield from self.__get__(owner, type(owner))

    @override
    def resolve(self, owner: OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, EntityReference):
            collection = self._new_collection(owner)
            setattr(owner, self._internal_owner_attr_name, collection)
            collection.add(*value.resolve())

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        if self._linked_data_embedded:
            return Array(
                await self.associate_type.linked_data_schema(project),
                title=self._label,
                description=None if self._description is None else self._description,
            )
        return ToManySchema(
            title=self._label,
            description=None if self._description is None else self._description,
        )

    @override
    async def dump_linked_data_for(
        self, project: Project, target: Intersection[OwnerT, Entity], /
    ) -> PortableData:
        associates = self.__get__(target, type(target))
        if self._linked_data_embedded:
            return [
                await associate.dump_linked_data(project) for associate in associates
            ]  # ty:ignore[invalid-return-type]
        return list(
            filter(
                None,
                [
                    await _generate_associate_url(project, associate)
                    for associate in associates
                ],
            )
        )  # ty:ignore[invalid-return-type]


class _BidirectionalAssociation[OwnerT: Entity, AssociateT: Entity](
    _Association[OwnerT, AssociateT]
):
    def __init__(
        self,
        associate_type_name: str,
        associate_attr_name: str,
        *,
        label: ResolvableLocalizable,
        linked_data_embedded: bool = False,
        description: ResolvableLocalizable | None = None,
    ):
        self._associate_attr_name = associate_attr_name
        super().__init__(
            associate_type_name,
            label=label,
            description=description,
            linked_data_embedded=linked_data_embedded,
        )

    @override
    def __hash__(self) -> int:
        return hash((super().__hash__(), self._associate_attr_name))

    @property
    def associate_attr_name(self) -> str:
        """
        The association's attribute name on the associate type.
        """
        return self._associate_attr_name

    def inverse(self) -> _BidirectionalAssociation[AssociateT, OwnerT]:
        """
        Get the inverse association.
        """
        association = AssociationRegistry.get_association(
            self.associate_type, self.associate_attr_name
        )
        assert isinstance(association, _BidirectionalAssociation)
        return association


@final
class BidirectionalToZeroOrOne[OwnerT: Entity, AssociateT: Entity](
    _ToZeroOrOneAssociation[OwnerT, AssociateT],
    _BidirectionalAssociation[OwnerT, AssociateT],
):
    r"""
    A bidirectional \\*-to-zero-or-one entity type association.
    """

    @override
    def __set__(self, instance: OwnerT, value: Associate[AssociateT] | None) -> None:
        previous_associate = self.__get__(instance, type(instance))
        if previous_associate == value:
            return
        super().__set__(instance, value)
        if previous_associate is not None:
            self.inverse().disassociate(previous_associate, instance)
        if not isinstance(value, EntityReference) and value is not None:
            self.inverse().associate(value, instance)

    @override
    def resolve(self, owner: OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, EntityReference):
            associate = value.resolve()
            setattr(owner, self._internal_owner_attr_name, value.resolve())
            if associate:
                self.inverse().associate(associate, owner)


@final
class BidirectionalToOne[OwnerT: Entity, AssociateT: Entity](
    _ToOneAssociation[OwnerT, AssociateT],
    _BidirectionalAssociation[OwnerT, AssociateT],
):
    r"""
    A bidirectional \\*-to-one entity type association.
    """

    @override
    def resolve(self, owner: OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if value is None:
            raise AssociationRequired(self, owner)
        if isinstance(value, EntityReference):
            associate = value.resolve()
            setattr(owner, self._internal_owner_attr_name, associate)
            self.inverse().associate(associate, owner)

    @override
    def __set__(self, instance: OwnerT, value: Associate[AssociateT]) -> None:
        try:
            previous_associate = cast(
                "AssociateT | None", getattr(self, self._internal_owner_attr_name)
            )
        except AttributeError:
            previous_associate = None
        if previous_associate == value:
            return
        super().__set__(instance, value)
        if previous_associate:
            self.inverse().disassociate(previous_associate, instance)
        if not isinstance(value, EntityReference):
            self.inverse().associate(value, instance)


@final
class BidirectionalToManySingleType[OwnerT: Entity, AssociateT: Entity](
    _ToManyAssociation[OwnerT, AssociateT, SingleTypeEntityCollection[AssociateT]],
    _BidirectionalAssociation[OwnerT, AssociateT],
):
    r"""
    A bidirectional \\*-to-many entity type association where all associates are of the same entity type.
    """

    @override
    def _new_collection(
        self, instance: OwnerT, /
    ) -> SingleTypeEntityCollection[AssociateT]:
        return _BidirectionalSingleTypeAssociateCollection(instance, self)


@final
class BidirectionalToManyMultipleTypes[OwnerT: Entity, AssociateT: Entity](
    _ToManyAssociation[OwnerT, AssociateT, MultipleTypesEntityCollection[AssociateT]],
    _BidirectionalAssociation[OwnerT, AssociateT],
):
    r"""
    A bidirectional \\*-to-many entity type association where associates may be of different entity types.
    """

    @override
    def _new_collection(
        self, instance: OwnerT, /
    ) -> MultipleTypesEntityCollection[AssociateT]:
        return _BidirectionalMultipleTypesAssociateCollection(
            instance,
            self,
        )


@final
class UnidirectionalToZeroOrOne[OwnerT: Entity, AssociateT: Entity](
    _ToZeroOrOneAssociation[OwnerT, AssociateT]
):
    """
    A unidirectional to-zero-or-one entity type association.
    """

    @override
    def resolve(self, owner: OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, EntityReference):
            setattr(owner, self._internal_owner_attr_name, value.resolve())


@final
class UnidirectionalToOne[OwnerT: Entity, AssociateT: Entity](
    _ToOneAssociation[OwnerT, AssociateT]
):
    """
    A unidirectional to-one entity type association.
    """

    @override
    def resolve(self, owner: OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if value is None:
            raise AssociationRequired(self, owner)
        if isinstance(value, EntityReference):
            setattr(owner, self._internal_owner_attr_name, value.resolve())


@final
class UnidirectionalToManySingleType[OwnerT: Entity, AssociateT: Entity](
    _ToManyAssociation[OwnerT, AssociateT, SingleTypeEntityCollection[AssociateT]]
):
    """
    A unidirectional to-many entity type association where all associates are of the same entity type.
    """

    @override
    def _new_collection(
        self, instance: OwnerT, /
    ) -> SingleTypeEntityCollection[AssociateT]:
        return SingleTypeEntityCollection[AssociateT]()


@final
class UnidirectionalToManyMultipleTypes[OwnerT: Entity, AssociateT: Entity](
    _ToManyAssociation[OwnerT, AssociateT, MultipleTypesEntityCollection[AssociateT]],
):
    """
    A unidirectional to-many entity type association where associates may be of different entity types.
    """

    @override
    def _new_collection(
        self, instance: OwnerT, /
    ) -> MultipleTypesEntityCollection[AssociateT]:
        return MultipleTypesEntityCollection[AssociateT]()


@final
class AssociationRegistry:
    """
    Inspect any known entity type associations.
    """

    _associations = set[_Association[Any, Any]]()

    @classmethod
    def get_all_associations(
        cls, owner: type | object, /
    ) -> set[_Association[Any, Any]]:
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
    def get_association[OwnerT: Entity](
        cls, owner: type[OwnerT] | OwnerT, owner_attr_name: str, /
    ) -> _Association[OwnerT, Any]:
        """
        Get the association for a given owner and attribute name.
        """
        for association in cls.get_all_associations(owner):
            if association.owner_attr_name == owner_attr_name:
                return association
        raise ValueError(
            f"No association exists for {fully_qualified_name(owner if isinstance(owner, type) else type(owner))}.{owner_attr_name}."
        )

    @classmethod
    def _register(cls, association: _Association[Any, Any], /) -> None:
        cls._associations.add(association)


class _BidirectionalAssociateCollection[AssociateT: Entity, OwnerT: Entity](
    EntityCollection[AssociateT]
):
    def __init__(
        self,
        owner: OwnerT,
        association: _BidirectionalAssociation[OwnerT, AssociateT],
        /,
    ):
        super().__init__()
        self._association = association
        self.__owner = weakref.ref(owner)

    @property
    def _owner(self) -> OwnerT:
        owner = self.__owner()
        assert owner is not None, (
            "This associate collection's owner no longer exists in memory."
        )
        return owner

    @override
    def _on_add(self, *entities: AssociateT) -> None:
        super()._on_add(*entities)
        for associate in entities:
            self._association.inverse().associate(associate, self._owner)

    @override
    def _on_remove(self, *entities: AssociateT) -> None:
        super()._on_remove(*entities)
        for associate in entities:
            self._association.inverse().disassociate(associate, self._owner)


class _BidirectionalSingleTypeAssociateCollection[OwnerT: Entity, AssociateT: Entity](
    _BidirectionalAssociateCollection[AssociateT, OwnerT],
    SingleTypeEntityCollection[AssociateT],
):
    pass


class _BidirectionalMultipleTypesAssociateCollection[
    OwnerT: Entity,
    AssociateT: Entity,
](
    _BidirectionalAssociateCollection[AssociateT, OwnerT],
    MultipleTypesEntityCollection[AssociateT],
):
    pass


def resolve(*entities: Entity) -> None:
    """
    Resolve all entities' associates.

    You **MUST** call this on all entities once the resolvers you have set on them can indeed be resolved.
    """
    for entity in entities:
        for association in AssociationRegistry.get_all_associations(entity):
            association.resolve(entity)


type Associate[EntityT: Entity] = EntityT | EntityReference
type Associates[EntityT: Entity] = Iterable[Associate[EntityT]]
