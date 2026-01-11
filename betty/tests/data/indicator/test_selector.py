from collections.abc import Sequence
from typing import Any

import pytest
from typing_extensions import override

from betty.data.indicator import Indicator
from betty.data.indicator.selector import Attr, Index, Key, Selector, Selectors
from betty.exception import HumanFacingException


class DummyIndicator(Indicator):
    @override
    def format(self) -> str:
        return "DUMMY"


class TestAttr:
    def test_format(self) -> None:
        assert Attr("attr").format() == ".attr"

    def test_get(self) -> None:
        class _Data:
            my_first_attr = "my-first-value"

        assert Attr("my_first_attr").get(_Data()) == "my-first-value"

    @pytest.mark.parametrize(
        "data",
        [
            [],
            {},
            object(),
        ],
    )
    def test_get__with_error(self, data: Any) -> None:
        with pytest.raises(HumanFacingException):
            Attr("my_first_attr").get(data)


class TestIndex:
    def test_format(self) -> None:
        assert Index(0).format() == "[0]"

    def test_get(self) -> None:
        assert Index(0).get(["my-first-value"]) == "my-first-value"

    @pytest.mark.parametrize(
        "data",
        [
            [],
            {},
            object(),
        ],
    )
    def test_get__with_error(self, data: Any) -> None:
        with pytest.raises(HumanFacingException):
            Index(0).get(data)


class TestKey:
    def test_format(self) -> None:
        assert Key("key").format() == '["key"]'

    def test_get(self) -> None:
        assert (
            Key("my_first_key").get({"my_first_key": "my-first-value"})
            == "my-first-value"
        )

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {
                "my_second_key": "my-second-value",
            },
            [],
            object(),
        ],
    )
    def test_get__with_error(self, data: Any) -> None:
        with pytest.raises(HumanFacingException):
            Key("my_first_key").get(data)


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

    def test_get__with_error(self) -> None:
        outer_selector = Index(1)
        inner_selector = Index(0)
        selectors = [outer_selector, inner_selector]
        with pytest.raises(HumanFacingException) as exc_info:
            Selectors(*selectors).get([[], []])
        assert list(exc_info.value.indicators) == [inner_selector, outer_selector]
