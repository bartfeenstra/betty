from collections.abc import Mapping

import pytest

from betty.data import DataDefinition
from betty.datas.aggregate.collection.mapping import (
    MappingDefinition,
    MutableMappingDefinition,
)
from betty.datas.str import StrDefinition
from betty.portable.error import NotPortable


class TestMappingDefinition:
    def test_item(self) -> None:
        key = StrDefinition(label="-")
        sut = MappingDefinition[dict[str, str], str, str](
            key=key, value=StrDefinition(label="-"), label="-"
        )
        assert sut.item is key

    def test_load__without_items(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            manufacturer=lambda values: dict(values) if values else {},
            key=StrDefinition(label="-"),
            value=StrDefinition(label="-"),
            label="-",
        )
        assert sut.porter.load({}) == {}

    def test_load__with_items(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            manufacturer=lambda values: dict(values) if values else {},
            key=StrDefinition(label="-"),
            value=StrDefinition(label="-"),
            label="-",
        )
        assert sut.porter.load({"hello": "Hello, world!"}) == {"hello": "Hello, world!"}

    def test_load__with_item_without_porter(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            manufacturer=lambda values: dict(values) if values else {},
            key=StrDefinition(label="-"),
            value=DataDefinition(cls=str, label="-"),
            label="-",
        )
        with pytest.raises(NotPortable):
            sut.porter.load({"hello": "Hello, world!"})

    def test_dump__without_items(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            manufacturer=lambda values: dict(values) if values else {},
            key=StrDefinition(label="-"),
            value=StrDefinition(label="-"),
            label="-",
        )
        assert sut.porter.dump({}) == {}

    def test_dump__with_items(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            manufacturer=lambda values: dict(values) if values else {},
            key=StrDefinition(label="-"),
            value=StrDefinition(label="-"),
            label="-",
        )
        assert sut.porter.dump({"hello": "Hello, world!"}) == {"hello": "Hello, world!"}

    def test_dump__with_item_without_porter(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            manufacturer=lambda values: dict(values) if values else {},
            key=StrDefinition(label="-"),
            value=DataDefinition(cls=str, label="-"),
            label="-",
        )
        with pytest.raises(NotPortable):
            sut.porter.dump({"hello": "Hello, world!"})


class TestMutableMappingDefinition:
    def test_clear(self) -> None:
        data = {"foo": "FOO", "bar": "BAR"}
        MutableMappingDefinition[dict[str, str], str, str](
            cls=list,
            key=StrDefinition(label="-"),
            value=DataDefinition(cls=str, label="-"),
            label="-",
        ).clear(data)
        assert not data

    @pytest.mark.parametrize(
        ("expected", "data", "values"),
        [
            ({}, {}, {}),
            (
                {"foo": "FOO", "bar": "BAR"},
                {"qux": "QUX"},
                ({"foo": "FOO", "bar": "BAR"}),
            ),
            ({}, {"qux": "QUX"}, {}),
        ],
    )
    def test_replace(
        self, expected: dict[str, str], data: dict[str, str], values: Mapping[str, str]
    ) -> None:
        MutableMappingDefinition[dict[str, str], str, str](
            cls=list,
            key=StrDefinition(label="-"),
            value=DataDefinition(cls=str, label="-"),
            label="-",
        ).replace(data, values)
        assert data == expected
