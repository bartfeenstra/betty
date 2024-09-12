from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, TypeVar, Sized, TYPE_CHECKING

import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.assertion import (
    Number,
    OptionalField,
    RequiredField,
    Assertion,
    AssertionChain,
    assert_or,
    assert_bool,
    assert_directory_path,
    assert_path,
    assert_record,
    assert_str,
    assert_int,
    assert_float,
    assert_positive_number,
    assert_number,
    assert_mapping,
    assert_sequence,
    assert_fields,
    assert_field,
    assert_file_path,
    assert_isinstance,
    assert_len,
    assert_passthrough,
    assert_none,
)
from betty.assertion.error import AssertionFailed, Index, Key
from betty.error import UserFacingError
from betty.locale.localizable import static
from betty.test_utils.assertion.error import raises_error
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_T = TypeVar("_T")


class TestAssertionChain:
    async def test___call__(self) -> None:
        sut = AssertionChain[int, int](lambda value: value)
        assert sut(123) == 123

    async def test___or__(self) -> None:
        sut = AssertionChain[int, int](lambda value: value)
        sut |= lambda value: 2 * value
        assert sut(123) == 246

    async def test_assertion(self) -> None:
        sut = AssertionChain[int, int](lambda value: value)
        assert sut(123) == 123

    async def test_chain(self) -> None:
        sut = AssertionChain[int, int](lambda value: value)
        sut = sut.chain(lambda value: 2 * value)
        assert sut(123) == 246


def _always_valid(value: int) -> int:
    return value


def _always_invalid(value: int) -> int:
    raise AssertionFailed(static(""))


class TestAssertOr:
    @pytest.mark.parametrize(
        ("if_assertion", "else_assertion", "value"),
        [
            (_always_valid, _always_valid, 123),
            (_always_valid, _always_invalid, 123),
            (_always_invalid, _always_valid, 123),
        ],
    )
    async def test_with_valid_assertion(
        self,
        if_assertion: Assertion[Any, bool],
        else_assertion: Assertion[Any, bool],
        value: int,
    ) -> None:
        assert assert_or(if_assertion, else_assertion)(value) == value

    async def test_with_invalid_assertion(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_or(_always_invalid, _always_invalid)(123)


class TestAssertBool:
    async def test_with_valid_value(self) -> None:
        assert_bool()(True)

    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_bool()(123)


class TestAssertInt:
    async def test_with_valid_value(self) -> None:
        assert_int()(123)

    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_int()(False)


class TestAssertFloat:
    async def test_with_valid_value(self) -> None:
        assert_float()(1.23)

    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_float()(False)


class TestAssertNumber:
    @pytest.mark.parametrize(
        "value",
        [
            3,
            3.13,
        ],
    )
    async def test_with_valid_value(self, value: Number) -> None:
        assert_number()(value)

    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_number()(False)


class TestAssertPositiveNumber:
    @pytest.mark.parametrize(
        "value",
        [
            0,
            0.0,
            1,
            1.1,
        ],
    )
    async def test_with_valid_value(self, value: int | float) -> None:
        assert_positive_number()(1.23)

    @pytest.mark.parametrize(
        "value",
        [
            -1,
            -0.0000000001,
            -1.0,
        ],
    )
    async def test_with_invalid_value(self, value: int | float) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_positive_number()(value)


class TestAssertStr:
    async def test_with_valid_value(self) -> None:
        assert_str()("Hello, world!")

    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_str()(False)


class TestAssertSequence:
    async def test_without_list(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_sequence(assert_str())(False)

    async def test_with_invalid_item(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Index(0)]):
            assert_sequence(assert_str())([123])

    async def test_with_empty_list(self) -> None:
        assert_sequence(assert_str())([])

    async def test_with_valid_sequence(self) -> None:
        assert_sequence(assert_str())(["Hello!"])


class TestAssertFields:
    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_fields(OptionalField("hello", assert_str()))(None)

    async def test_required_without_key(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Key("hello")]):
            assert_fields(RequiredField("hello", assert_str()))({})

    async def test_optional_without_key(self) -> None:
        expected: Mapping[str, Any] = {}
        actual = assert_fields(OptionalField("hello", assert_str()))({})
        assert actual == expected

    async def test_required_key_with_key(self) -> None:
        expected = {
            "hello": "World!",
        }
        actual = assert_fields(RequiredField("hello", assert_str()))(
            {"hello": "World!"}
        )
        assert actual == expected

    async def test_optional_key_with_key(self) -> None:
        expected = {
            "hello": "World!",
        }
        actual = assert_fields(OptionalField("hello", assert_str()))(
            {"hello": "World!"}
        )
        assert actual == expected


