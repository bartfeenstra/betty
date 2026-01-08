from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence
from enum import Enum
from typing import Any, Generic

import pytest
from typing_extensions import TypeVar

from betty.data import (
    AggregateDefinition,
    BoolDefinition,
    CollectionDefinition,
    DataDefinition,
    EnumDefinition,
    FloatDefinition,
    IntDefinition,
    MappingDefinition,
    RecordDefinition,
    SequenceDefinition,
    SimpleDefinition,
    StrDefinition,
)
from betty.data.indicator import Attr, Index, Key
from betty.locale.localizable.plain import Plain
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

_DataDefinitionT = TypeVar("_DataDefinitionT", bound=DataDefinition[Any, Any])
_AggregateDefinitionT = TypeVar(
    "_AggregateDefinitionT",
    bound=AggregateDefinition[Any, Any, Any, Any, Any, Any],
)
_RecordDefinitionT = TypeVar("_RecordDefinitionT", bound=RecordDefinition[Any])
_CollectionDefinitionT = TypeVar(
    "_CollectionDefinitionT", bound=CollectionDefinition[Any, Any, Any, Any, Any, Any]
)
_MappingDefinitionT = TypeVar(
    "_MappingDefinitionT", bound=MappingDefinition[Any, Any, Any, Any]
)
_SequenceDefinitionT = TypeVar(
    "_SequenceDefinitionT", bound=SequenceDefinition[Any, Any, Any, Any]
)
_DataT = TypeVar("_DataT")
_DataSetT = TypeVar("_DataSetT")
_MutableMappingT = TypeVar("_MutableMappingT", bound=MutableMapping[str, Any])
_MutableMappingSetT = TypeVar("_MutableMappingSetT", bound=MutableMapping[str, Any])
_MutableSequenceT = TypeVar("_MutableSequenceT", bound=MutableSequence[Any])
_MutableSequenceSetT = TypeVar("_MutableSequenceSetT", bound=MutableSequence[Any])


# @todo Do we need this still?
class DataDefinitionTestBase(Generic[_DataDefinitionT, _DataSetT]):
    pass


class TestBoolDefinition(DataDefinitionTestBase[BoolDefinition, bool]):
    pass


# @todo Do we need this still?
class AggregateDefinitionTestBase(
    DataDefinitionTestBase[_AggregateDefinitionT, _DataSetT]
):
    pass


# @todo Do we need this still?
class CollectionDefinitionTestBase(
    AggregateDefinitionTestBase[_CollectionDefinitionT, _DataSetT]
):
    pass


