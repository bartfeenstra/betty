"""
The Assertion API.
"""

from __future__ import annotations

from collections.abc import (
    Callable,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
    Sized,
)
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import NoneType
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeAlias,
    TypeVar,
    final,
    overload,
)

from betty.data import Index, Key
from betty.error import FileNotFound
from betty.exception import HumanFacingException, HumanFacingExceptionGroup
from betty.locale import from_language_tag
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph, do_you_mean
from betty.typing import internal

if TYPE_CHECKING:
    from babel import Locale

    from betty.locale.localizable import Localizable

Number: TypeAlias = int | float


_EnumT = TypeVar("_EnumT", bound=Enum)
_AssertionValueT = TypeVar("_AssertionValueT")
_AssertionReturnT = TypeVar("_AssertionReturnT")
_AssertionReturnU = TypeVar("_AssertionReturnU")
_AssertionKeyT = TypeVar("_AssertionKeyT")

Assertion: TypeAlias = Callable[
    [
        _AssertionValueT,
    ],
    _AssertionReturnT,
]

_AssertionsExtendReturnT = TypeVar("_AssertionsExtendReturnT")
_AssertionsIntermediateValueReturnT = TypeVar("_AssertionsIntermediateValueReturnT")


class AssertionChain(Generic[_AssertionValueT, _AssertionReturnT]):
    """
    An assertion chain.

    Assertion chains let you chain/link/combine assertions into pipelines that take an input
    value and, if the assertions pass, return an output value. Each chain may be (re)used as many
    times as needed.

    Assertion chains are assertions themselves: you can use a chain wherever you can use a 'plain'
    assertion.

    Assertions chains are `monads <https://en.wikipedia.org/wiki/Monad_(functional_programming)>`_.
    While uncommon in Python, this allows us to create these chains in a type-safe way, and tools
    like mypy can confirm that all assertions in any given chain are compatible with each other.
    """

    def __init__(self, _assertion: Assertion[_AssertionValueT, _AssertionReturnT], /):
        self._assertion = _assertion

    def chain(
        self, assertion: Assertion[_AssertionReturnT, _AssertionsExtendReturnT], /
    ) -> AssertionChain[_AssertionValueT, _AssertionsExtendReturnT]:
        """
        Extend the chain with the given assertion.
        """
        return AssertionChain(lambda value: assertion(self(value)))

    def __or__(
        self, _assertion: Assertion[_AssertionReturnT, _AssertionsExtendReturnT]
    ) -> AssertionChain[_AssertionValueT, _AssertionsExtendReturnT]:
        return self.chain(_assertion)

    def __call__(self, value: _AssertionValueT) -> _AssertionReturnT:
        """
        Invoke the chain with a value.

        This method may be called more than once.

        :raises betty.exception.HumanFacingException: Raised if any part of the
            assertion chain fails.
        """
        return self._assertion(value)


@internal
@dataclass(frozen=True)
class Field(Generic[_AssertionValueT, _AssertionReturnT]):
    """
    A key-value mapping field.

    Do not instantiate this class directly. Use :py:class:`betty.assertion.RequiredField` or
    :py:class:`betty.assertion.OptionalField` instead.
    """

    name: str
    assertion: Assertion[_AssertionValueT, _AssertionReturnT] | None = None
    as_name: str | None = None


@final
@dataclass(frozen=True)
class RequiredField(
    Generic[_AssertionValueT, _AssertionReturnT],
    Field[_AssertionValueT, _AssertionReturnT],
):
    """
    A required key-value mapping field.
    """


@final
@dataclass(frozen=True)
class OptionalField(
    Generic[_AssertionValueT, _AssertionReturnT],
    Field[_AssertionValueT, _AssertionReturnT],
):
    """
    An optional key-value mapping field.
    """


_AssertionBuilderFunction = Callable[[_AssertionValueT], _AssertionReturnT]
_AssertionBuilderMethod = Callable[[object, _AssertionValueT], _AssertionReturnT]
_AssertionBuilder = "_AssertionBuilderFunction[ValueT, ReturnT] | _AssertionBuilderMethod[ValueT, ReturnT]"


