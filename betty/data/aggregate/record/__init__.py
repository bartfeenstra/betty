"""
Record data types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, final

from typing_extensions import override

from betty.assertion import OptionalField
from betty.data import DataDefinition
from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Element
from betty.locale.localizable.ensure import ensure_localizable
from betty.portable import Loader, PortableData, PortableMapping, Porter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from betty.data import Data, Sample
    from betty.locale.localizable import Localizable, LocalizableLike

_DataClsT = TypeVar("_DataClsT")
_ElementT = TypeVar("_ElementT", bound=Element[Any])


@final
class FieldDefinition(Generic[_ElementT, _DataClsT]):
    """
    A record field definition.
    """

    def __init__(
        self,
        selector: _ElementT,
        data: DataDefinition[_DataClsT] | Data[DataDefinition[_DataClsT]],
        *,
        label: LocalizableLike | None = None,
        description: LocalizableLike | None = None,
        required: bool = True,
        empty: Callable[[_DataClsT], bool] | None = None,
    ):
        self._selector = selector
        self._data = data if isinstance(data, DataDefinition) else data.data()
        self._label = None if label is None else ensure_localizable(label)
        self._description = (
            None if description is None else ensure_localizable(description)
        )
        self._required = required
        self._empty = empty

    @property
    def selector(self) -> Element:
        """
        The field selector.
        """
        return self._selector

    @property
    def data(self) -> DataDefinition:
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
    def required(self) -> bool:
        """
        Whether the field is required.
        """
        return self._required

    def empty(self, data: _DataClsT) -> bool:
        """
        Check if the data can be considered 'empty'.
        """
        if self._empty is None:
            return self.data.empty(data)
        return self._empty(data)


class _RecordPorter(Porter[_DataClsT]):
    def __init__(
        self,
        loader: Loader[_DataClsT],
        dumper: Callable[[_DataClsT], PortableMapping],
        /,
    ):
        self._loader = loader
        self._dumper = dumper

    @override
    def load(self, portable: PortableData) -> _DataClsT:
        return self._loader(portable)

    @override
    def dump(self, data: _DataClsT) -> PortableMapping:
        return self._dumper(data)


class RecordDefinition(AggregateDefinition[_DataClsT, _ElementT]):
    """
    A record data definition.

    Records have explicitly defined fields.
    """

    _porter: _RecordPorter[_DataClsT]

    def __init__(
        self,
        *,
        cls: type[_DataClsT] | None = None,
        label: LocalizableLike,
        fields: Sequence[FieldDefinition[_ElementT, Any]],
        description: LocalizableLike | None = None,
        samples: Iterable[Callable[[], Sample[_DataClsT]]] | None = None,
        factory: Callable[..., _DataClsT] | None = None,
    ):
        super().__init__(
            cls=cls,
            label=label,
            description=description,
            samples=samples,
            porter=_RecordPorter(self._load, self._dump),
        )
        self._factory = factory
        self._fields = fields

    @property
    def fields(self) -> Sequence[FieldDefinition[_ElementT, Any]]:
        """
        The definitions of the fields contained by this record.
        """
        return self._fields

    @override
    def elements(self, data: _DataClsT) -> Sequence[tuple[_ElementT, DataDefinition]]:
        return [(field.selector, field.data) for field in self.fields]  # ty:ignore[invalid-return-type]

    def _load(self, portable: PortableData, /) -> _DataClsT:
        from betty.assertion import RequiredField, assert_record

        factory = self.cls if not self._factory else self._factory
        return factory(
            **assert_record(
                *[
                    (RequiredField if field.required else OptionalField)(
                        field.selector.element, field.data.load
                    )
                    for field in self._fields
                ]
            )(portable)
        )

    def _dump(self, data: _DataClsT) -> PortableMapping:
        portable = {}
        for field in self.fields:
            field_data = field.selector.get(data)
            if not field.empty(field_data):
                portable[field.selector.element] = field.data.dump(field_data)
        return portable

    def load_key(
        self, portable: PortableData, key: _ElementT, portable_key: str, /
    ) -> _DataClsT:
        """
        Create a new data instance from portable data and a portable primary key.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """
        return self._porter.load({**portable, key.element: portable_key})

    def dump_key(self, data: _DataClsT, key: _ElementT, /) -> tuple[str, PortableData]:
        """
        Dump the data to portable data and a portable primary key.
        """
        portable = self._porter.dump(data)
        portable_key = portable.pop(key.element)
        assert isinstance(portable_key, str)
        return portable_key, portable
