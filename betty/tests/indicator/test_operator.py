from collections.abc import Sequence
from typing import Any, override

import pytest

from betty.indicator import Indicator
from betty.indicator.operator import (
    Attr,
    Index,
    Key,
    Operator,
    OperatorError,
    Operators,
    _Operator,
)


class DummyIndicator(Indicator):
    @override
    def format(self) -> str:
        return "DUMMY"


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


class TestOperators:
    def test___hash__(self) -> None:
        assert hash(Operators()) == hash(Operators())
        assert hash(Operators()) != hash(Operators(Index(0)))

    def test___eq__(self) -> None:
        assert Operators() == Operators()
        assert Operators() != Operators(Index(0))

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
        assert Operators(*operators).format() == expected

    @pytest.mark.parametrize(
        ("expected", "operators"),
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
    def test_reduce(self, expected: str, operators: Sequence[Operator]) -> None:
        assert (
            "\n".join([
                operator.format() for operator in Operators.reduce(*operators)
            ]).format()
            == expected
        )

    def test_get(self) -> None:
        assert (
            Operators(Index(1), Index(0)).get([[], ["my-first-value"]])
            == "my-first-value"
        )

    def test_set(self) -> None:
        data = [[], ["my-first-value"]]
        Operators(Index(1), Index(0)).set(data, "my-second-value")
        assert data[1][0] == "my-second-value"

    def test_delete(self) -> None:
        data = [[], ["my-first-value"]]
        Operators(Index(1), Index(0)).delete(data)
        assert data[1] == []


class OperatorTest_Operator(_Operator):
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
