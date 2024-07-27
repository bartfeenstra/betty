from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, TypeVar

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
    assert_list,
    assert_mapping,
    assert_sequence,
    assert_dict,
    assert_fields,
    assert_field,
    assert_file_path,
    assert_isinstance,
)
from betty.assertion.error import AssertionFailed
from betty.locale.localizable import static
from betty.typing import Void
from betty.tests.assertion import raises_error

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


class TestAssertList:
    async def test_with_list(self) -> None:
        assert_list()([])

    async def test_without_list(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_list()(False)


class TestAssertSequence:
    async def test_without_list(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_sequence(assert_str())(False)

    async def test_with_invalid_item(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=["0"]):
            assert_sequence(assert_str())([123])

    async def test_with_empty_list(self) -> None:
        assert_sequence(assert_str())([])

    async def test_with_valid_sequence(self) -> None:
        assert_sequence(assert_str())(["Hello!"])


class TestAssertDict:
    async def test_with_dict(self) -> None:
        assert_dict()({})

    async def test_without_dict(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_dict()(False)


class TestAssertFields:
    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_fields(OptionalField("hello", assert_str()))(None)

    async def test_required_without_key(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=["hello"]):
            assert_fields(RequiredField("hello", assert_str()))({})

    async def test_optional_without_key(self) -> None:
        expected: dict[str, Any] = {}
        actual = assert_fields(OptionalField("hello", assert_str()))({})
        assert expected == actual

    async def test_required_key_with_key(self) -> None:
        expected = {
            "hello": "World!",
        }
        actual = assert_fields(RequiredField("hello", assert_str()))(
            {"hello": "World!"}
        )
        assert expected == actual

    async def test_optional_key_with_key(self) -> None:
        expected = {
            "hello": "World!",
        }
        actual = assert_fields(OptionalField("hello", assert_str()))(
            {"hello": "World!"}
        )
        assert expected == actual


class TestAssertField:
    async def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_field(OptionalField("hello", assert_str()))(None)

    async def test_required_without_key(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=["hello"]):
            assert_field(RequiredField("hello", assert_str()))({})

    async def test_optional_without_key(self) -> None:
        expected = Void
        actual = assert_field(OptionalField("hello", assert_str()))({})
        assert expected == actual

    async def test_required_key_with_key(self) -> None:
        expected = "World!"
        actual = assert_field(RequiredField("hello", assert_str()))({"hello": "World!"})
        assert expected == actual

    async def test_optional_key_with_key(self) -> None:
        expected = "World!"
        actual = assert_field(OptionalField("hello", assert_str()))({"hello": "World!"})
        assert expected == actual


class TestAssertMapping:
    async def test_without_mapping(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_mapping(assert_str())(None)

    async def test_with_invalid_item(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=["hello"]):
            assert_mapping(assert_str())({"hello": False})

    async def test_with_empty_dict(self) -> None:
        assert_mapping(assert_str())({})

    async def test_with_valid_mapping(self) -> None:
        assert_mapping(assert_str())({"hello": "World!"})


class TestAssertRecord:
    async def test_with_optional_fields_without_items(self) -> None:
        expected: dict[str, Any] = {}
        actual = assert_record(OptionalField("hello", assert_str()))({})
        assert expected == actual

    async def test_with_optional_fields_with_items(self) -> None:
        expected = {
            "hello": "WORLD!",
        }
        actual = assert_record(
            OptionalField("hello", assert_str().chain(lambda x: x.upper()))
        )({"hello": "World!"})
        assert expected == actual

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
        assert expected == actual


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
        with raises_error(error_type=AssertionFailed):
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
