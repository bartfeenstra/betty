"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping, MutableMapping, MutableSequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, cast, final

from typing_extensions import TypeVar, override

from betty.data.indicator import AnyIndex, AnyKey, Attr, Index, Indicator, Key, Selector
from betty.locale.localizable.ensure import ensure_localizable

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.locale.localizable import Localizable, LocalizableLike


_DataT = TypeVar("_DataT")
_DataSetT = TypeVar("_DataSetT")
_DataItemT = TypeVar("_DataItemT")
_DataItemSetT = TypeVar("_DataItemSetT")
_EnumT = TypeVar("_EnumT", bound=Enum)
_MutableMappingGetT = TypeVar("_MutableMappingGetT", bound=MutableMapping[str, Any])
_MutableMappingSetT = TypeVar("_MutableMappingSetT", bound=MutableMapping[str, Any])
_MutableSequenceGetT = TypeVar("_MutableSequenceGetT", bound=MutableSequence[Any])
_MutableSequenceSetT = TypeVar("_MutableSequenceSetT", bound=MutableSequence[Any])
_IndicatorT = TypeVar("_IndicatorT", bound=Indicator)
_SelectorT = TypeVar("_SelectorT", bound=Selector)


class DataDefinition(Generic[_DataT, _DataSetT]):
    """
    A data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_DataT],
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        self._cls = cls
        self._label = ensure_localizable(label)
        self._description = (
            None if description is None else ensure_localizable(description)
        )

    @property
    def cls(self) -> type[_DataT]:
        """
        The data's Python type.
        """
        return self._cls

    @property
    def label(self) -> Localizable:
        """
        The human-readable data label.
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The human-readable long data description.
        """
        return self._description


class AggregateDefinition(
    DataDefinition[_DataT, _DataSetT],
    Generic[_DataT, _DataSetT, _DataItemT, _DataItemSetT, _IndicatorT, _SelectorT],
):
    """
    An aggregate data definition.

    Aggregate data is data that consists of other elements that may themselves be simple or aggregate data.
    """

    @property
    @abstractmethod
    def elements(self) -> Iterable[tuple[_IndicatorT, DataDefinition[Any, Any]]]:
        """
        The data definitions of the elements contained by this aggregate type.
        """

    @abstractmethod
    def get(self, data: _DataT, selector: _SelectorT, /) -> _DataItemT:
        """
        Get the value for contained data.
        """


@final
class RecordDefinition(AggregateDefinition[_DataT, _DataT, Any, Any, Attr, Attr]):
    """
    A record data definition.

    Records have explicitly defined attributes. Use them to define classed objects.
    """

    def __init__(
        self,
        *,
        cls: type[_DataT],
        label: LocalizableLike,
        attrs: Mapping[str, DataDefinition[Any, Any]],
        description: LocalizableLike | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description)
        self._attrs = attrs

    @override
    @property
    def elements(self) -> Iterable[tuple[Attr, DataDefinition[Any, Any]]]:
        for attr_name, attr_data in self._attrs.items():
            yield Attr(attr_name), attr_data

    @override
    def get(self, data: _DataT, attr: Attr, /) -> Any:
        return getattr(data, attr.attr)


class CollectionDefinition(
    AggregateDefinition[
        _DataT,
        _DataSetT,
        _DataItemT,
        _DataItemSetT,
        _IndicatorT,
        _SelectorT,
    ]
):
    """
    A homogenous collection data definition.
    """

    _item_indicator: _IndicatorT

    def __init__(
        self,
        *,
        cls: type[_DataT],
        item: DataDefinition[_DataItemT, _DataItemSetT],
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description)
        self._item = item

    @override
    @property
    def elements(self) -> Iterable[tuple[_IndicatorT, DataDefinition[Any, Any]]]:
        return ((self._item_indicator, self._item),)


@final
class MappingDefinition(
    CollectionDefinition[
        _MutableMappingGetT, _MutableMappingSetT, _DataItemT, _DataItemSetT, AnyKey, Key
    ]
):
    """
    A key-value mapping data definition.
    """

    _item_indicator = AnyKey()

    @override
    def get(self, data: _MutableMappingGetT, key: Key, /) -> _DataItemT:
        return cast(_DataItemT, data[key.item])


@final
class SequenceDefinition(
    CollectionDefinition[
        _MutableSequenceGetT,
        _MutableSequenceSetT,
        _DataItemT,
        _DataItemSetT,
        AnyIndex,
        Index,
    ]
):
    """
    A sequence data definition.
    """

    _item_indicator = AnyIndex()

    @override
    def get(self, data: _MutableSequenceGetT, index: Index, /) -> _DataItemT:
        return cast(_DataItemT, data[index.item])


class SimpleDefinition(DataDefinition[_DataT, _DataSetT]):
    """
    A simple (scalar) data definition.
    """

    _cls: type[_DataT]

    def __init__(
        self, *, label: LocalizableLike, description: LocalizableLike | None = None
    ):
        super().__init__(cls=self._cls, label=label, description=description)


class _NumberDefinition(SimpleDefinition[_DataT, _DataSetT]):
    pass


@final
class IntDefinition(_NumberDefinition[int, int]):
    """
    An integer data definition.
    """

    _cls = int


@final
class FloatDefinition(_NumberDefinition[float, float]):
    """
    A floating-point number data definition.
    """

    _cls = float


@final
class StrDefinition(SimpleDefinition[str, str]):
    """
    A string data definition.
    """

    _cls = str


@final
class BoolDefinition(SimpleDefinition[bool, bool]):
    """
    A boolean data definition.
    """

    _cls = bool


@final
class EnumDefinition(DataDefinition[_EnumT, _EnumT]):
    """
    An enum data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_EnumT],
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description)
