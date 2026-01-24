from collections.abc import Sequence
from typing import Any

import pytest
from typing_extensions import override

from betty.data.indicator import Indicator
from betty.data.indicator.selector import (
    Attr,
    Element,
    Index,
    Key,
    Selector,
    SelectorError,
    Selectors,
)


class DummyIndicator(Indicator):
    @override
    def format(self) -> str:
        return "DUMMY"


class TestAttr:
    def test_element(self) -> None:
        assert Attr("my_first_attr").element == "my_first_attr"

    def test_format(self) -> None:
        assert Attr("attr").format() == ".attr"

    def test_get(self) -> None:
        class _Data:
            def __init__(self):
                self.my_first_attr = "my-first-value"

        assert Attr("my_first_attr").get(_Data()) == "my-first-value"

    def test_set(self) -> None:
        class _Data:
            def __init__(self):
                self.my_first_attr = "my-first-value"

        data = _Data()
        Attr("my_first_attr").set(data, "my-second-value")
        assert data.my_first_attr == "my-second-value"

    def test_delete(self) -> None:
        class _Data:
            def __init__(self):
                self.my_first_attr = "my-first-value"

        data = _Data()
        Attr("my_first_attr").delete(data)
        with pytest.raises(AttributeError):
            assert data.my_first_attr


class TestIndex:
    def test_format(self) -> None:
        assert Index(0).format() == "[0]"

    def test_get(self) -> None:
        assert Index(0).get(["my-first-value"]) == "my-first-value"

    def test_set(self) -> None:
        data = ["my-first-value"]
        Index(0).set(data, "my-second-value")
        assert data[0] == "my-second-value"

    def test_delete(self) -> None:
        data = ["my-first-value"]
        Index(0).delete(data)
        assert data == []


class TestKey:
    def test_format(self) -> None:
        assert Key("key").format() == '["key"]'

    def test_get(self) -> None:
        assert (
            Key("my_first_key").get({"my_first_key": "my-first-value"})
            == "my-first-value"
        )

    def test_set(self) -> None:
        data = {"my_first_key": "my-first-value"}
        Key("my_first_key").set(data, "my-second-value")
        assert data["my_first_key"] == "my-second-value"

    def test_delete(self) -> None:
        data = {"my_first_key": "my-first-value"}
        Key("my_first_key").delete(
            data,
        )
        assert data == {}


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

    def test_get(self) -> None:
        assert (
            Selectors(Index(1), Index(0)).get([[], ["my-first-value"]])
            == "my-first-value"
        )

    def test_set(self) -> None:
        data = [[], ["my-first-value"]]
        Selectors(Index(1), Index(0)).set(data, "my-second-value")
        assert data[1][0] == "my-second-value"

    def test_delete(self) -> None:
        data = [[], ["my-first-value"]]
        Selectors(Index(1), Index(0)).delete(data)
        assert data[1] == []


class ElementTestElement(Element[Any]):
    @override
    def _get(self, data: Any, /) -> Any:
        raise NotImplementedError

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        raise NotImplementedError

    @override
    def _delete(self, data: Any, /) -> None:
        raise NotImplementedError

    @override
    def format(self) -> str:
        raise NotImplementedError


class TestElement:
    def test_element(self) -> None:
        element = "my_first_element"
        sut = ElementTestElement(element)
        assert sut.element == element

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (True, ElementTestElement(1), ElementTestElement(1)),
            (False, ElementTestElement(1), ElementTestElement(2)),
            (False, ElementTestElement(1), ElementTestElement("1")),
        ],
    )
    def test___eq__(self, expected: bool, one: Element, other: Element) -> None:
        assert (one == other) is expected


class TestSelectorError:
    def test(self) -> None:
        assert "[0]" in str(SelectorError(Index(0)))
