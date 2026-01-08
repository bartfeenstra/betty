import pathlib
from collections.abc import Sequence

import pytest
from typing_extensions import override

from betty.data.indicator import (
    AnyIndex,
    AnyKey,
    Attr,
    Index,
    Indicator,
    Key,
    Path,
    Selector,
    Selectors,
)


class DummyIndicator(Indicator):
    @override
    def format(self) -> str:
        return "DUMMY"


class TestAttr:
    def test_attr(self) -> None:
        assert Attr("attr").attr == "attr"

    def test_format(self) -> None:
        assert Attr("attr").format() == ".attr"


class TestAnyIndex:
    def test_format(self) -> None:
        assert AnyIndex().format()


class TestIndex:
    def test_item(self) -> None:
        assert Index(0).item == 0

    def test_format(self) -> None:
        assert Index(0).format() == "[0]"


class TestAnyKey:
    def test_item(self) -> None:
        assert Key("key").item == "key"

    def test_format(self) -> None:
        assert AnyKey().format()


class TestKey:
    def test_format(self) -> None:
        assert Key("key").format() == '["key"]'


class TestPath:
    def test_format(self) -> None:
        assert Path(pathlib.Path("my-first-path")).format().endswith("my-first-path")


class TestSelectors:
    @pytest.mark.parametrize(
        ("expected", "selectors"),
        [
            (
                "data",
                [],
            ),
            (
                "data.my_first_attr.my_second_attr",
                [
                    Attr("my_first_attr"),
                    Attr("my_second_attr"),
                ],
            ),
        ],
    )
    def test_format(self, expected: str, selectors: Sequence[Selector]) -> None:
        assert Selectors(*selectors).format() == expected

    @pytest.mark.parametrize(
        ("expected", "selectors"),
        [
            (
                "",
                [],
            ),
            (
                "DUMMY\ndata.my_first_attr.my_second_attr\nDUMMY\ndata.my_third_attr.my_fourth_attr",
                [
                    DummyIndicator(),
                    Attr("my_first_attr"),
                    Attr("my_second_attr"),
                    DummyIndicator(),
                    Attr("my_third_attr"),
                    Attr("my_fourth_attr"),
                ],
            ),
        ],
    )
    def test_reduce(self, expected: str, selectors: Sequence[Selector]) -> None:
        assert (
            "\n".join(
                [selector.format() for selector in Selectors.reduce(*selectors)]
            ).format()
            == expected
        )
