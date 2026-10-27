from collections.abc import Iterable
from typing import ClassVar

import pytest

from betty.collection.catalog import Catalog, MutableCatalog
from betty.collections.catalog.dict import DictCatalog, FrozenDictCatalog
from betty.datas.aggregate.collection.catalog import (
    CatalogDefinition,
    MutableCatalogDefinition,
)
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.mapping import TypedMappingDefinition
from betty.datas.str import StrDefinition
from betty.operator import Key
from betty.pipeline import pipe
from betty.portable import PortableData
from betty.porters.fields import FieldsPorter
from betty.porters.keyed_mapping import KeyedMappingPorter

_item = TypedMappingDefinition[dict[str, str]](
    cls=dict,
    label="-",
    fields={
        Key("key"): FieldDefinition(StrDefinition(label="-")),
        Key("other_element"): FieldDefinition(StrDefinition(label="-")),
    },
    porter=lambda field: KeyedMappingPorter("key", FieldsPorter(field)),
)


class TestCatalogDefinition:
    _portable_unordered: ClassVar[PortableData] = {
        "my_first_key": {
            "other_element": "my_first_other_element",
        }
    }
    _portable_ordered: ClassVar[PortableData] = [
        {
            "key": "my_first_key",
            "other_element": "my_first_other_element",
        }
    ]
    _values: Iterable[dict[str, str]] = [
        {
            "key": "my_first_key",
            "other_element": "my_first_other_element",
        }
    ]
    _sut_unordered = CatalogDefinition[
        Catalog[str, str, dict[str, str]],
        dict[str, str],
    ](
        value=_item,
        label="-",
        manufacturer=lambda values: FrozenDictCatalog(
            lambda value: value["key"], () if values is None else values
        ),
    )
    _sut_ordered = CatalogDefinition[
        Catalog[str, str, dict[str, str]],
        dict[str, str],
    ](
        value=_item,
        order_dump=True,
        label="-",
        manufacturer=lambda values: FrozenDictCatalog(
            lambda value: value["key"], () if values is None else values
        ),
    )

    def test_load__unordered(self) -> None:
        data = self._sut_unordered.porter.load(self._portable_unordered)
        assert isinstance(data, FrozenDictCatalog)
        assert data["my_first_key"]["key"] == "my_first_key"
        assert data["my_first_key"]["other_element"] == "my_first_other_element"

    def test_load__ordered(self) -> None:
        data = self._sut_ordered.porter.load(self._portable_ordered)
        assert isinstance(data, FrozenDictCatalog)
        assert data["my_first_key"]["key"] == "my_first_key"
        assert data["my_first_key"]["other_element"] == "my_first_other_element"

    def test_dump__unordered(self) -> None:
        data = FrozenDictCatalog[str, str, dict[str, str]](pipe, self._values)
        assert self._sut_unordered.porter.dump(data) == self._portable_unordered

    def test_dump__ordered(self) -> None:
        data = FrozenDictCatalog[str, str, dict[str, str]](pipe, self._values)
        assert self._sut_ordered.porter.dump(data) == self._portable_ordered


class TestMutableCatalogDefinition:
    _sut = MutableCatalogDefinition[
        MutableCatalog[str, str, dict[str, str], dict[str, str]],
        dict[str, str],
    ](
        value=_item,
        label="-",
        manufacturer=lambda _: DictCatalog(lambda value: value["key"]),
    )

    def test_clear(self) -> None:
        data = DictCatalog(lambda value: value["key"], ({"key": "qux"},))
        self._sut.clear(data)
        assert not data

    @pytest.mark.parametrize(
        ("expected", "data", "values"),
        [
            ([], DictCatalog(lambda value: value["key"]), ()),
            (
                [{"key": "foo"}, {"key": "bar"}],
                DictCatalog(lambda value: value["key"], ({"key": "qux"},)),
                ({"key": "foo"}, {"key": "bar"}),
            ),
            (
                [],
                DictCatalog(lambda value: value["key"], ({"key": "qux"},)),
                (),
            ),
        ],
    )
    def test_replace(
        self,
        expected: list[str],
        data: MutableCatalog[str, str, dict[str, str], dict[str, str]],
        values: Iterable[dict[str, str]],
    ) -> None:
        self._sut.replace(data, values)
        assert list(data) == expected
