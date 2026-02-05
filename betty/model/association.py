"""
Entity associations.
"""

from __future__ import annotations

import weakref
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Self,
    TypeAlias,
    TypeVar,
    cast,
    final,
    overload,
)
from urllib.parse import quote

from typing_extensions import override

from betty.importlib import fully_qualified_name, import_any
from betty.json.linked_data import LinkedDataDumper
from betty.json.schema import Array, Null, OneOf, Schema
from betty.locale.localizable import resolve_localizable
from betty.model import Entity, persistent_id
from betty.model.collections import (
    EntityCollection,
    MultipleTypesEntityCollection,
    SingleTypeEntityCollection,
)
from betty.model.schema import ToManySchema, ToZeroOrOneSchema

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableData
    from betty.project import Project

_T = TypeVar("_T")
_EntityT = TypeVar("_EntityT", bound=Entity)
_OwnerT = TypeVar("_OwnerT", bound=Entity)
_AssociateT = TypeVar("_AssociateT", bound=Entity)
_EntityCollectionT = TypeVar("_EntityCollectionT", bound=EntityCollection[Any])


async def _generate_associate_url(project: Project, associate: Entity, /) -> str | None:
    if not persistent_id(associate):
        return None
    if not associate.plugin().public_facing:
        return None
    url_generator = await project.url_generator
    return url_generator.generate(
        f"betty-static:///{associate.plugin().id}/{quote(associate.id)}/index.json"
    )


class AssociationRequired(RuntimeError):
    """
    Raised when an operation cannot be performed because the association in question is required.
    """

    def __init__(self, association: _Association[_OwnerT, Any], owner: _OwnerT, /):
        super().__init__(
            f"Association {fully_qualified_name(association.owner_type)}.{association.owner_attr_name} is required, but missing for {owner}."
        )


class _Resolver(ABC, Generic[_T]):
    @abstractmethod
    def resolve(self) -> _T:
        """
        Return the resolved entity or entities.

        :raises ResolutionError: Raised if resolution failed.
        """


class ToZeroOrOneResolver(_Resolver[_EntityT | None]):
    """
    An object that can optionally resolve to an entity.
    """


class ToOneResolver(_Resolver[_EntityT]):
    """
    An object that can resolve to an entity.
    """


class ToManyResolver(_Resolver[Iterable[_EntityT]]):
    """
    An object that can resolve to a collection of entities.
    """


class _TemporaryResolver(_Resolver[_T]):
    @override
    def resolve(self) -> _T:
        raise RuntimeError(
            "This temporary resolver was supposed to be replaced. It intentionally cannot resolve itself."
        )


class TemporaryToZeroOrOneResolver(
    _TemporaryResolver[_EntityT], ToZeroOrOneResolver[_EntityT]
):
    """
    A 'temporary' to-zero-or-one resolver.

    This is helpful to satisfy association requirements in multiple steps. Users **MUST** ensure that this resolver
    is replaced by a real value, because the resolver will never be able to resolve itself.
    """


class TemporaryToOneResolver(_TemporaryResolver[_EntityT], ToOneResolver[_EntityT]):
    """
    A 'temporary' to-one resolver.

    This is helpful to satisfy association requirements in multiple steps. Users **MUST** ensure that this resolver
    is replaced by a real value, because the resolver will never be able to resolve itself.
    """


class TemporaryToManyResolver(_TemporaryResolver[_EntityT], ToManyResolver[_EntityT]):
    """
    A 'temporary' to-many resolver.

    This is helpful to satisfy association requirements in multiple steps. Users **MUST** ensure that this resolver
    is replaced by a real value, because the resolver will never be able to resolve itself.
    """


class _Association(LinkedDataDumper[_OwnerT], Generic[_OwnerT, _AssociateT]):
    _owner_type: type[_OwnerT]
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

    def __set_name__(self, owner: type[_OwnerT], name: str) -> None:
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
    def owner_type(self) -> type[_OwnerT]:
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
    def associate_type(self) -> type[_AssociateT]:
        """
        The type of any associate entities.

        This may be an abstract class.
        """
        return cast(
            "type[_AssociateT]",
            import_any(self._associate_type_name),
        )

    @abstractmethod
    def resolve(self, owner: _OwnerT, /) -> None:
        """
        Resolve any associates the owner may have for this association.
        """

    @abstractmethod
    def associate(self, owner: _OwnerT, associate: _AssociateT, /) -> None:
        """
        Associate two entities.
        """

    @abstractmethod
    def disassociate(self, owner: _OwnerT, associate: _AssociateT, /) -> None:
        """
        Disassociate two entities.

        :raises AssociationRequired: Raised if the association is required and the disassociation would leave it without
            any associates.
        """

    @abstractmethod
    def get_associates(self, owner: _OwnerT, /) -> Iterable[_AssociateT]:
        """
        Get the associates for the given owner.
        """


