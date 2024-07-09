"""
The Assertion API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import NoneType
from typing import (
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

from betty.assertion.error import AssertionFailedGroup, AssertionFailed
from betty.locale import (
    LocaleNotFoundError,
    get_data,
    UNDETERMINED_LOCALE,
)
from betty.locale.localizable import _, plain, Localizable
from betty.model import (
    Entity,
    get_entity_type,
    EntityTypeImportError,
    EntityTypeInvalidError,
    EntityTypeError,
)
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Mapping

Number: TypeAlias = int | float


_AssertionValueT = TypeVar("_AssertionValueT")
_AssertionReturnT = TypeVar("_AssertionReturnT")
_AssertionReturnU = TypeVar("_AssertionReturnU")

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

    def __init__(self, _assertion: Assertion[_AssertionValueT, _AssertionReturnT]):
        self._assertion = _assertion

    def chain(
        self, assertion: Assertion[_AssertionReturnT, _AssertionsExtendReturnT]
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


_AssertionBuilderFunction = Callable[[_AssertionValueT], _AssertionReturnT]
_AssertionBuilderMethod = Callable[[object, _AssertionValueT], _AssertionReturnT]
_AssertionBuilder = "_AssertionBuilderFunction[ValueT, ReturnT] | _AssertionBuilderMethod[ValueT, ReturnT]"


AssertTypeType: TypeAlias = bool | dict[Any, Any] | float | int | list[Any] | None | str
AssertTypeTypeT = TypeVar("AssertTypeTypeT", bound=AssertTypeType)


def _assert_type_violation_error_message(
    asserted_type: type[AssertTypeType],
) -> Localizable:
    messages: Mapping[type[AssertTypeType], Localizable] = {
        NoneType: _("This must be none/null."),
        bool: _("This must be a boolean."),
        int: _("This must be a whole number."),
        float: _("This must be a decimal number."),
        str: _("This must be a string."),
        list: _("This must be a list."),
        dict: _("This must be a key-value mapping."),
    }
    return messages[asserted_type]


def _assert_type(
    value: Any,
    value_required_type: type[AssertTypeTypeT],
    value_disallowed_type: type[AssertTypeType] | None = None,
) -> AssertTypeTypeT:
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
) -> AssertionChain[_AssertionValueT, _AssertionReturnT | _AssertionReturnU]:
    """
    Assert that at least one of the given assertions passed.
    """

    def _assert_or(value: Any) -> _AssertionReturnT | _AssertionReturnU:
        assertions = (if_assertion, else_assertion)
        errors = AssertionFailedGroup()
        for assertion in assertions:
            try:
                return assertion(value)
            except AssertionFailed as e:
                if e.raised(AssertionFailed):
                    errors.append(e)
        raise errors

    return AssertionChain(_assert_or)


def assert_none() -> AssertionChain[Any, None]:
    """
    Assert that a value is ``None``.
    """

    def _assert_none(value: Any) -> None:
        _assert_type(value, NoneType)

    return AssertionChain(_assert_none)


def assert_bool() -> AssertionChain[Any, bool]:
    """
    Assert that a value is a Python ``bool``.
    """

    def _assert_bool(value: Any) -> bool:
        return _assert_type(value, bool)

    return AssertionChain(_assert_bool)


def assert_int() -> AssertionChain[Any, int]:
    """
    Assert that a value is a Python ``int``.
    """

    def _assert_int(value: Any) -> int:
        return _assert_type(value, int, bool)

    return AssertionChain(_assert_int)


def assert_float() -> AssertionChain[Any, float]:
    """
    Assert that a value is a Python ``float``.
    """

    def _assert_float(value: Any) -> float:
        return _assert_type(value, float)

    return AssertionChain(_assert_float)


def assert_number() -> AssertionChain[Any, Number]:
    """
    Assert that a value is a number (a Python ``int`` or ``float``).
    """
    return assert_or(assert_int(), assert_float())


def assert_positive_number() -> AssertionChain[Any, Number]:
    """
    Assert that a vaue is a positive nu,ber.
    """

    def _assert_positive_number(
        value: Any,
    ) -> Number:
        value = assert_number()(value)
        if value <= 0:
            raise AssertionFailed(_("This must be a positive number."))
        return value

    return AssertionChain(_assert_positive_number)


def assert_str() -> AssertionChain[Any, str]:
    """
    Assert that a value is a Python ``str``.
    """

    def _assert_str(value: Any) -> str:
        return _assert_type(value, str)

    return AssertionChain(_assert_str)


def assert_list() -> AssertionChain[Any, list[Any]]:
    """
    Assert that a value is a Python ``list``.
    """

    def _assert_list(value: Any) -> list[Any]:
        return _assert_type(value, list)

    return AssertionChain(_assert_list)


def assert_dict() -> AssertionChain[Any, dict[str, Any]]:
    """
    Assert that a value is a Python ``dict``.
    """

    def _assert_dict(value: Any) -> dict[str, Any]:
        return _assert_type(value, dict)

    return AssertionChain(_assert_dict)


def assert_sequence(
    item_assertion: Assertion[Any, _AssertionReturnT],
) -> AssertionChain[Any, MutableSequence[_AssertionReturnT]]:
    """
    Assert that a value is a sequence and that all item values are of the given type.
    """

    def _assert_sequence(value: Any) -> MutableSequence[_AssertionReturnT]:
        list_value = assert_list()(value)
        sequence: MutableSequence[_AssertionReturnT] = []
        with AssertionFailedGroup().assert_valid() as errors:
            for value_item_index, value_item_value in enumerate(list_value):
                with errors.catch(plain(value_item_index)):
                    sequence.append(item_assertion(value_item_value))
        return sequence

    return AssertionChain(_assert_sequence)


def assert_mapping(
    item_assertion: Assertion[Any, _AssertionReturnT],
) -> AssertionChain[Any, MutableMapping[str, _AssertionReturnT]]:
    """
    Assert that a value is a key-value mapping and assert that all item values are of the given type.
    """

    def _assert_mapping(value: Any) -> MutableMapping[str, _AssertionReturnT]:
        dict_value = assert_dict()(value)
        mapping: MutableMapping[str, _AssertionReturnT] = {}
        with AssertionFailedGroup().assert_valid() as errors:
            for value_item_key, value_item_value in dict_value.items():
                with errors.catch(plain(value_item_key)):
                    mapping[value_item_key] = item_assertion(value_item_value)
        return mapping

    return AssertionChain(_assert_mapping)


def assert_fields(
    *fields: _Field[Any, Any],
) -> AssertionChain[Any, MutableMapping[str, Any]]:
    """
    Assert that a value is a key-value mapping of arbitrary value types, and assert several of its values.
    """

    def _assert_fields(value: Any) -> MutableMapping[str, Any]:
        value_dict = assert_dict()(value)
        mapping: MutableMapping[str, Any] = {}
        with AssertionFailedGroup().assert_valid() as errors:
            for field in fields:
                with errors.catch(plain(field.name)):
                    if field.name in value_dict:
                        if field.assertion:
                            mapping[field.name] = field.assertion(
                                value_dict[field.name]
                            )
                    elif isinstance(field, RequiredField):
                        raise AssertionFailed(_("This field is required."))
        return mapping

    return AssertionChain(_assert_fields)


@overload
def assert_field(
    field: RequiredField[_AssertionValueT, _AssertionReturnT],
) -> AssertionChain[_AssertionValueT, _AssertionReturnT]:
    pass  # pragma: no cover


@overload
def assert_field(
    field: OptionalField[_AssertionValueT, _AssertionReturnT],
) -> AssertionChain[_AssertionValueT, _AssertionReturnT | type[Void]]:
    pass  # pragma: no cover


def assert_field(
    field: _Field[_AssertionValueT, _AssertionReturnT],
) -> (
    AssertionChain[_AssertionValueT, _AssertionReturnT]
    | AssertionChain[_AssertionValueT, _AssertionReturnT | type[Void]]
):
    """
    Assert that a value is a key-value mapping of arbitrary value types, and assert a single of its values.
    """

    def _assert_field(value: Any) -> _AssertionReturnT | type[Void]:
        fields = assert_fields(field)(value)
        try:
            return cast("_AssertionReturnT | type[Void]", fields[field.name])
        except KeyError:
            if isinstance(field, RequiredField):
                raise
            return Void

    return AssertionChain(_assert_field)


def assert_record(
    *fields: _Field[Any, Any],
) -> AssertionChain[Any, MutableMapping[str, Any]]:
    """
    Assert that a value is a record: a key-value mapping of arbitrary value types, with a known structure.

    To validate a key-value mapping as a records, assertions for all possible keys
    MUST be provided. Any keys present in the value for which no field assertions
    are provided will cause the entire record assertion to fail.
    """
    if not len(fields):
        raise ValueError("One or more fields are required.")

    def _assert_record(value: Any) -> MutableMapping[str, Any]:
        dict_value = assert_dict()(value)
        known_keys = {x.name for x in fields}
        unknown_keys = set(dict_value.keys()) - known_keys
        with AssertionFailedGroup().assert_valid() as errors:
            for unknown_key in unknown_keys:
                with errors.catch(plain(unknown_key)):
                    raise AssertionFailed(
                        _(
                            "Unknown key: {unknown_key}. Did you mean {known_keys}?"
                        ).format(
                            unknown_key=f'"{unknown_key}"',
                            known_keys=", ".join(
                                (f'"{x}"' for x in sorted(known_keys))
                            ),
                        )
                    )
            return assert_fields(*fields)(dict_value)

    return AssertionChain(_assert_record)


def assert_path() -> AssertionChain[Any, Path]:
    """
    Assert that a value is a path to a file or directory on disk that may or may not exist.
    """
    return assert_str().chain(lambda value: Path(value).expanduser().resolve())


def assert_directory_path() -> AssertionChain[Any, Path]:
    """
    Assert that a value is a path to an existing directory.
    """

    def _assert_directory_path(value: Any) -> Path:
        directory_path = assert_path()(value)
        if directory_path.is_dir():
            return directory_path
        raise AssertionFailed(_('"{path}" is not a directory.').format(path=value))

    return AssertionChain(_assert_directory_path)


def assert_locale() -> AssertionChain[Any, str]:
    """
    Assert that a value is a valid `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_.
    """

    def _assert_locale(
        value: Any,
    ) -> str:
        value = assert_str()(value)

        # Allow locales for which no system information usually exists.
        if value == UNDETERMINED_LOCALE:
            return value

        try:
            get_data(value)
            return value
        except LocaleNotFoundError:
            raise AssertionFailed(
                _('"{locale}" is not a valid IETF BCP 47 language tag.').format(
                    locale=value
                )
            ) from None

    return AssertionChain(_assert_locale)


def assert_setattr(
    instance: object,
    attr_name: str,
) -> AssertionChain[Any, Any]:
    """
    Set a value for the given object's attribute.
    """

    def _assert_setattr(value: Any) -> Any:
        setattr(instance, attr_name, value)
        # Return the getter's return value rather than the assertion value, just
        # in case the setter and/or getter perform changes to the value.
        return getattr(instance, attr_name)

    return AssertionChain(_assert_setattr)


def assert_entity_type() -> AssertionChain[Any, type[Entity]]:
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
                _(
                    'Cannot find and import "{entity_type}".',
                ).format(entity_type=str(value))
            ) from None
        except EntityTypeInvalidError:
            raise AssertionFailed(
                _('"{entity_type}" is not a valid Betty entity type.').format(
                    entity_type=str(value)
                )
            ) from None
        except EntityTypeError:
            raise AssertionFailed(
                _(
                    'Cannot determine the entity type for "{entity_type}". Did you perhaps make a typo, or could it be that the entity type comes from another package that is not yet installed?'
                ).format(entity_type=str(value))
            ) from None

    return AssertionChain(_assert_entity_type)