class TestSequenceDefinition(
    CollectionDefinitionTestBase[
        SequenceDefinition[list[bool], list[bool], bool, bool],
        list[bool],
    ]
):
    def test_elements__should_contain_exactly_one_element(self) -> None:
        sut = SequenceDefinition[list[bool], list[bool], bool, bool](
            cls=list[bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert len(list(sut.elements)) == 1

    def test_get(self) -> None:
        sut = SequenceDefinition[list[bool], list[bool], bool, bool](
            cls=list[bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        value = True
        data = [value]
        assert sut.get(data, Index(0)) == value

    def test_get__with_index_error(self) -> None:
        sut = SequenceDefinition[list[bool], list[bool], bool, bool](
            cls=list[bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        data: list[bool] = []
        with pytest.raises(IndexError):
            sut.get(data, Index(0))

    def test_set(self) -> None:
        sut = SequenceDefinition[list[bool], list[bool], bool, bool](
            cls=list[bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        value = True
        data: list[bool] = []
        sut.set(data, Index(0), value)
        assert data[0] == value

    def test_delete(self) -> None:
        sut = SequenceDefinition[list[bool], list[bool], bool, bool](
            cls=list[bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        value = True
        data = [value]
        sut.delete(data, Index(0))
        assert not data


class TestDataDefinition(DataDefinitionTestBase[DataDefinition[Any, Any], Any]):
    def test_cls(self) -> None:
        cls = object
        sut = DataDefinition[object, object](cls=cls, label=DUMMY_LOCALIZABLE)
        assert sut.cls is cls

    def test_label(self) -> None:
        label = Plain("-")
        sut = DataDefinition[object, object](cls=object, label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = Plain("-")
        sut = DataDefinition[object, object](
            cls=object, label=DUMMY_LOCALIZABLE, description=description
        )
        assert sut.description is description

    def test_transform__without_transformer(self) -> None:
        sut = DataDefinition[object, object](cls=object, label=DUMMY_LOCALIZABLE)
        data = object()
        assert sut.transform(data) is data

    def test_transform__with_transformer(self) -> None:
        transformed_data = object()
        sut = DataDefinition[object, object](
            cls=object, label=DUMMY_LOCALIZABLE, transformer=lambda _: transformed_data
        )
        assert sut.transform(object()) is transformed_data


class EnumDefinitionData(Enum):
    pass


class TestEnumDefinition(
    DataDefinitionTestBase[EnumDefinition[EnumDefinitionData], Any]
):
    pass


class TestFloatDefinition(DataDefinitionTestBase[FloatDefinition, Any]):
    pass


class TestIntDefinition(DataDefinitionTestBase[IntDefinition, Any]):
    pass


class TestMappingDefinition(
    CollectionDefinitionTestBase[
        MappingDefinition[dict[str, bool], dict[str, bool], bool, bool], dict[str, bool]
    ]
):
    def test_elements__should_contain_exactly_one_element(self) -> None:
        sut = MappingDefinition[dict[str, bool], dict[str, bool], bool, bool](
            cls=dict[str, bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert len(list(sut.elements)) == 1

    def test_get(self) -> None:
        sut = MappingDefinition[dict[str, bool], dict[str, bool], bool, bool](
            cls=dict[str, bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        key = "kEy"
        value = True
        data = {key: value}
        assert sut.get(data, Key(key)) == value

    def test_get__with_key_error(self) -> None:
        sut = MappingDefinition[dict[str, bool], dict[str, bool], bool, bool](
            cls=dict[str, bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        data: dict[str, bool] = {}
        with pytest.raises(KeyError):
            sut.get(data, Key("kEy"))

    def test_set(self) -> None:
        sut = MappingDefinition[dict[str, bool], dict[str, bool], bool, bool](
            cls=dict[str, bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        key = "kEy"
        value = True
        data: dict[str, bool] = {}
        sut.set(data, Key(key), value)
        assert data[key] == value

    def test_delete(self) -> None:
        sut = MappingDefinition[dict[str, bool], dict[str, bool], bool, bool](
            cls=dict[str, bool],
            item=BoolDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        key = "kEy"
        value = True
        data = {key: value}
        sut.delete(data, Key("kEy"))
        assert key not in data


# @todo Do we need this still?
class RecordDefinitionTestBase(
    AggregateDefinitionTestBase[_RecordDefinitionT, _DataSetT]
):
    pass


class RecordDefinitionTestRecord:
    my_first_attr: str


class TestRecordDefinition(RecordDefinitionTestBase[RecordDefinition[Any], Any]):
    attr_name = "my_first_attr"
    attr_data = StrDefinition(label=DUMMY_LOCALIZABLE)
    sut = RecordDefinition[RecordDefinitionTestRecord](
        cls=RecordDefinitionTestRecord,
        label=DUMMY_LOCALIZABLE,
        attrs={
            attr_name: attr_data,
        },
    )

    def test_get(self) -> None:
        value = "Hello, world!"
        data = RecordDefinitionTestRecord()
        data.my_first_attr = value
        assert self.sut.get(data, Attr(self.attr_name)) == value

    def test_set(self) -> None:
        value = "Hello, world!"
        data = RecordDefinitionTestRecord()
        self.sut.set(data, Attr(self.attr_name), value)
        assert data.my_first_attr == value

    def test_delete(self) -> None:
        value = "Hello, world!"
        data = RecordDefinitionTestRecord()
        data.my_first_attr = value
        self.sut.delete(data, Attr(self.attr_name))
        with pytest.raises(AttributeError):
            data.my_first_attr  # noqa B018

    def test_elements(self) -> None:
        assert list(self.sut.elements)[0][1] is self.attr_data


class TestSimpleDefinition(DataDefinitionTestBase[SimpleDefinition[Any, Any], Any]):
    pass


class TestStrDefinition(DataDefinitionTestBase[StrDefinition, Any]):
    pass