class _ToOneAssociation(_Association[_OwnerT, _AssociateT]):
    @override
    def associate(self, owner: _OwnerT, associate: _AssociateT, /) -> None:
        self.__set__(owner, associate)

    @override
    def disassociate(self, owner: _OwnerT, associate: _AssociateT, /) -> None:
        setattr(owner, self._internal_owner_attr_name, None)

    @overload
    def __get__(self, instance: None, owner: type[_OwnerT]) -> Self:
        pass

    @overload
    def __get__(self, instance: _OwnerT, owner: type[_OwnerT]) -> _AssociateT:
        pass

    def __get__(self, instance: _OwnerT | None, owner: type[_OwnerT]):
        if instance is None:
            return self
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            raise AssociationRequired(self, instance) from None
        else:
            if value is None:
                raise AssociationRequired(self, instance)
            assert not isinstance(value, _Resolver)
            return cast(_AssociateT, value)

    def __set__(self, instance: _OwnerT, value: ToOneAssociate[_AssociateT]) -> None:
        setattr(instance, self._internal_owner_attr_name, value)

    @override
    def get_associates(self, owner: _OwnerT, /) -> Iterable[_AssociateT]:
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
        self, project: Project, target: Intersection[_OwnerT, Entity], /
    ) -> PortableData:
        associate = self.__get__(target, type(target))
        if self._linked_data_embedded:
            return await associate.dump_linked_data(project)
        return await _generate_associate_url(project, associate)


class _ToZeroOrOneAssociation(_Association[_OwnerT, _AssociateT]):
    @override
    def associate(self, owner: _OwnerT, associate: _AssociateT, /) -> None:
        self.__set__(owner, associate)

    @override
    def disassociate(self, owner: _OwnerT, associate: _AssociateT, /) -> None:
        if associate == self.__get__(owner, type(owner)):
            self.__delete__(owner)

    @overload
    def __get__(self, instance: None, owner: type[_OwnerT]) -> Self:
        pass

    @overload
    def __get__(self, instance: _OwnerT, owner: type[_OwnerT]) -> _AssociateT | None:
        pass

    def __get__(self, instance: _OwnerT | None, owner: type[_OwnerT]):
        if instance is None:
            return self
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            setattr(instance, self._internal_owner_attr_name, None)
            return None
        else:
            assert not isinstance(value, _Resolver)
            return cast(_AssociateT | None, value)

    def __set__(
        self, instance: _OwnerT, value: ToZeroOrOneAssociate[_AssociateT]
    ) -> None:
        setattr(instance, self._internal_owner_attr_name, value)

    def __delete__(self, instance: _OwnerT) -> None:
        self.__set__(instance, None)

    @override
    def get_associates(self, owner: _OwnerT, /) -> Iterable[_AssociateT]:
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
        self, project: Project, target: Intersection[_OwnerT, Entity], /
    ) -> PortableData:
        associate = self.__get__(target, type(target))
        if associate is None:
            return None
        if self._linked_data_embedded:
            return await associate.dump_linked_data(project)
        return await _generate_associate_url(project, associate)