_AssertTypeType: TypeAlias = (
    bool | float | int | Mapping[Any, Any] | None | Sequence[Any] | str
)
_AssertTypeTypeT = TypeVar("_AssertTypeTypeT", bound=_AssertTypeType)


def _assert_type_violation_error_message(
    asserted_type: type[_AssertTypeType], /
) -> Localizable:
    messages: Mapping[type[_AssertTypeType], Localizable] = {
        bool: _("This must be a boolean."),
        int: _("This must be a whole number."),
        float: _("This must be a decimal number."),
        Mapping: _("This must be a key-value mapping."),
        NoneType: _("This must be none/null."),
        Sequence: _("This must be a sequence."),
        str: _("This must be a string."),
    }
    return messages[asserted_type]


def _assert_type(
    value: Any,
    value_required_type: type[_AssertTypeTypeT],
    value_disallowed_type: type[_AssertTypeType] | None = None,
    /,
) -> _AssertTypeTypeT:
    if isinstance(value, value_required_type) and (
        value_disallowed_type is None or not isinstance(value, value_disallowed_type)
    ):
        return value
    raise HumanFacingException(
        _assert_type_violation_error_message(
            value_required_type,  # type: ignore[arg-type]
        )
    )


def assert_or(
    if_assertion: Assertion[_AssertionValueT, _AssertionReturnT],
    else_assertion: Assertion[_AssertionValueT, _AssertionReturnU],
    /,
) -> AssertionChain[_AssertionValueT, _AssertionReturnT | _AssertionReturnU]:
    """
    Assert that at least one of the given assertions passed.
    """

    def _assert_or(value: Any, /) -> _AssertionReturnT | _AssertionReturnU:
        assertions = (if_assertion, else_assertion)
        errors = HumanFacingExceptionGroup()
        for assertion in assertions:
            try:
                return assertion(value)
            except HumanFacingException as e:
                errors.append(e)
        raise errors

    return AssertionChain(_assert_or)


def assert_none() -> AssertionChain[Any, None]:
    """
    Assert that a value is ``None``.
    """

    def _assert_none(value: Any, /) -> None:
        _assert_type(value, NoneType)

    return AssertionChain(_assert_none)


def assert_bool() -> AssertionChain[Any, bool]:
    """
    Assert that a value is a Python ``bool``.
    """

    def _assert_bool(value: Any, /) -> bool:
        return _assert_type(value, bool)

    return AssertionChain(_assert_bool)


def assert_int() -> AssertionChain[Any, int]:
    """
    Assert that a value is a Python ``int``.
    """

    def _assert_int(value: Any, /) -> int:
        return _assert_type(value, int, bool)

    return AssertionChain(_assert_int)


def assert_float() -> AssertionChain[Any, float]:
    """
    Assert that a value is a Python ``float``.
    """

    def _assert_float(value: Any, /) -> float:
        return _assert_type(value, float)

    return AssertionChain(_assert_float)


def assert_number() -> AssertionChain[Any, Number]:
    """
    Assert that a value is a number (a Python ``int`` or ``float``).
    """
    return assert_or(assert_int(), assert_float())


def assert_positive_number() -> AssertionChain[Any, Number]:
    """
    Assert that a value is a positive nu,ber.
    """

    def _assert_positive_number(number: int | float, /) -> Number:
        if number <= 0:
            raise HumanFacingException(_("This must be a positive number."))
        return number

    return assert_number() | _assert_positive_number


def assert_str(
    *,
    exact_length: int | None = None,
    minimum_length: int | None = None,
    maximum_length: int | None = None,
) -> AssertionChain[Any, str]:
    """
    Assert that a value is a Python ``str``.
    """

    def _assert_str(value: Any, /) -> str:
        string = _assert_type(value, str)
        actual = len(value)
        if exact_length is not None and actual != exact_length:
            raise HumanFacingException(
                _("This must be {length} characters long.").format(
                    length=str(exact_length)
                )
            )
        if minimum_length is not None and actual < minimum_length:
            raise HumanFacingException(
                _("This must be at least {length} characters long.").format(
                    length=str(minimum_length)
                )
            )
        if maximum_length is not None and actual > maximum_length:
            raise HumanFacingException(
                _("This must be at most {length} characters long.").format(
                    length=str(maximum_length)
                )
            )
        return string

    return AssertionChain(_assert_str)


