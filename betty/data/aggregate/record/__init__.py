"""
Record data types.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, final, override

from betty.assertion import OptionalField, assert_mapping
from betty.data import DataDefinition, OptionalDefinition, Sample, Samples
from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Element
from betty.locale.localizable import resolve_localizable
from betty.portable import Portable, PortableData, PortablePorter, Porter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, MutableSequence, Sequence

    from betty.data import Data
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.portable import PortableMapping


@final
class FieldDefinition[ElementT: Element[Any] = Element[Any], DataClsT = Any]:
    """
    A record field definition.
    """

    def __init__(
        self,
        selector: ElementT,
        data: DataDefinition[DataClsT] | type[Data[DataDefinition[DataClsT]]],
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[DataClsT], bool] | None = None,
    ):
        self._selector = selector
        self._data = data if isinstance(data, DataDefinition) else data.data()
        self._label = None if label is None else resolve_localizable(label)
        self._description = (
            None if description is None else resolve_localizable(description)
        )
        self._omit_load = omit_load
        self._omit_dump = omit_dump

    @property
    def selector(self) -> Element:
        """
        The field selector.
        """
        return self._selector

    @property
    def data(self) -> DataDefinition[DataClsT]:
        """
        The field's data definition.
        """
        return self._data

    @property
    def label(self) -> Localizable | None:
        """
        The human-readable field label.
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The human-readable long field description.
        """
        return self._description

    @property
    def omit_load(self) -> bool:
        """
        Check if the field may be omitted from the parent when loading from portable data.
        """
        if self._omit_load is not None:
            return self._omit_load
        return isinstance(self._data, OptionalDefinition)

    def omit_dump(self, data: DataClsT, /) -> bool:
        """
        Check if the field may be omitted from the parent when dumping to portable data.
        """
        if data is None and isinstance(self._data, OptionalDefinition):
            return True
        if self._omit_dump is None:
            return False
        return self._omit_dump(data)


_PortableRecordElementT = TypeVar(
    "_PortableRecordElementT", bound=Element[str], default=Element[str], covariant=True
)


class PortableRecord(Portable, Generic[_PortableRecordElementT]):
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


class RecordPorter[DataClsT = Any, ElementT: Element[str] = Element[str]](
    Porter[DataClsT]
):
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


@final
class PortableRecordPorter[
    PortableRecordT: PortableRecord,
    ElementT: Element[str] = Element[str],
](PortablePorter[PortableRecordT], RecordPorter[PortableRecordT, ElementT]):
    """
    Expose a portable record data type as a porter.
    """

    @override
    def load_key(
        self, portable: PortableData, key: ElementT, portable_key: str, /
    ) -> PortableRecordT:
        return self._cls.load_key(portable, key, portable_key)

    @override
    def dump_key(
        self, data: PortableRecordT, key: ElementT, /
    ) -> tuple[str, PortableData]:
        return data.dump_key(key)


@final
class MappingPorter[DataClsT = Any, ElementT: Element[str] = Element[str]](
    RecordPorter[DataClsT]
):
    """
    Load and dump a record from and to portable mappings.
    """

    def __init__(self, record: RecordDefinition[DataClsT, ElementT], /):
        self._record = record

    @override
    def load(self, portable: PortableData, /) -> DataClsT:
        from betty.assertion import RequiredField, assert_record

        return self._record.factory(
            **assert_record(
                *[
                    (OptionalField if field.omit_load else RequiredField)(
                        field.selector.element, field.data.porter.load
                    )
                    for field in self._record.fields
                ]
            )(portable)
        )

    @override
    def dump(self, data: DataClsT, /) -> PortableMapping:
        portable = {}
        for field in self._record.fields:
            field_data = field.selector.get(data)
            if not field.omit_dump(field_data):
                portable[field.selector.element] = field.data.porter.dump(field_data)
        return portable

    @override
    def load_key(
        self,
        portable: PortableData,
        key: ElementT,
        portable_key: str,
        /,
    ) -> DataClsT:  # ty:ignore[invalid-method-override]
        return self.load({**assert_mapping()(portable), key.element: portable_key})

    @override
    def dump_key(
        self,
        data: DataClsT,
        key: ElementT,
        /,
    ) -> tuple[str, PortableData]:  # ty:ignore[invalid-method-override]
        portable = self.dump(data)
        portable_key = portable.pop(key.element)
        assert isinstance(portable_key, str)
        return portable_key, portable


class RecordDefinition[DataClsT = Any, ElementT: Element[str] = Element[str]](
    AggregateDefinition[DataClsT, ElementT]
):
    """
    A record data definition.

    Records have explicitly defined fields.
    """

    _porter: RecordPorter[DataClsT] | None

    def __init__(
        self,
        *,
        cls: type[DataClsT] | None = None,
        label: ResolvableLocalizable,
        fields: Sequence[FieldDefinition[ElementT, Any]] | None = None,
        description: ResolvableLocalizable | None = None,
        samples: Iterable[Callable[[], Sample[DataClsT]] | Samples] | None = None,
        factory: Callable[..., DataClsT] | None = None,
        porter: RecordPorter[DataClsT] | None = None,
    ):
        super().__init__(
            cls=cls,
            label=label,
            description=description,
            samples=samples,
            porter=porter,
        )
        self._factory = factory
        self._fields: MutableSequence[FieldDefinition[ElementT, Any]] = (
            [] if fields is None else list(fields)
        )

    @property
    def factory(self) -> Callable[..., DataClsT]:
        """
        The factory to create new instances.

        The factory's arguments are kwargs whose names are this record's field names, and whose values are their fully
        typed values.
        """
        return self.cls if self._factory is None else self._factory

    @override
    @property
    def porter(self) -> RecordPorter[DataClsT]:
        if self._porter is None:
            if issubclass(self.cls, PortableRecord):
                self._porter = PortableRecordPorter(self.cls)
            else:
                self._porter = MappingPorter(
                    self,  # ty:ignore[invalid-argument-type]
                )
        return self._porter

    @property
    def fields(self) -> Sequence[FieldDefinition[ElementT, Any]]:
        """
        The definitions of the fields contained by this record.
        """
        return self._fields

    @override
    def elements(self, data: DataClsT) -> Sequence[tuple[ElementT, DataDefinition]]:
        return [(field.selector, field.data) for field in self.fields]  # ty:ignore[invalid-return-type]
