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
    assert_none,
    assert_locale,
    assert_setattr,
    assert_locale_identifier,
)
from betty.assertion.error import AssertionFailed, Index, Key
from betty.error import UserFacingError
from betty.locale import UNDETERMINED_LOCALE, DEFAULT_LOCALE
from betty.locale.localizable import static
from betty.test_utils.assertion.error import raises_error
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Mapping

_T = TypeVar("_T")


class TestAssertionChain:
    def test___call__(self) -> None:
        sut = AssertionChain[int, int](lambda value: value)
        assert sut(123) == 123

    def test___or__(self) -> None:
        sut = AssertionChain[int, int](lambda value: value)
        sut |= lambda value: 2 * value
        assert sut(123) == 246

    def test_assertion(self) -> None:
        sut = AssertionChain[int, int](lambda value: value)
        assert sut(123) == 123

    def test_chain(self) -> None:
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
    def test_with_valid_assertion(
        self,
        if_assertion: Assertion[Any, bool],
        else_assertion: Assertion[Any, bool],
        value: int,
    ) -> None:
        assert assert_or(if_assertion, else_assertion)(value) == value

    def test_with_invalid_assertion(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_or(_always_invalid, _always_invalid)(123)


class TestAssertBool:
    def test_with_valid_value(self) -> None:
        assert_bool()(True)

    def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_bool()(123)


class TestAssertInt:
    def test_with_valid_value(self) -> None:
        assert_int()(123)

    def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_int()(False)


class TestAssertFloat:
    def test_with_valid_value(self) -> None:
        assert_float()(1.23)

    def test_with_invalid_value(self) -> None:
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
    def test_with_valid_value(self, value: Number) -> None:
        assert_number()(value)

    def test_with_invalid_value(self) -> None:
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
    def test_with_valid_value(self, value: int | float) -> None:
        assert_positive_number()(1.23)

    @pytest.mark.parametrize(
        "value",
        [
            -1,
            -0.0000000001,
            -1.0,
        ],
    )
    def test_with_invalid_value(self, value: int | float) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_positive_number()(value)


class TestAssertStr:
    def test_with_valid_value(self) -> None:
        assert_str()("Hello, world!")

    def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_str()(False)


class TestAssertSequence:
    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            None,
            123,
            object(),
            {},
        ],
    )
    def test_with_invalid_top_level_value(self, value: Any) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_sequence()(value)

    def test_with_invalid_item(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Index(0)]):
            assert_sequence(assert_str())([123])

    @pytest.mark.parametrize(
        ("value", "value_assertion"),
        [
            ([], None),
            ([], assert_str()),
            (["abc"], assert_str()),
        ],
    )
    def test_valid(
        self, value: Any, value_assertion: Assertion[Any, Any] | None
    ) -> None:
        assert_sequence(value_assertion)(value)


class TestAssertFields:
    def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_fields(OptionalField("hello", assert_str()))(None)

    def test_required_without_key(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Key("hello")]):
            assert_fields(RequiredField("hello", assert_str()))({})

    def test_optional_without_key(self) -> None:
        expected: Mapping[str, Any] = {}
        actual = assert_fields(OptionalField("hello", assert_str()))({})
        assert actual == expected

    def test_required_key_with_key(self) -> None:
        expected = {
            "hello": "World!",
        }
        actual = assert_fields(RequiredField("hello", assert_str()))(
            {"hello": "World!"}
        )
        assert actual == expected

    def test_optional_key_with_key(self) -> None:
        expected = {
            "hello": "World!",
        }
        actual = assert_fields(OptionalField("hello", assert_str()))(
            {"hello": "World!"}
        )
        assert actual == expected

    def test_without_field_assertion(self) -> None:
        expected = {
            "hello": "World!",
        }
        actual = assert_fields(RequiredField("hello"))({"hello": "World!"})
        assert actual == expected


class TestAssertField:
    def test_with_invalid_value(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_field(OptionalField("hello", assert_str()))(None)

    def test_required_without_key(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Key("hello")]):
            assert_field(RequiredField("hello", assert_str()))({})

    def test_optional_without_key(self) -> None:
        expected = Void
        actual = assert_field(OptionalField("hello", assert_str()))({})
        assert actual == expected

    def test_required_key_with_key(self) -> None:
        expected = "World!"
        actual = assert_field(RequiredField("hello", assert_str()))({"hello": "World!"})
        assert actual == expected

    def test_optional_key_with_key(self) -> None:
        expected = "World!"
        actual = assert_field(OptionalField("hello", assert_str()))({"hello": "World!"})
        assert actual == expected


