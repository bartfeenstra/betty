"""
Record data types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, final

from typing_extensions import TypeVar, override

from betty.assertion import OptionalField
from betty.data import DataDefinition, OptionalDefinition, Sample, Samples
from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Element
from betty.locale.localizable.ensure import ensure_localizable
from betty.portable.error import NotPortable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, MutableSequence, Sequence

    from betty.data import Data
    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.portable import PortableData, PortableMapping

_DataClsT = TypeVar("_DataClsT")
_ElementCoT = TypeVar("_ElementCoT", bound=Element[Any], covariant=True)


@final
class FieldDefinition(Generic[_ElementCoT, _DataClsT]):
    """
    A record field definition.
    """

    def __init__(
        self,
        selector: _ElementCoT,
        data: DataDefinition[_DataClsT] | Data[DataDefinition[_DataClsT]],
        *,
        label: LocalizableLike | None = None,
        description: LocalizableLike | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[_DataClsT], bool] | None = None,
    ):
        self._selector = selector
        self._data = data if isinstance(data, DataDefinition) else data.data()
        self._label = None if label is None else ensure_localizable(label)
        self._description = (
            None if description is None else ensure_localizable(description)
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
    def data(self) -> DataDefinition[_DataClsT]:
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

    def omit_dump(self, data: _DataClsT, /) -> bool:
        """
        Check if the field may be omitted from the parent when dumping to portable data.
        """
        if data is None and isinstance(self._data, OptionalDefinition):
            return True
        if self._omit_dump is None:
            return False
        return self._omit_dump(data)


class RecordPorter(ABC, Generic[_DataClsT]):
    """
    An object capable of dumping and loading data to and from portable data.
    """

    @abstractmethod
    def load(self, portable: PortableData, /) -> _DataClsT:
        """
        Load data from its portable form.
        """

    @abstractmethod
    def dump(self, data: _DataClsT, /) -> PortableData:
        """
        Dump data to its portable form.
        """

    @abstractmethod
    def load_key(
        self, portable: PortableData, key: _ElementCoT, portable_key: str, /
    ) -> _DataClsT:
        """
        Create a new data instance from portable data and a portable primary key.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """

    @abstractmethod
    def dump_key(
        self, data: _DataClsT, key: _ElementCoT, /
    ) -> tuple[str, PortableData]:
        """
        Dump the data to portable data and a portable primary key.
        """


@final
class MappingPorter(RecordPorter[_DataClsT]):
    """
    Load and dump a record from and to portable mappings.
    """

    def __init__(self, record: RecordDefinition[_DataClsT, Element[str]], /):
        self._record = record

    @override
    def load(self, portable: PortableData, /) -> _DataClsT:
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
    def dump(self, data: _DataClsT, /) -> PortableMapping:
        portable = {}
        for field in self._record.fields:
            field_data = field.selector.get(data)
            if not field.omit_dump(field_data):
                portable[field.selector.element] = field.data.porter.dump(field_data)
        return portable

    @override
    def load_key(
        self, portable: PortableData, key: _ElementCoT, portable_key: str, /
    ) -> _DataClsT:
        return self.load({**portable, key.element: portable_key})

    @override
    def dump_key(
        self, data: _DataClsT, key: _ElementCoT, /
    ) -> tuple[str, PortableMapping]:
        portable = self.dump(data)
        portable_key = portable.pop(key.element)
        assert isinstance(portable_key, str)
        return portable_key, portable


class RecordDefinition(AggregateDefinition[_DataClsT, _ElementCoT]):
    """
    A record data definition.

    Records have explicitly defined fields.
    """

    def __init__(
        self,
        *,
        cls: type[_DataClsT] | None = None,
        label: LocalizableLike,
        fields: Sequence[FieldDefinition[_ElementCoT, Any]] | None = None,
        description: LocalizableLike | None = None,
        samples: Iterable[Callable[[], Sample[_DataClsT]] | Samples] | None = None,
        factory: Callable[..., _DataClsT] | None = None,
        porter: RecordPorter[_DataClsT] | None = None,
    ):
        super().__init__(
            cls=cls,
            label=label,
            description=description,
            samples=samples,
            porter=porter,
        )
        self._factory = factory
        self._fields: MutableSequence[FieldDefinition[_ElementCoT, Any]] = (
            [] if fields is None else list(fields)
        )

    @property
    def factory(self) -> Callable[..., _DataClsT]:
        """
        The factory to create new instances.

        The factory's arguments are kwargs whose names are this record's field names, and whose values are their fully
        typed values.
        """
        return self.cls if self._factory is None else self._factory

    @override
    @property
    def porter(self) -> RecordPorter[_DataClsT]:
        try:
            return super().porter
        except NotPortable:
            self._porter = MappingPorter(self)
            return self._porter

    @property
    def fields(self) -> Sequence[FieldDefinition[_ElementCoT, Any]]:
        """
        The definitions of the fields contained by this record.
        """
        return self._fields

    def field(self, selector: _ElementCoT) -> FieldDefinition[_ElementCoT, Any]:
        """
        Get the field definition for the given selector.
        """
        for field in self.fields:
            if field.selector == selector:
                return field
        raise ValueError(f"Field {selector} not found")

    @override
    def elements(self, data: _DataClsT) -> Sequence[tuple[_ElementCoT, DataDefinition]]:
        return [(field.selector, field.data) for field in self.fields]  # ty:ignore[invalid-return-type]
