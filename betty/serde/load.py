"""
Provide a deserialization API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import (
    Iterator,
    Callable,
    Any,
    Generic,
    TYPE_CHECKING,
    TypeVar,
    MutableSequence,
    MutableMapping,
    overload,
    cast,
    TypeAlias,
)

from betty.locale import LocaleNotFoundError, get_data, Str, Localizable
from betty.model import (
    Entity,
    get_entity_type,
    EntityTypeImportError,
    EntityTypeInvalidError,
    EntityTypeError,
)
from betty.serde.dump import DumpType, Void
from betty.serde.error import SerdeError, SerdeErrorCollection

if TYPE_CHECKING:
    from betty.app.extension import Extension


_DumpTypeT = TypeVar("_DumpTypeT", bound=DumpType)
_AssertionValueT = TypeVar("_AssertionValueT")
_AssertionReturnT = TypeVar("_AssertionReturnT")
_AssertionReturnU = TypeVar("_AssertionReturnU")

Assertion: TypeAlias = Callable[
    [
        _AssertionValueT,
    ],
    _AssertionReturnT,
]


Number: TypeAlias = int | float


class LoadError(SerdeError):
    """
    Raised for any error while deserializing data.
    """

    pass  # pragma: no cover


class AssertionFailed(LoadError):
    """
    Raised when an assertion failed while deserializing data.
    """

    pass  # pragma: no cover


class FormatError(LoadError):
    """
    Raised when data that is being deserialized is provided in an unknown (undeserializable) format.
    """

    pass  # pragma: no cover


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

    def __init__(self, _assertion: Assertion[_AssertionValueT, _AssertionReturnT]):
        self._assertion = _assertion

    def extend(
        self, assertion: Assertion[_AssertionReturnT, _AssertionsExtendReturnT]
    ) -> AssertionChain[_AssertionValueT, _AssertionsExtendReturnT]:
        """
        Extend the chain with the given assertion.
        """
        return AssertionChain(lambda value: assertion(self(value)))

    def __or__(
        self, _assertion: Assertion[_AssertionReturnT, _AssertionsExtendReturnT]
    ) -> AssertionChain[_AssertionValueT, _AssertionsExtendReturnT]:
        return self.extend(_assertion)

    def __call__(self, value: _AssertionValueT) -> _AssertionReturnT:
        """
        Invoke the chain with a value.

        This method may be called more than once.
        """
        return self._assertion(value)


@dataclass(frozen=True)
class _Field(Generic[_AssertionValueT, _AssertionReturnT]):
    name: str
    assertion: Assertion[_AssertionValueT, _AssertionReturnT] | None = None


@dataclass(frozen=True)
class RequiredField(
    Generic[_AssertionValueT, _AssertionReturnT],
    _Field[_AssertionValueT, _AssertionReturnT],
):
    """
    A required key-value mapping field.
    """

    pass  # pragma: no cover


@dataclass(frozen=True)
class OptionalField(
    Generic[_AssertionValueT, _AssertionReturnT],
    _Field[_AssertionValueT, _AssertionReturnT],
):
    """
    An optional key-value mapping field.
    """

    pass  # pragma: no cover


class Fields:
    """
    A sequence of fields, used to assert key-value mappings.
    """

    def __init__(self, *fields: _Field[Any, Any]):
        self._fields = fields

    def __iter__(self) -> Iterator[_Field[Any, Any]]:
        return (field for field in self._fields)


_AssertionBuilderFunction = Callable[[_AssertionValueT], _AssertionReturnT]
_AssertionBuilderMethod = Callable[[object, _AssertionValueT], _AssertionReturnT]
_AssertionBuilder = "_AssertionBuilderFunction[ValueT, ReturnT] | _AssertionBuilderMethod[ValueT, ReturnT]"


def _assert_type_violation_error_message(
    asserted_type: type[DumpType],
) -> Localizable:
    messages = {
        None: Str._("This must be none/null."),
        bool: Str._("This must be a boolean."),
        int: Str._("This must be a whole number."),
        float: Str._("This must be a decimal number."),
        str: Str._("This must be a string."),
        list: Str._("This must be a list."),
        dict: Str._("This must be a key-value mapping."),
    }
    return messages[asserted_type]  # type: ignore[index]


def _assert_type(
    value: Any,
    value_required_type: type[_DumpTypeT],
    value_disallowed_type: type[DumpType] | None = None,
) -> _DumpTypeT:
    if isinstance(value, value_required_type) and (
        value_disallowed_type is None or not isinstance(value, value_disallowed_type)
    ):
        return value
    raise AssertionFailed(
        _assert_type_violation_error_message(
            value_required_type,  # type: ignore[arg-type]
        )
    )


def assert_or(
    if_assertion: Assertion[_AssertionValueT, _AssertionReturnT],
    else_assertion: Assertion[_AssertionValueT, _AssertionReturnU],
) -> Assertion[_AssertionValueT, _AssertionReturnT | _AssertionReturnU]:
    """
    Assert that at least one of the given assertions passed.
    """

    def _assert_or(value: Any) -> _AssertionReturnT | _AssertionReturnU:
        assertions = (if_assertion, else_assertion)
        errors = SerdeErrorCollection()
        for assertion in assertions:
            try:
                return assertion(value)
            except SerdeError as e:
                if e.raised(AssertionFailed):
                    errors.append(e)
        raise errors

    return _assert_or


def assert_none() -> Assertion[Any, None]:
    """
    Assert that a value is ``None``.
    """

    def _assert_none(value: Any) -> None:
        _assert_type(value, type(None))

    return _assert_none


def assert_bool() -> Assertion[Any, bool]:
    """
    Assert that a value is a Python ``bool``.
    """

    def _assert_bool(value: Any) -> bool:
        return _assert_type(value, bool)

    return _assert_bool


def assert_int() -> Assertion[Any, int]:
    """
    Assert that a value is a Python ``int``.
    """

    def _assert_int(value: Any) -> int:
        return _assert_type(value, int, bool)

    return _assert_int


def assert_float() -> Assertion[Any, float]:
    """
    Assert that a value is a Python ``float``.
    """

    def _assert_float(value: Any) -> float:
        return _assert_type(value, float)

    return _assert_float


def assert_number() -> Assertion[Any, Number]:
    """
    Assert that a value is a number (a Python ``int`` or ``float``).
    """
    return assert_or(assert_int(), assert_float())


def assert_positive_number() -> Assertion[Any, Number]:
    """
    Assert that a vaue is a positive nu,ber.
    """

    def _assert_positive_number(
        value: Any,
    ) -> Number:
        value = assert_number()(value)
        if value <= 0:
            raise AssertionFailed(Str._("This must be a positive number."))
        return value

    return _assert_positive_number


def assert_str() -> Assertion[Any, str]:
    """
    Assert that a value is a Python ``str``.
    """

    def _assert_str(value: Any) -> str:
        return _assert_type(value, str)

    return _assert_str


def assert_list() -> Assertion[Any, list[Any]]:
    """
    Assert that a value is a Python ``list``.
    """

    def _assert_list(value: Any) -> list[Any]:
        return _assert_type(value, list)

    return _assert_list


def assert_dict() -> Assertion[Any, dict[str, Any]]:
    """
    Assert that a value is a Python ``dict``.
    """

    def _assert_dict(value: Any) -> dict[str, Any]:
        return _assert_type(value, dict)

    return _assert_dict


def assert_sequence(
    item_assertion: Assertion[Any, _AssertionReturnT],
) -> Assertion[Any, MutableSequence[_AssertionReturnT]]:
    """
    Assert that a value is a sequence and that all item values are of the given type.
    """

    def _assert_sequence(value: Any) -> MutableSequence[_AssertionReturnT]:
        list_value = assert_list()(value)
        sequence: MutableSequence[_AssertionReturnT] = []
        with SerdeErrorCollection().assert_valid() as errors:
            for value_item_index, value_item_value in enumerate(list_value):
                with errors.catch(Str.plain(value_item_index)):
                    sequence.append(item_assertion(value_item_value))
        return sequence

    return _assert_sequence


def assert_mapping(
    item_assertion: Assertion[Any, _AssertionReturnT],
) -> Assertion[Any, MutableMapping[str, _AssertionReturnT]]:
    """
    Assert that a value is a key-value mapping and assert that all item values are of the given type.
    """

    def _assert_mapping(value: Any) -> MutableMapping[str, _AssertionReturnT]:
        dict_value = assert_dict()(value)
        mapping: MutableMapping[str, _AssertionReturnT] = {}
        with SerdeErrorCollection().assert_valid() as errors:
            for value_item_key, value_item_value in dict_value.items():
                with errors.catch(Str.plain(value_item_key)):
                    mapping[value_item_key] = item_assertion(value_item_value)
        return mapping

    return _assert_mapping


def assert_fields(fields: Fields) -> Assertion[Any, MutableMapping[str, Any]]:
    """
    Assert that a value is a key-value mapping of arbitrary value types, and assert several of its values.
    """

    def _assert_fields(value: Any) -> MutableMapping[str, Any]:
        value_dict = assert_dict()(value)
        mapping: MutableMapping[str, Any] = {}
        with SerdeErrorCollection().assert_valid() as errors:
            for field in fields:
                with errors.catch(Str.plain(field.name)):
                    if field.name in value_dict:
                        if field.assertion:
                            mapping[field.name] = field.assertion(
                                value_dict[field.name]
                            )
                    elif isinstance(field, RequiredField):
                        raise AssertionFailed(Str._("This field is required."))
        return mapping

    return _assert_fields


@overload
def assert_field(
    field: RequiredField[_AssertionValueT, _AssertionReturnT],
) -> Assertion[_AssertionValueT, _AssertionReturnT]:
    pass  # pragma: no cover


@overload
def assert_field(
    field: OptionalField[_AssertionValueT, _AssertionReturnT],
) -> Assertion[_AssertionValueT, _AssertionReturnT | type[Void]]:
    pass  # pragma: no cover


def assert_field(
    field: _Field[_AssertionValueT, _AssertionReturnT],
) -> Assertion[_AssertionValueT, _AssertionReturnT | type[Void]]:
    """
    Assert that a value is a key-value mapping of arbitrary value types, and assert a single of its values.
    """

    def _assert_field(value: Any) -> _AssertionReturnT | type[Void]:
        fields = assert_fields(Fields(field))(value)
        try:
            return cast("_AssertionReturnT | type[Void]", fields[field.name])
        except KeyError:
            if isinstance(field, RequiredField):
                raise
            return Void

    return _assert_field


def assert_record(fields: Fields) -> Assertion[Any, MutableMapping[str, Any]]:
    """
    Assert that a value is a record: a key-value mapping of arbitrary value types, with a known structure.

    To validate a key-value mapping as a records, assertions for all possible keys
    MUST be provided. Any keys present in the value for which no field assertions
    are provided will cause the entire record assertion to fail.
    """
    if not len(list(fields)):
        raise ValueError("One or more fields are required.")

    def _assert_record(value: Any) -> MutableMapping[str, Any]:
        dict_value = assert_dict()(value)
        known_keys = {x.name for x in fields}
        unknown_keys = set(dict_value.keys()) - known_keys
        with SerdeErrorCollection().assert_valid() as errors:
            for unknown_key in unknown_keys:
                with errors.catch(Str.plain(unknown_key)):
                    raise AssertionFailed(
                        Str._(
                            "Unknown key: {unknown_key}. Did you mean {known_keys}?",
                            unknown_key=f'"{unknown_key}"',
                            known_keys=", ".join(
                                (f'"{x}"' for x in sorted(known_keys))
                            ),
                        )
                    )
            return assert_fields(fields)(dict_value)

    return _assert_record


def assert_path() -> Assertion[Any, Path]:
    """
    Assert that a value is a path to a file or directory on disk that may or may not exist.
    """

    def _assert_path(value: Any) -> Path:
        assert_str()(value)
        return Path(value).expanduser().resolve()

    return _assert_path


def assert_directory_path() -> Assertion[Any, Path]:
    """
    Assert that a value is a path to an existing directory.
    """

    def _assert_directory_path(value: Any) -> Path:
        directory_path = assert_path()(value)
        if directory_path.is_dir():
            return directory_path
        raise AssertionFailed(
            Str._(
                '"{path}" is not a directory.',
                path=value,
            )
        )

    return _assert_directory_path


def assert_locale() -> Assertion[Any, str]:
    """
    Assert that a value is a valid `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_.
    """

    def _assert_locale(
        value: Any,
    ) -> str:
        value = assert_str()(value)
        try:
            get_data(value)
            return value
        except LocaleNotFoundError:
            raise AssertionFailed(
                Str._(
                    '"{locale}" is not a valid IETF BCP 47 language tag.',
                    locale=value,
                )
            ) from None

    return _assert_locale


def assert_setattr(
    instance: object, attr_name: str
) -> Assertion[_AssertionValueT, _AssertionValueT]:
    """
    Set a value for the given object's attribute.
    """

    def _assert_setattr(value: _AssertionValueT) -> _AssertionValueT:
        setattr(instance, attr_name, value)
        return value

    return _assert_setattr


def assert_extension_type() -> Assertion[Any, type[Extension]]:
    """
    Assert that a value is an extension type.

    This assertion passes if the value is fully qualified :py:class:`betty.app.extension.Extension` subclass name.
    """

    def _assert_extension_type(
        value: Any,
    ) -> type[Extension]:
        from betty.app.extension import (
            get_extension_type,
            ExtensionTypeImportError,
            ExtensionTypeInvalidError,
            ExtensionTypeError,
        )

        assert_str()(value)
        try:
            return get_extension_type(value)
        except ExtensionTypeImportError:
            raise AssertionFailed(
                Str._(
                    'Cannot find and import "{extension_type}".',
                    extension_type=str(value),
                )
            ) from None
        except ExtensionTypeInvalidError:
            raise AssertionFailed(
                Str._(
                    '"{extension_type}" is not a valid Betty extension type.',
                    extension_type=str(value),
                )
            ) from None
        except ExtensionTypeError:
            raise AssertionFailed(
                Str._(
                    'Cannot determine the extension type for "{extension_type}". Did you perhaps make a typo, or could it be that the extension type comes from another package that is not yet installed?',
                    extension_type=str(value),
                )
            ) from None

    return _assert_extension_type


def assert_entity_type() -> Assertion[Any, type[Entity]]:
    """
    Assert that a value is an entity type.

    This assertion passes if the value is fully qualified :py:class:`betty.model.Entity` subclass name.
    """

    def _assert_entity_type(
        value: Any,
    ) -> type[Entity]:
        assert_str()(value)
        try:
            return get_entity_type(value)
        except EntityTypeImportError:
            raise AssertionFailed(
                Str._(
                    'Cannot find and import "{entity_type}".',
                    entity_type=str(value),
                )
            ) from None
        except EntityTypeInvalidError:
            raise AssertionFailed(
                Str._(
                    '"{entity_type}" is not a valid Betty entity type.',
                    entity_type=str(value),
                )
            ) from None
        except EntityTypeError:
            raise AssertionFailed(
                Str._(
                    'Cannot determine the entity type for "{entity_type}". Did you perhaps make a typo, or could it be that the entity type comes from another package that is not yet installed?',
                    entity_type=str(value),
                )
            ) from None

    return _assert_entity_type
