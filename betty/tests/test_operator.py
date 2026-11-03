from collections.abc import Sequence
from typing import override

import pytest

from betty.localizer import default_localizer
from betty.operator import Attr, Chain, Index, Key, Operator, _Operator
from betty.typing import Unreachable
from betty.user.location import format_


class TestAttr:
    def test_operator(self) -> None:
        assert Attr("my_first_attr").operator == "my_first_attr"

    def test___str__(self) -> None:
        assert str(Attr("attr")) == ".attr"

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
    def test___str__(self) -> None:
        assert str(Index(0)) == "[0]"


class TestKey:
    def test___str__(self) -> None:
        assert str(Key("key")) == '["key"]'


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
    def test___str__(self, expected: str, operators: Sequence[Operator]) -> None:
        assert str(Chain(*operators)) == expected

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
                    "DUMMY",
                    Attr("my_first_attr"),
                    Attr("my_second_attr"),
                    "DUMMY",
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
    def __str__(self) -> str:
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