class _ToManyAssociation(
    _Association[_OwnerT, _AssociateT],
    Generic[_OwnerT, _AssociateT, _EntityCollectionT],
):
    @abstractmethod
    def _new_collection(self, instance: _OwnerT, /) -> _EntityCollectionT:
        pass

    @overload
    def __get__(self, instance: None, owner: type[_OwnerT]) -> Self:
        pass

    @overload
    def __get__(self, instance: _OwnerT, owner: type[_OwnerT]) -> _EntityCollectionT:
        pass

    def __get__(self, instance: _OwnerT | None, owner: type[_OwnerT]):
        if instance is None:
            return self
        try:
            value = getattr(instance, self._internal_owner_attr_name)
        except AttributeError:
            value = self._new_collection(instance)
            setattr(instance, self._internal_owner_attr_name, value)
            return value
        else:
            assert not isinstance(value, _Resolver)
            return cast(_EntityCollectionT, value)

    def __set__(self, instance: _OwnerT, value: ToManyAssociates[_AssociateT]) -> None:
        if isinstance(value, _Resolver):
            setattr(instance, self._internal_owner_attr_name, value)
        else:
            self.__get__(instance, type(instance)).replace(*value)

    def __delete__(self, instance: _OwnerT) -> None:
        self.__get__(instance, type(instance)).clear()

    @override
    def associate(self, owner: _OwnerT, associate: _AssociateT, /) -> None:
        self.__get__(owner, type(owner)).add(associate)

    @override
    def disassociate(self, owner: _OwnerT, associate: _AssociateT, /) -> None:
        self.__get__(owner, type(owner)).remove(associate)

    @override
    def get_associates(self, owner: _OwnerT, /) -> Iterable[_AssociateT]:
        yield from self.__get__(owner, type(owner))

    @override
    def resolve(self, owner: _OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, _Resolver):
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
        self, project: Project, target: Intersection[_OwnerT, Entity], /
    ) -> PortableData:
        associates = self.__get__(target, type(target))
        if self._linked_data_embedded:
            return [
                await associate.dump_linked_data(project) for associate in associates
            ]
        return list(
            filter(
                None,
                [
                    await _generate_associate_url(project, associate)
                    for associate in associates
                ],
            )
        )


class _BidirectionalAssociation(_Association[_OwnerT, _AssociateT]):
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

    def inverse(self) -> _BidirectionalAssociation[_AssociateT, _OwnerT]:
        """
        Get the inverse association.
        """
        association = AssociationRegistry.get_association(
            self.associate_type, self.associate_attr_name
        )
        assert isinstance(association, _BidirectionalAssociation)
        return association


