from __future__ import annotations

from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, TypeVar

import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.assertion import (
    Assertion,
    AssertionChain,
    Number,
    OptionalField,
    RequiredField,
    assert_bool,
    assert_directory_path,
    assert_enum,
    assert_file_path,
    assert_float,
    assert_int,
    assert_isinstance,
    assert_len,
    assert_locale,
    assert_mapping,
    assert_none,
    assert_number,
    assert_or,
    assert_path,
    assert_positive_number,
    assert_record,
    assert_sequence,
    assert_str,
)
from betty.data.indicator import Index, Key
from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE_TAG, to_language_tag
from betty.locale.localizable.static import StaticTranslations
from betty.test_utils.exception import assert_error

if TYPE_CHECKING:
    from collections.abc import Mapping, Sized

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
    raise HumanFacingException(StaticTranslations(""))


@pytest.mark.parametrize(
    ("if_assertion", "else_assertion", "value"),
    [
        (_always_valid, _always_valid, 123),
        (_always_valid, _always_invalid, 123),
        (_always_invalid, _always_valid, 123),
    ],
)
def test_assert_or__with_valid_assertion(
    if_assertion: Assertion[Any, bool],
    else_assertion: Assertion[Any, bool],
    value: int,
) -> None:
    assert assert_or(if_assertion, else_assertion)(value) == value


def test_assert_or__with_invalid_assertion() -> None:
    with pytest.raises(HumanFacingException):
        assert_or(_always_invalid, _always_invalid)(123)


def test_assert_bool__with_valid_value() -> None:
    assert_bool()(True)


def test_assert_bool__with_invalid_value() -> None:
    with pytest.raises(HumanFacingException):
        assert_bool()(123)


def test_assert_int__with_valid_value() -> None:
    assert_int()(123)


def test_assert_int__with_invalid_value() -> None:
    with pytest.raises(HumanFacingException):
        assert_int()(False)


def test_assert_float__with_valid_value() -> None:
    assert_float()(1.23)


def test_assert_float__with_invalid_value() -> None:
    with pytest.raises(HumanFacingException):
        assert_float()(False)


@pytest.mark.parametrize(
    "value",
    [
        3,
        3.13,
    ],
)
def test_assert_number__with_valid_value(value: Number) -> None:
    assert_number()(value)


def test_assert_number__with_invalid_value() -> None:
    with pytest.raises(HumanFacingException):
        assert_number()(False)


@pytest.mark.parametrize(
    "value",
    [
        0,
        0.0,
        1,
        1.1,
    ],
)
def test_assert_positive_number__with_valid_value(value: int | float) -> None:
    assert_positive_number()(1.23)


@pytest.mark.parametrize(
    "value",
    [
        -1,
        -0.0000000001,
        -1.0,
    ],
)
def test_assert_positive_number__with_invalid_value(value: int | float) -> None:
    with pytest.raises(HumanFacingException):
        assert_positive_number()(value)


@pytest.mark.parametrize(
    ("value", "exact_length", "minimum_length", "maximum_length"),
    [
        ("abcde", None, None, None),
        ("abcde", 5, None, None),
        ("abcde", None, 1, None),
        ("abcde", None, 5, None),
        ("abcde", None, None, 5),
        ("abcde", None, None, 9),
    ],
)
def test_assert_str__with_valid_value(
    value: Any,
    exact_length: int | None,
    minimum_length: int | None,
    maximum_length: int | None,
) -> None:
    assert (
        assert_str(
            exact_length=exact_length,
            minimum_length=minimum_length,
            maximum_length=maximum_length,
        )(value)
        == value
    )


@pytest.mark.parametrize(
    ("value", "exact_length", "minimum_length", "maximum_length"),
    [
        (False, None, None, None),
        ("abcde", 4, None, None),
        ("abcde", 6, None, None),
        ("abcde", None, 6, None),
        ("abcde", None, None, 4),
    ],
)
def test_assert_str__with_invalid_value(
    value: Any,
    exact_length: int | None,
    minimum_length: int | None,
    maximum_length: int | None,
) -> None:
    with pytest.raises(HumanFacingException):
        assert_str(
            exact_length=exact_length,
            minimum_length=minimum_length,
            maximum_length=maximum_length,
        )(value)


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
def test_assert_sequence__with_invalid_top_level_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_sequence()(value)


def test_assert_sequence__with_invalid_item() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        assert_sequence(assert_str())([123])
    assert_error(
        exc_info.value, error_type=HumanFacingException, error_indicators=[Index(0)]
    )


@pytest.mark.parametrize(
    ("value", "value_assertion"),
    [
        ([], None),
        ([], assert_str()),
        (["abc"], assert_str()),
    ],
)
def test_assert_sequence__valid(
    value: Any, value_assertion: Assertion[Any, Any] | None
) -> None:
    assert_sequence(value_assertion)(value)


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
def test_assert_mapping__with_invalid_top_level_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_mapping()(value)