@overload
def assert_sequence(
    value_assertion: None = None, /
) -> AssertionChain[Any, MutableSequence[Any]]:
    pass


@overload
def assert_sequence(
    value_assertion: Assertion[Any, _AssertionReturnT], /
) -> AssertionChain[Any, MutableSequence[_AssertionReturnT]]:
    pass


def assert_sequence(
    value_assertion: Assertion[Any, _AssertionReturnT] | None = None, /
):
    """
    Assert that a value is a sequence.

    Optionally assert that values are of a given type.
    """

    def _assert_sequence(value: Any, /) -> MutableSequence[_AssertionReturnT]:
        sequence = _assert_type(
            value,
            Sequence,  # type: ignore[type-abstract]
        )
        if value_assertion is None:
            return list(sequence)
        asserted_sequence = []
        with HumanFacingExceptionGroup() as errors:
            for value_index, value_value in enumerate(sequence):
                with errors.absorb(Index(value_index)):
                    asserted_sequence.append(value_assertion(value_value))
        return asserted_sequence

    return AssertionChain(_assert_sequence)


@overload
def assert_mapping(
    value_assertion: None = None, key_assertion: None = None, /
) -> AssertionChain[Any, MutableMapping[Any, Any]]:
    pass


@overload
def assert_mapping(
    value_assertion: Assertion[Any, _AssertionReturnT], key_assertion: None = None, /
) -> AssertionChain[Any, MutableMapping[Any, _AssertionReturnT]]:
    pass


@overload
def assert_mapping(
    value_assertion: None, key_assertion: Assertion[Any, _AssertionKeyT], /
) -> AssertionChain[Any, MutableMapping[_AssertionKeyT, Any]]:
    pass


@overload
def assert_mapping(
    value_assertion: Assertion[Any, _AssertionReturnT],
    key_assertion: Assertion[Any, _AssertionKeyT],
    /,
) -> AssertionChain[Any, MutableMapping[_AssertionKeyT, _AssertionReturnT]]:
    pass


def assert_mapping(
    value_assertion: Assertion[Any, _AssertionReturnT] | None = None,
    key_assertion: Assertion[Any, _AssertionKeyT] | None = None,
    /,
):
    """
    Assert that a value is a key-value mapping.

    Optionally assert that keys and/or values are of a given type.
    """

    def _assert_mapping(
        value: Any, /
    ) -> MutableMapping[_AssertionKeyT, _AssertionReturnT]:
        mapping = _assert_type(
            value,
            Mapping,  # type: ignore[type-abstract]
        )
        if value_assertion is None and key_assertion is None:
            return dict(mapping)
        asserted_mapping = {}
        with HumanFacingExceptionGroup() as errors:
            for value_key, value_value in mapping.items():
                asserted_value_key = value_key
                if key_assertion:
                    with errors.absorb(Key(value_key)):
                        asserted_value_key = key_assertion(value_key)
                asserted_value_value = value_value
                if value_assertion:
                    with errors.absorb(Key(value_key)):
                        asserted_value_value = value_assertion(value_value)
                asserted_mapping[asserted_value_key] = asserted_value_value
        return asserted_mapping

    return AssertionChain(_assert_mapping)


def assert_record(
    *fields: Field[Any, Any],
) -> AssertionChain[Any, MutableMapping[str, Any]]:
    """
    Assert that a value is a record: a key-value mapping of arbitrary value types, with a known structure.

    To validate a key-value mapping as a records, assertions for all possible keys
    MUST be provided. Any keys present in the value for which no field assertions
    are provided will cause the entire record assertion to fail.
    """

    def _assert_record(value: Mapping[Any, Any], /) -> MutableMapping[str, Any]:
        known_keys = {x.name for x in fields}
        unknown_keys = set(value.keys()) - known_keys
        record: MutableMapping[str, Any] = {}
        with HumanFacingExceptionGroup() as errors:
            for unknown_key in unknown_keys:
                with errors.absorb(Key(unknown_key)):
                    raise HumanFacingException(
                        Paragraph(
                            _("Unknown key: {unknown_key}.").format(
                                unknown_key=f'"{unknown_key}"'
                            ),
                            do_you_mean(*(f'"{x}"' for x in sorted(known_keys))),
                        )
                    )
            for field in fields:
                with errors.absorb(Key(field.name)):
                    if field.name in value:
                        record[
                            field.name if field.as_name is None else field.as_name
                        ] = (
                            field.assertion(value[field.name])
                            if field.assertion
                            else value[field.name]
                        )
                    elif isinstance(field, RequiredField):
                        raise HumanFacingException(_("This field is required."))
        return record

    return assert_mapping() | _assert_record