@final
class BidirectionalToZeroOrOne(
    _ToZeroOrOneAssociation[_OwnerT, _AssociateT],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    r"""
    A bidirectional \\*-to-zero-or-one entity type association.
    """

    @override
    def __set__(
        self, instance: _OwnerT, value: ToZeroOrOneAssociate[_AssociateT]
    ) -> None:
        previous_associate = self.__get__(instance, type(instance))
        if previous_associate == value:
            return
        super().__set__(instance, value)
        if previous_associate is not None:
            self.inverse().disassociate(previous_associate, instance)
        if not isinstance(value, _Resolver) and value is not None:
            self.inverse().associate(value, instance)

    @override
    def resolve(self, owner: _OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, _Resolver):
            associate = value.resolve()
            setattr(owner, self._internal_owner_attr_name, value.resolve())
            if associate:
                self.inverse().associate(associate, owner)


@final
class BidirectionalToOne(
    _ToOneAssociation[_OwnerT, _AssociateT],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    r"""
    A bidirectional \\*-to-one entity type association.
    """

    @override
    def resolve(self, owner: _OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if value is None:
            raise AssociationRequired(self, owner)
        if isinstance(value, _Resolver):
            associate = value.resolve()
            setattr(owner, self._internal_owner_attr_name, associate)
            self.inverse().associate(associate, owner)

    @override
    def __set__(self, instance: _OwnerT, value: ToOneAssociate[_AssociateT]) -> None:
        try:
            previous_associate = cast(
                "_AssociateT | None", getattr(self, self._internal_owner_attr_name)
            )
        except AttributeError:
            previous_associate = None
        if previous_associate == value:
            return
        super().__set__(instance, value)
        if previous_associate:
            self.inverse().disassociate(previous_associate, instance)
        if not isinstance(value, _Resolver):
            self.inverse().associate(value, instance)


@final
class BidirectionalToManySingleType(
    _ToManyAssociation[_OwnerT, _AssociateT, SingleTypeEntityCollection[_AssociateT]],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    r"""
    A bidirectional \\*-to-many entity type association where all associates are of the same entity type.
    """

    @override
    def _new_collection(
        self, instance: _OwnerT, /
    ) -> SingleTypeEntityCollection[_AssociateT]:
        return _BidirectionalSingleTypeAssociateCollection(instance, self)


@final
class BidirectionalToManyMultipleTypes(
    _ToManyAssociation[
        _OwnerT, _AssociateT, MultipleTypesEntityCollection[_AssociateT]
    ],
    _BidirectionalAssociation[_OwnerT, _AssociateT],
):
    r"""
    A bidirectional \\*-to-many entity type association where associates may be of different entity types.
    """

    @override
    def _new_collection(
        self, instance: _OwnerT, /
    ) -> MultipleTypesEntityCollection[_AssociateT]:
        return _BidirectionalMultipleTypesAssociateCollection(
            instance,
            self,
        )


@final
class UnidirectionalToZeroOrOne(_ToZeroOrOneAssociation[_OwnerT, _AssociateT]):
    """
    A unidirectional to-zero-or-one entity type association.
    """

    @override
    def resolve(self, owner: _OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if isinstance(value, _Resolver):
            setattr(owner, self._internal_owner_attr_name, value.resolve())


@final
class UnidirectionalToOne(_ToOneAssociation[_OwnerT, _AssociateT]):
    """
    A unidirectional to-one entity type association.
    """

    @override
    def resolve(self, owner: _OwnerT, /) -> None:
        value = getattr(owner, self._internal_owner_attr_name, None)
        if value is None:
            raise AssociationRequired(self, owner)
        if isinstance(value, _Resolver):
            setattr(owner, self._internal_owner_attr_name, value.resolve())


@final
class UnidirectionalToManySingleType(
    _ToManyAssociation[_OwnerT, _AssociateT, SingleTypeEntityCollection[_AssociateT]]
):
    """
    A unidirectional to-many entity type association where all associates are of the same entity type.
    """

    @override
    def _new_collection(
        self, instance: _OwnerT, /
    ) -> SingleTypeEntityCollection[_AssociateT]:
        return SingleTypeEntityCollection[_AssociateT]()


@final
class UnidirectionalToManyMultipleTypes(
    _ToManyAssociation[
        _OwnerT, _AssociateT, MultipleTypesEntityCollection[_AssociateT]
    ],
):
    """
    A unidirectional to-many entity type association where associates may be of different entity types.
    """

    @override
    def _new_collection(
        self, instance: _OwnerT, /
    ) -> MultipleTypesEntityCollection[_AssociateT]:
        return MultipleTypesEntityCollection[_AssociateT]()


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
    def get_association(
        cls, owner: type[_OwnerT] | _OwnerT, owner_attr_name: str, /
    ) -> _Association[_OwnerT, Any]:
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


class _BidirectionalAssociateCollection(
    EntityCollection[_AssociateT], Generic[_AssociateT, _OwnerT]
):
    def __init__(
        self,
        owner: _OwnerT,
        association: _BidirectionalAssociation[_OwnerT, _AssociateT],
        /,
    ):
        super().__init__()
        self._association = association
        self.__owner = weakref.ref(owner)

    @property
    def _owner(self) -> _OwnerT:
        owner = self.__owner()
        assert owner is not None, (
            "This associate collection's owner no longer exists in memory."
        )
        return owner

    @override
    def _on_add(self, *entities: _AssociateT) -> None:
        super()._on_add(*entities)
        for associate in entities:
            self._association.inverse().associate(associate, self._owner)

    @override
    def _on_remove(self, *entities: _AssociateT) -> None:
        super()._on_remove(*entities)
        for associate in entities:
            self._association.inverse().disassociate(associate, self._owner)


class _BidirectionalSingleTypeAssociateCollection(
    _BidirectionalAssociateCollection[_AssociateT, _OwnerT],
    SingleTypeEntityCollection[_AssociateT],
):
    pass


class _BidirectionalMultipleTypesAssociateCollection(
    _BidirectionalAssociateCollection[_AssociateT, _OwnerT],
    MultipleTypesEntityCollection[_AssociateT],
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


ToOneAssociate: TypeAlias = _EntityT | ToOneResolver[_EntityT]
ToZeroOrOneAssociate: TypeAlias = (
    ToOneAssociate[_EntityT] | ToZeroOrOneResolver[_EntityT] | None
)
ToManyAssociates: TypeAlias = Iterable[_EntityT] | ToManyResolver[_EntityT]
