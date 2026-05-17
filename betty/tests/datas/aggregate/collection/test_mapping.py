from collections.abc import Mapping

import pytest

from betty.data import DataDefinition
from betty.datas.aggregate.collection.mapping import MappingDefinition
from betty.datas.str import StrDefinition
from betty.portable.error import NotPortable
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestMappingDefinition:
    def test_item(self) -> None:
        key = StrDefinition(label=DUMMY_LOCALIZABLE)
        sut = MappingDefinition[dict[str, str], str, str](
            cls=dict,
            key=key,
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.item is key

    def test_load__without_items(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.load({}) == {}

    def test_load__with_items(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.load({"hello": "Hello, world!"}) == {"hello": "Hello, world!"}

    def test_load__with_factory(self) -> None:
        class FactoryDict(dict[str, str]):
            pass

        sut = MappingDefinition[dict[str, str], str, str](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
            factory=FactoryDict,
        )
        assert isinstance(sut.porter.load({}), FactoryDict)

    def test_load__with_item_not_loadable(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.porter.load({"hello": "Hello, world!"})

    def test_dump__without_items(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.dump({}) == {}

    def test_dump__with_items(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=StrDefinition(label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        assert sut.porter.dump({"hello": "Hello, world!"}) == {"hello": "Hello, world!"}

    def test_dump__with_item_not_dumpable(self) -> None:
        sut = MappingDefinition[dict[str, str], str, str](
            cls=dict,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        )
        with pytest.raises(NotPortable):
            sut.porter.dump({"hello": "Hello, world!"})

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
        MappingDefinition[dict[str, str], str, str](
            cls=list,
            key=StrDefinition(label=DUMMY_LOCALIZABLE),
            value=DataDefinition(cls=str, label=DUMMY_LOCALIZABLE),
            label=DUMMY_LOCALIZABLE,
        ).replace(data, values)
        assert data == expected