def assert_isinstance(
    alleged_type: type[_AssertionValueT], /
) -> Assertion[Any, _AssertionValueT]:
    """
    Assert that a value is an instance of the given type.

    This assertion is **NOT** optimized to be user-facing (it is untranslated)
    because Python types are not user-facing.
    """

    def _assert(value: Any, /) -> _AssertionValueT:
        if isinstance(value, alleged_type):
            return value
        raise HumanFacingException(f"{value} must be an instance of {alleged_type}.")

    return _assert


def assert_path() -> AssertionChain[Any, Path]:
    """
    Assert that a value is a path to a file or directory on disk that may or may not exist.
    """
    return assert_or(assert_isinstance(Path), assert_str() | Path).chain(
        lambda value: value.expanduser().resolve()
    )


def assert_directory_path() -> AssertionChain[Any, Path]:
    """
    Assert that a value is a path to an existing directory.
    """

    def _assert_directory_path(directory_path: Path, /) -> Path:
        if directory_path.is_dir():
            return directory_path
        raise HumanFacingException(
            _('"{path}" is not a directory.').format(path=str(directory_path))
        )

    return assert_path() | _assert_directory_path


def assert_file_path() -> AssertionChain[Any, Path]:
    """
    Assert that a value is a path to an existing file.
    """

    def _assert_file_path(file_path: Path, /) -> Path:
        if file_path.is_file():
            return file_path
        raise FileNotFound(file_path)

    return assert_path() | _assert_file_path


def assert_locale() -> AssertionChain[Any, Locale]:
    """
    Assert that a value is a valid `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_.
    """
    return assert_str() | from_language_tag


_SizedT = TypeVar("_SizedT", bound=Sized)


@overload
def assert_len(exact: int, /) -> AssertionChain[Sized, Sized]:
    pass


@overload
def assert_len(
    *, minimum: int | None, maximum: int | None = None
) -> AssertionChain[Sized, Sized]:
    pass


@overload
def assert_len(
    *, minimum: int | None = None, maximum: int | None
) -> AssertionChain[Sized, Sized]:
    pass


def assert_len(
    exact: int | None = None, *, minimum: int | None = None, maximum: int | None = None
) -> AssertionChain[Sized, Sized]:
    """
    Assert the length of a value.

    This assertion can be used in two ways:
    - with an exact required length
    - with minimum and/or maximum bounds (inclusive)
    """

    def _assert_len(value: _SizedT, /) -> _SizedT:
        actual = len(value)
        if exact is not None and actual != exact:
            raise HumanFacingException(
                _("Exactly {expected} items are required, but found {actual}.").format(
                    expected=str(exact), actual=str(actual)
                )
            )
        if minimum is not None and actual < minimum:
            raise HumanFacingException(
                _("At least {expected} items are required, but found {actual}.").format(
                    expected=str(minimum), actual=str(actual)
                )
            )
        if maximum is not None and actual > maximum:
            raise HumanFacingException(
                _("At most {expected} items are allowed, but found {actual}.").format(
                    expected=str(maximum), actual=str(actual)
                )
            )
        return value

    return AssertionChain(_assert_len)


def assert_enum(options: type[_EnumT]) -> AssertionChain[Any, _EnumT]:
    """
    Assert that a value is allowed by an enum, and return the enum value.
    """

    def _assert_enum(value: Any) -> Any:
        try:
            return options(value)
        except ValueError:
            raise HumanFacingException(
                Paragraph(
                    _("Invalid option {value}.").format(value=str(value)),
                    do_you_mean(*[option.value for option in options]),
                )
            ) from None

    return AssertionChain(_assert_enum)
