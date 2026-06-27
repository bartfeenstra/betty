"""
Record data types.
"""

from __future__ import annotations

from abc import abstractmethod
from inspect import signature
from typing import TYPE_CHECKING, Any, Final, Generic, Self, TypeVar, final, override

from betty.data import (
    DataDefinition,
    ResolvableDataDefinition,
    Sample,
    Samples,
    resolve_data_definition,
)
from betty.datas.aggregate import AggregateDefinition
from betty.indicator.selector import Element
from betty.localizable import resolve_localizable
from betty.portable import Portable, PortableData, Porter
from betty.privacy import HasPrivacy, Privacy
from betty.privacy.resolve import merge_privacies, negotiate_privacies

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, MutableMapping

    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.typing import Intersection


@final
class FieldDefinition[
    OwnerT,
    DataClsT,
    DataDefinitionT: DataDefinition = DataDefinition,
]:
    """
    A record field definition.
    """

    def __init__(
        self,
        data: ResolvableDataDefinition[
            Intersection[DataDefinitionT, DataDefinition[DataClsT]]
        ],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool = False,
        omit_dump: Callable[[DataClsT], bool]
        | Callable[[OwnerT, DataClsT], bool]
        | None = None,
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        self.data: Final[DataDefinitionT] = resolve_data_definition(data)
        """
        The field's data definition.
        """

        self.label: Final[Localizable] = (
            self.data.label if label is None else resolve_localizable(label)
        )
        """
        The human-readable field label.
        """

        self.description: Final[Localizable | None] = (
            self.data.description
            if description is None
            else resolve_localizable(description)
        )
        """
        The human-readable long field description.
        """

        self.omit_load: Final[bool] = omit_load
        """
        Whether the field may be omitted from the parent when loading from portable data.
        """

        self._omit_dump: Callable[[OwnerT, DataClsT], bool] | None = (
            None
            if omit_dump is None
            else (
                (
                    lambda _, data: omit_dump(
                        data,  # ty:ignore[invalid-argument-type]
                    )  # ty:ignore[missing-argument]
                )
                if len(signature(omit_dump).parameters) == 1
                else omit_dump
            )  # ty:ignore[invalid-assignment]
        )

        self._privacy: Final[Privacy] = privacy

    def omit_dump(self, owner: OwnerT, data: DataClsT, /) -> bool:
        """
        Check if the field may be omitted from the parent when dumping to portable data.
        """
        if self._omit_dump is None:
            return False
        return self._omit_dump(owner, data)

    def privacy(self, owner: OwnerT, data: DataClsT, /) -> Privacy:
        """
        Get the field data's effective privacy.
        """
        # @todo - if field def is public -> public
        # @todo - if field def is private -> private
        # @todo - if owner is private -> private
        # @todo - if data def is private -> private
        # @todo - if data is private -> private
        # @todo - ELSE -> merge privacies
        # @todo
        # @todo HOWEVER...
        # @todo - if field def is public and owner is private -> public
        # @todo
        # @todo
        # @todo
        # @todo
        privacy = self.data.privacy(data)
        if isinstance(owner, HasPrivacy):
            privacy = merge_privacies(privacy, owner)
        return negotiate_privacies(self._privacy, privacy)


_PortableRecordElementT = TypeVar(
    "_PortableRecordElementT", bound=Element[str], default=Element[str], covariant=True
)


class PortableRecord(
    Portable,
    Generic[_PortableRecordElementT],  # noqa: UP046
):
    """
    A record object capable of dumping and loading itself to and from portable data.
    """

    @classmethod
    @abstractmethod
    def load_key(
        cls, portable: PortableData, key: _PortableRecordElementT, portable_key: str, /
    ) -> Self:
        """
        Create a new instance from portable data and a portable primary key.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """

    @abstractmethod
    def dump_key(self, key: _PortableRecordElementT, /) -> tuple[str, PortableData]:
        """
        Dump the instance to portable data and a portable primary key.

        :raises betty.portable.error.NotPortable: Raised if any part of the data is not portable.
        """


class RecordPorter[DataClsT, ElementT: Element[str] = Element[str]](Porter[DataClsT]):
    """
    An object capable of dumping and loading record data to and from portable data.
    """

    @abstractmethod
    def load_key(
        self, portable: PortableData, key: ElementT, portable_key: str, /
    ) -> DataClsT:
        """
        Create a new data instance from portable data and a portable primary key.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """

    @abstractmethod
    def dump_key(self, data: DataClsT, key: ElementT, /) -> tuple[str, PortableData]:
        """
        Dump the data to portable data and a portable primary key.
        """


class RecordDefinition[DataClsT, ElementT: Element[str] = Element[str]](
    AggregateDefinition[DataClsT, ElementT]
):
    """
    A record data definition.

    Records have explicitly defined fields.
    """

    _porter: RecordPorter[DataClsT] | None

    def __init__(
        self,
        *args: Any,
        cls: type[DataClsT] | None = None,
        label: ResolvableLocalizable,
        fields: Mapping[ElementT, FieldDefinition[DataClsT, Any]] | None = None,
        description: ResolvableLocalizable | None = None,
        samples: Iterable[Callable[[], Sample[DataClsT]] | Samples] = (),
        factory: Callable[..., DataClsT] | None = None,
        porter: RecordPorter[DataClsT] | None = None,
        **kwargs: Any,
    ):
        self._fields: MutableMapping[ElementT, FieldDefinition[DataClsT, Any]] = (
            {} if fields is None else dict(fields)
        )
        super().__init__(
            *args,
            cls=cls,
            label=label,
            description=description,
            samples=samples,
            porter=porter,
            **kwargs,
        )
        self._factory = factory

    @property
    def factory(self) -> Callable[..., DataClsT]:
        """
        The factory to create new instances.

        The factory's arguments are kwargs whose names are this record's field names, and whose values are their fully
        typed values.
        """
        if self._factory:
            return self._factory
        if self.cls:
            return self.cls
        raise ValueError(
            "This definition does not have a factory. Either set a data class, or provide a factory when initializing the definition."
        )

    @override
    @property
    def porter(self) -> RecordPorter[DataClsT]:
        from betty.porters.portable_record import PortableRecordPorter
        from betty.porters.record_mapping import RecordMappingPorter

        if self._porter is None:
            if self.cls and issubclass(self.cls, PortableRecord):
                self._porter = PortableRecordPorter(self.cls)  # ty:ignore[invalid-assignment]
            else:
                self._porter = RecordMappingPorter(  # ty:ignore[invalid-assignment]
                    self,  # ty:ignore[invalid-argument-type]
                )
        return self._porter  # ty:ignore[invalid-return-type]

    @property
    def fields(self) -> Mapping[ElementT, FieldDefinition[DataClsT, Any]]:
        """
        The definitions of the fields contained by this record.
        """
        return self._fields