class TestAssertField:
    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_field(OptionalField("hello", assert_str()))(None)

    async def test_required_without_key(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Key("hello")]):
            assert_field(RequiredField("hello", assert_str()))({})

    async def test_optional_without_key(self) -> None:
        expected = Void
        actual = assert_field(OptionalField("hello", assert_str()))({})
        assert actual == expected

    async def test_required_key_with_key(self) -> None:
        expected = "World!"
        actual = assert_field(RequiredField("hello", assert_str()))({"hello": "World!"})
        assert actual == expected

    async def test_optional_key_with_key(self) -> None:
        expected = "World!"
        actual = assert_field(OptionalField("hello", assert_str()))({"hello": "World!"})
        assert actual == expected


class TestAssertMapping:
    async def test_without_mapping(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_mapping(assert_str())(None)

    async def test_with_invalid_item(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Key("hello")]):
            assert_mapping(assert_str())({"hello": False})

    async def test_with_empty_dict(self) -> None:
        assert_mapping(assert_str())({})

    async def test_with_valid_mapping(self) -> None:
        assert_mapping(assert_str())({"hello": "World!"})


class TestAssertRecord:
    async def test_with_optional_fields_without_items(self) -> None:
        expected: Mapping[str, Any] = {}
        actual = assert_record(OptionalField("hello", assert_str()))({})
        assert actual == expected

    async def test_with_optional_fields_with_items(self) -> None:
        expected = {
            "hello": "WORLD!",
        }
        actual = assert_record(
            OptionalField("hello", assert_str().chain(lambda x: x.upper()))
        )({"hello": "World!"})
        assert actual == expected

    async def test_with_required_fields_without_items(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_record(RequiredField("hello", assert_str()))({})

    async def test_with_required_fields_with_items(self) -> None:
        expected = {
            "hello": "WORLD!",
        }
        actual = assert_record(
            RequiredField("hello", assert_str().chain(lambda x: x.upper()))
        )(
            {
                "hello": "World!",
            }
        )
        assert actual == expected


class TestAssertPath:
    async def test_with_valid_str_path(self) -> None:
        assert_path()("~/../foo/bar")

    async def test_with_valid_path_path(self) -> None:
        assert_path()(Path("~/../foo/bar"))


class TestAssertDirectoryPath:
    async def test_without_existing_path(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_directory_path()("~/../foo/bar")

    async def test_without_directory_path(self) -> None:
        with NamedTemporaryFile() as f, raises_error(error_type=AssertionFailed):
            assert_directory_path()(f.name)

    async def test_with_valid_path_str(self) -> None:
        async with TemporaryDirectory() as directory_path_str:
            assert_directory_path()(directory_path_str)

    async def test_with_valid_path_path(self) -> None:
        async with TemporaryDirectory() as directory_path_str:
            assert_directory_path()(Path(directory_path_str))


class TestAssertFilePath:
    async def test_without_existing_path(self) -> None:
        with pytest.raises(UserFacingError):
            assert_file_path()("~/../foo/bar")

    async def test_with_valid_path_str(self) -> None:
        with NamedTemporaryFile() as f:
            assert_file_path()(f.name)

    async def test_with_valid_path_path(self) -> None:
        with NamedTemporaryFile() as f:
            assert_file_path()(Path(f.name))


class TestAssertIsinstance:
    async def test_with_instance(self) -> None:
        class MyClass:
            pass

        instance = MyClass()
        assert assert_isinstance(MyClass)(instance) == instance

    async def test_without_instance(self) -> None:
        class MyClass:
            pass

        with pytest.raises(AssertionFailed):
            assert assert_isinstance(MyClass)(object())  # type: ignore[truthy-bool]


class TestAssertLen:
    @pytest.mark.parametrize(
        ("exact", "value"),
        [
            (0, ""),
            (3, "abc"),
            (0, []),
            (3, ["a", "b", "c"]),
            (0, {}),
            (3, {"a": 1, "b": 2, "c": 3}),
        ],
    )
    async def test_exact_with_valid_value(self, exact: int, value: Sized) -> None:
        assert_len(exact)(value)

    @pytest.mark.parametrize(
        ("exact", "value"),
        [
            (1, ""),
            (4, ""),
            (4, "abc"),
            (1, []),
            (1, ["a", "b", "c"]),
            (4, ["a", "b", "c"]),
            (1, {}),
            (1, {"a": 1, "b": 2, "c": 3}),
            (4, {"a": 1, "b": 2, "c": 3}),
        ],
    )
    async def test_exact_with_invalid_value(self, exact: int, value: Sized) -> None:
        with pytest.raises(AssertionFailed):
            assert_len(exact)(value)

    @pytest.mark.parametrize(
        ("minimum", "maximum", "value"),
        [
            # Minimums that match the exact length.
            (0, None, ""),
            (3, None, "abc"),
            (0, None, []),
            (3, None, ["a", "b", "c"]),
            (0, None, {}),
            (3, None, {"a": 1, "b": 2, "c": 3}),
            # Minimums that are significantly below the exact length.
            (0, None, "abc"),
            (0, None, ["a", "b", "c"]),
            (0, None, {"a": 1, "b": 2, "c": 3}),
            # Maximums that match the exact length.
            (None, 0, ""),
            (None, 3, "abc"),
            (None, 0, []),
            (None, 3, ["a", "b", "c"]),
            (None, 0, {}),
            (None, 3, {"a": 1, "b": 2, "c": 3}),
            # Maximums that are significantly above the exact length.
            (None, 9, "abc"),
            (None, 9, ["a", "b", "c"]),
            (None, 9, {"a": 1, "b": 2, "c": 3}),
        ],
    )
    async def test_bound_with_valid_value(
        self, minimum: int | None, maximum: int | None, value: Sized
    ) -> None:
        assert_len(minimum=minimum, maximum=maximum)(value)

    @pytest.mark.parametrize(
        ("minimum", "maximum", "value"),
        [
            # Minimums.
            (1, None, ""),
            (4, None, "abc"),
            (1, None, []),
            (4, None, ["a", "b", "c"]),
            (1, None, {}),
            (4, None, {"a": 1, "b": 2, "c": 3}),
            # Maximums.
            (None, 2, "abc"),
            (None, 2, ["a", "b", "c"]),
            (None, 2, {"a": 1, "b": 2, "c": 3}),
        ],
    )
    async def test_bound_with_invalid_value(
        self, minimum: int | None, maximum: int | None, value: Sized
    ) -> None:
        with pytest.raises(AssertionFailed):
            assert_len(minimum=minimum, maximum=maximum)(value)


class TestAssertPassthrough:
    @pytest.mark.parametrize(
        ("assertions", "value"),
        [
            ([], object()),
            ([lambda value: isinstance(value, object)], object()),
        ],
    )
    async def test_exact_with_valid_value(
        self, assertions: Sequence[Assertion[object, Any]], value: object
    ) -> None:
        assert assert_passthrough(*assertions)(value) is value

    @pytest.mark.parametrize(
        ("assertions", "value"),
        [
            ([assert_bool()], None),
            ([assert_none(), assert_bool()], None),
        ],
    )
    async def test_exact_with_invalid_value(
        self, assertions: Sequence[Assertion[Any, Any]], value: Any
    ) -> None:
        with pytest.raises(AssertionFailed):
            assert_passthrough(*assertions)(value)
