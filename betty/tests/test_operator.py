from collections.abc import Sequence
from typing import Any, override

import pytest

from betty.localizables.plain import Plain
from betty.localizer import default_localizer
from betty.location import format_
from betty.operator import Attr, Chain, Index, Key, Operator, OperatorError, _Operator
from betty.typing import Unreachable


class TestAttr:
    def test_operator(self) -> None:
        assert Attr("my_first_attr").operator == "my_first_attr"

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


class TestChain:
    def test___hash__(self) -> None:
        assert hash(Chain()) == hash(Chain())
        assert hash(Chain()) != hash(Chain(Index(0)))

    def test___eq__(self) -> None:
        assert Chain() == Chain()
        assert Chain() != Chain(Index(0))

    @pytest.mark.parametrize(
        ("expected", "operators"),
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
    def test_format(self, expected: str, operators: Sequence[Operator]) -> None:
        assert Chain(*operators).format() == expected

    def test_get(self) -> None:
        assert (
            Chain(Index(1), Index(0)).get([[], ["my-first-value"]]) == "my-first-value"
        )

    def test_set(self) -> None:
        data = [[], ["my-first-value"]]
        Chain(Index(1), Index(0)).set(data, "my-second-value")
        assert data[1][0] == "my-second-value"

    def test_delete(self) -> None:
        data = [[], ["my-first-value"]]
        Chain(Index(1), Index(0)).delete(data)
        assert data[1] == []

    @pytest.mark.parametrize(
        ("expected", "locators"),
        [
            (
                "",
                [],
            ),
            (
                "DUMMY\ndata.my_first_attr.my_second_attr\nDUMMY\ndata.my_third_attr.my_fourth_attr",
                [
                    Plain("DUMMY"),
                    Attr("my_first_attr"),
                    Attr("my_second_attr"),
                    Plain("DUMMY"),
                    Attr("my_third_attr"),
                    Attr("my_fourth_attr"),
                ],
            ),
        ],
    )
    def test_reduce(self, expected: str, locators: Sequence[Operator]) -> None:
        assert (
            "\n".join(
                format_(*Chain.reduce(*locators), localizer=default_localizer)
            ).format()
            == expected
        )


class OperatorTest_Operator(_Operator):
    @override
    def _get(self, data: Any, /) -> Any:
        raise Unreachable

    @override
    def _set(self, data: Any, value: Any, /) -> None:
        raise Unreachable

    @override
    def _delete(self, data: Any, /) -> None:
        raise Unreachable

    @override
    def format(self) -> str:
        raise Unreachable


class Test_Operator:
    def test_operator(self) -> None:
        operator = "my_first_operator"
        sut = OperatorTest_Operator(operator)
        assert sut.operator == operator

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (True, OperatorTest_Operator(1), OperatorTest_Operator(1)),
            (False, OperatorTest_Operator(1), OperatorTest_Operator(2)),
            (False, OperatorTest_Operator(1), OperatorTest_Operator("1")),
        ],
    )
    def test___hash__(self, expected: bool, one: Operator, other: Operator) -> None:
        assert hash(one) == hash(one)
        assert hash(other) == hash(other)
        assert (hash(one) == hash(other)) is expected

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (True, OperatorTest_Operator(1), OperatorTest_Operator(1)),
            (False, OperatorTest_Operator(1), OperatorTest_Operator(2)),
            (False, OperatorTest_Operator(1), OperatorTest_Operator("1")),
        ],
    )
    def test___eq__(self, expected: bool, one: Operator, other: Operator) -> None:
        assert one == one
        assert other == other
        assert (one == other) is expected


class TestOperatorError:
    def test(self) -> None:
        assert "[0]" in str(OperatorError(Index(0)))