def test_assert_mapping__with_invalid_item_value() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        assert_mapping(assert_str())({"abc": 123})
    assert_error(
        exc_info.value, error_type=HumanFacingException, error_indicators=[Key("abc")]
    )


def test_assert_mapping__with_invalid_item_key() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        assert_mapping(None, assert_str())({123: "abc"})
    assert_error(
        exc_info.value, error_type=HumanFacingException, error_indicators=[Key("123")]
    )


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
def test_assert_mapping__valid(
    value: Any,
    value_assertion: Assertion[Any, Any] | None,
    key_assertion: Assertion[Any, Any] | None,
) -> None:
    assert_mapping(value_assertion, key_assertion)(value)


def test_assert_record__with_unknown_key_should_error() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        assert_record()({"unknown-key": True})
    assert_error(
        exc_info.value,
        error_type=HumanFacingException,
        error_indicators=[Key("unknown-key")],
    )


def test_assert_record__with_optional_fields_without_items() -> None:
    expected: Mapping[str, Any] = {}
    actual = assert_record(OptionalField("hello", assert_str()))({})
    assert actual == expected


def test_assert_record__with_optional_fields_with_items() -> None:
    expected = {
        "hello": "WORLD!",
    }
    actual = assert_record(
        OptionalField("hello", assert_str().chain(lambda x: x.upper()))
    )({"hello": "World!"})
    assert actual == expected


def test_assert_record__with_required_fields_without_items() -> None:
    with pytest.raises(HumanFacingException):
        assert_record(RequiredField("hello", assert_str()))({})


def test_assert_record__with_required_fields_with_items() -> None:
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


def test_assert_record__with_as_name() -> None:
    expected = {
        "as_hello": "World!",
    }
    actual = assert_record(RequiredField("hello", None, "as_hello"))(
        {
            "hello": "World!",
        }
    )
    assert actual == expected


def test_assert_path__with_valid_str_path() -> None:
    assert_path()("~/../foo/bar")


def test_assert_path__with_valid_path_path() -> None:
    assert_path()(Path("~/../foo/bar"))


def test_assert_directory_path__without_existing_path() -> None:
    with pytest.raises(HumanFacingException):
        assert_directory_path()("~/../foo/bar")


def test_assert_directory_path__without_directory_path() -> None:
    with NamedTemporaryFile() as f, pytest.raises(HumanFacingException):
        assert_directory_path()(f.name)


async def test_assert_directory_path__with_valid_path_str() -> None:
    async with TemporaryDirectory() as directory_path_str:
        assert_directory_path()(directory_path_str)


async def test_assert_directory_path__with_valid_path_path() -> None:
    async with TemporaryDirectory() as directory_path_str:
        assert_directory_path()(Path(directory_path_str))


def test_assert_file_path__without_existing_path() -> None:
    with pytest.raises(HumanFacingException):
        assert_file_path()("~/../foo/bar")


def test_assert_file_path__with_valid_path_str() -> None:
    with NamedTemporaryFile() as f:
        assert_file_path()(f.name)


def test_assert_file_path__with_valid_path_path() -> None:
    with NamedTemporaryFile() as f:
        assert_file_path()(Path(f.name))


def test_assert_isinstance__with_instance() -> None:
    class MyClass:
        pass

    instance = MyClass()
    assert assert_isinstance(MyClass)(instance) == instance


def test_assert_isinstance__without_instance() -> None:
    class MyClass:
        pass

    with pytest.raises(HumanFacingException):
        assert assert_isinstance(MyClass)(object())  # type: ignore[truthy-bool]


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
def test_assert_len__exact_with_valid_value(exact: int, value: Sized) -> None:
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
def test_assert_len__exact_with_invalid_value(exact: int, value: Sized) -> None:
    with pytest.raises(HumanFacingException):
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
def test_assert_len__bound_with_valid_value(
    minimum: int | None, maximum: int | None, value: Sized
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
def test_assert_len__bound_with_invalid_value(
    minimum: int | None, maximum: int | None, value: Sized
) -> None:
    with pytest.raises(HumanFacingException):
        assert_len(minimum=minimum, maximum=maximum)(value)


def test_assert_none__with_valid_value() -> None:
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
def test_assert_none__with_invalid_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_none()(value)


@pytest.mark.parametrize(
    "value",
    [
        DEFAULT_LOCALE_TAG,
        "nl-NL",
        "uk",
    ],
)
def test_assert_locale__with_valid_value(value: str) -> None:
    assert to_language_tag(assert_locale()(value)) == value


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
def test_assert_locale__with_invalid_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_locale()(value)


class _Enum(Enum):
    STRING = "string"
    INT = 123


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (_Enum.STRING, "string"),
        (_Enum.INT, 123),
    ],
)
def test_assert_enum(expected: _Enum, value: Any) -> None:
    assert assert_enum(_Enum)(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        456,
        "",
        object(),
        [],
        {},
    ],
)
def test_assert_enum__with_invalid_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_enum(_Enum)(value)