class TestAssertMapping:
    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            None,
            "abc",
            123,
            object(),
            [],
        ],
    )
    def test_with_invalid_top_level_value(self, value: Any) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_mapping()(value)

    def test_with_invalid_item_value(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Key("abc")]):
            assert_mapping(assert_str())({"abc": 123})

    def test_with_invalid_item_key(self) -> None:
        with raises_error(error_type=AssertionFailed, error_contexts=[Key("123")]):
            assert_mapping(None, assert_str())({123: "abc"})

    @pytest.mark.parametrize(
        ("value", "value_assertion", "key_assertion"),
        [
            ({}, None, None),
            ({}, assert_str(), None),
            ({}, None, assert_str()),
            ({123: "abc"}, assert_str(), None),
            ({"abc": 123}, None, assert_str()),
        ],
    )
    def test_valid(
        self,
        value: Any,
        value_assertion: Assertion[Any, Any] | None,
        key_assertion: Assertion[Any, Any] | None,
    ) -> None:
        assert_mapping(value_assertion, key_assertion)(value)


class TestAssertRecord:
    def test_with_unknown_key_should_error(self) -> None:
        with raises_error(error_contexts=[Key("unknown-key")]):
            assert_record()({"unknown-key": True})

    def test_with_optional_fields_without_items(self) -> None:
        expected: Mapping[str, Any] = {}
        actual = assert_record(OptionalField("hello", assert_str()))({})
        assert actual == expected

    def test_with_optional_fields_with_items(self) -> None:
        expected = {
            "hello": "WORLD!",
        }
        actual = assert_record(
            OptionalField("hello", assert_str().chain(lambda x: x.upper()))
        )({"hello": "World!"})
        assert actual == expected

    def test_with_required_fields_without_items(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_record(RequiredField("hello", assert_str()))({})

    def test_with_required_fields_with_items(self) -> None:
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
    def test_with_valid_str_path(self) -> None:
        assert_path()("~/../foo/bar")

    def test_with_valid_path_path(self) -> None:
        assert_path()(Path("~/../foo/bar"))


class TestAssertDirectoryPath:
    def test_without_existing_path(self) -> None:
        with raises_error(error_type=AssertionFailed):
            assert_directory_path()("~/../foo/bar")

    def test_without_directory_path(self) -> None:
        with NamedTemporaryFile() as f, raises_error(error_type=AssertionFailed):
            assert_directory_path()(f.name)

    async def test_with_valid_path_str(self) -> None:
        async with TemporaryDirectory() as directory_path_str:
            assert_directory_path()(directory_path_str)

    async def test_with_valid_path_path(self) -> None:
        async with TemporaryDirectory() as directory_path_str:
            assert_directory_path()(Path(directory_path_str))


class TestAssertFilePath:
    def test_without_existing_path(self) -> None:
        with pytest.raises(UserFacingError):
            assert_file_path()("~/../foo/bar")

    def test_with_valid_path_str(self) -> None:
        with NamedTemporaryFile() as f:
            assert_file_path()(f.name)

    def test_with_valid_path_path(self) -> None:
        with NamedTemporaryFile() as f:
            assert_file_path()(Path(f.name))


class TestAssertIsinstance:
    def test_with_instance(self) -> None:
        class MyClass:
            pass

        instance = MyClass()
        assert assert_isinstance(MyClass)(instance) == instance

    def test_without_instance(self) -> None:
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
    def test_exact_with_valid_value(self, exact: int, value: Sized) -> None:
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
    def test_exact_with_invalid_value(self, exact: int, value: Sized) -> None:
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
    def test_bound_with_valid_value(
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
    def test_bound_with_invalid_value(
        self, minimum: int | None, maximum: int | None, value: Sized
    ) -> None:
        with pytest.raises(AssertionFailed):
            assert_len(minimum=minimum, maximum=maximum)(value)


class TestAssertNone:
    def test_with_valid_value(self) -> None:
        assert_none()(None)

    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            123,
            "abc",
            object(),
            [],
            {},
        ],
    )
    def test_with_invalid_value(self, value: Any) -> None:
        with pytest.raises(AssertionFailed):
            assert_none()(value)


class TestAssertLocale:
    @pytest.mark.parametrize(
        "value",
        [
            UNDETERMINED_LOCALE,
            DEFAULT_LOCALE,
            "nl-NL",
            "uk",
        ],
    )
    def test_with_valid_value(self, value: str) -> None:
        assert assert_locale()(value) == value

    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            123,
            "",
            "non-existent-locale",
            object(),
            [],
            {},
        ],
    )
    def test_with_invalid_value(self, value: Any) -> None:
        with pytest.raises(AssertionFailed):
            assert_locale()(value)


class TestAssertLocaleIdentifier:
    @pytest.mark.parametrize(
        "value",
        [
            UNDETERMINED_LOCALE,
            DEFAULT_LOCALE,
            "nl-NL",
            "uk",
            "non-existent-locale",
        ],
    )
    def test_with_valid_value(self, value: str) -> None:
        assert assert_locale_identifier()(value) == value

    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            123,
            "",
            object(),
            [],
            {},
        ],
    )
    def test_with_invalid_value(self, value: Any) -> None:
        with pytest.raises(AssertionFailed):
            assert_locale_identifier()(value)


class TestAssertSetattr:
    class _Instance:
        attr: Any

    def test(self) -> None:
        value = "Hello, world!"
        instance = self._Instance()
        assert assert_setattr(instance, "attr")(value) == value
        assert instance.attr == value
