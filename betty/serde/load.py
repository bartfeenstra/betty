from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Callable, Any, Generic, TYPE_CHECKING, TypeVar, MutableSequence, MutableMapping, overload, \
    cast, TypeAlias

from betty.functools import _Result
from betty.locale import LocaleNotFoundError, get_data, Str
from betty.model import Entity, get_entity_type, EntityTypeImportError, EntityTypeInvalidError, EntityTypeError
from betty.serde.dump import DumpType, DumpTypeT, Void
from betty.serde.error import SerdeError, SerdeErrorCollection

if TYPE_CHECKING:
    from betty.app.extension import Extension

T = TypeVar('T')
ValueT = TypeVar('ValueT')
ReturnT = TypeVar('ReturnT')
ReturnU = TypeVar('ReturnU')
CallValueT = TypeVar('CallValueT')
CallReturnT = TypeVar('CallReturnT')
FValueT = TypeVar('FValueT')
MapReturnT = TypeVar('MapReturnT')
Number: TypeAlias = int | float
NumberT = TypeVar('NumberT', bound=Number)


class LoadError(SerdeError):
    pass


class AssertionFailed(LoadError):
    pass


class FormatError(LoadError):
    pass


Assertion: TypeAlias = Callable[
    [
        ValueT,
    ],
    ReturnT,
]


class _Assertions(Generic[CallValueT, CallReturnT, FValueT]):
    def __init__(self, _assertion: Assertion[FValueT, CallReturnT]):
        self._assertion = _assertion

    def extend(self, _assertion: Assertion[CallReturnT, MapReturnT]) -> _Assertions[CallValueT, MapReturnT, CallReturnT]:
        return _AssertionExtension(_assertion, self)

    def __or__(self, _assertion: Assertion[CallReturnT, MapReturnT]) -> _Assertions[CallValueT, MapReturnT, CallReturnT]:
        return self.extend(_assertion)

    def __call__(self, value: CallValueT) -> _Result[CallReturnT]:
        raise NotImplementedError(repr(self))


class Assertions(_Assertions[CallValueT, CallReturnT, CallValueT], Generic[CallValueT, CallReturnT]):
    def __call__(self, value: CallValueT) -> _Result[CallReturnT]:
        return _Result(value).map(self._assertion)


class _AssertionExtension(_Assertions[CallValueT, CallReturnT, FValueT], Generic[CallValueT, CallReturnT, FValueT]):
    def __init__(
        self,
        _assertion: Assertion[FValueT, CallReturnT],
        extended_assertion: _Assertions[CallValueT, FValueT, Any],
    ):
        super().__init__(_assertion)
        self._extended_assertion = extended_assertion

    def __call__(self, value: CallValueT) -> _Result[CallReturnT]:
        return self._extended_assertion(value).map(self._assertion)


@dataclass(frozen=True)
class _Field(Generic[ValueT, ReturnT]):
    name: str
    assertion: _Assertions[ValueT, ReturnT, Any] | None = None


@dataclass(frozen=True)
class RequiredField(Generic[ValueT, ReturnT], _Field[ValueT, ReturnT]):
    pass


@dataclass(frozen=True)
class OptionalField(Generic[ValueT, ReturnT], _Field[ValueT, ReturnT]):
    pass


class Fields:
    def __init__(self, *fields: _Field[Any, Any]):
        self._fields = fields

    def __iter__(self) -> Iterator[_Field[Any, Any]]:
        return (field for field in self._fields)


_AssertionBuilderFunction = Callable[[ValueT], ReturnT]
_AssertionBuilderMethod = Callable[[object, ValueT], ReturnT]
_AssertionBuilder = '_AssertionBuilderFunction[ValueT, ReturnT] | _AssertionBuilderMethod[ValueT, ReturnT]'


class Asserter:
    def _assert_type_violation_error_message(
            self,
            asserted_type: type[DumpType],
    ) -> Str:
        messages = {
            None: Str._('This must be none/null.'),
            bool: Str._('This must be a boolean.'),
            int: Str._('This must be a whole number.'),
            float: Str._('This must be a decimal number.'),
            str: Str._('This must be a string.'),
            list: Str._('This must be a list.'),
            dict: Str._('This must be a key-value mapping.'),
        }
        return messages[asserted_type]  # type: ignore[index]

    def _assert_type(
        self,
        value: Any,
        value_required_type: type[DumpTypeT],
        value_disallowed_type: type[DumpType] | None = None,
    ) -> DumpTypeT:
        if isinstance(value, value_required_type) and (value_disallowed_type is None or not isinstance(value, value_disallowed_type)):
            return value
        raise AssertionFailed(
            self._assert_type_violation_error_message(
                value_required_type,  # type: ignore[arg-type]
            )
        )

    def assert_or(self, if_assertion: Assertion[ValueT, ReturnT], else_assertions: Assertion[ValueT, ReturnU]) -> Assertion[ValueT, ReturnT | ReturnU]:
        def _assert_or(value: Any) -> ReturnT | ReturnU:
            assertions = (if_assertion, else_assertions)
            errors = SerdeErrorCollection()
            for assertion in assertions:
                try:
                    return assertion(value)
                except SerdeError as e:
                    if e.raised(AssertionFailed):
                        errors.append(e)
            raise errors
        return _assert_or

    def assert_none(self) -> Assertion[Any, None]:
        def _assert_none(value: Any) -> None:
            self._assert_type(value, type(None))
        return _assert_none

    def assert_bool(self) -> Assertion[Any, bool]:
        def _assert_bool(value: Any) -> bool:
            return self._assert_type(value, bool)
        return _assert_bool

    def assert_int(self) -> Assertion[Any, int]:
        def _assert_int(value: Any) -> int:
            return self._assert_type(value, int, bool)
        return _assert_int

    def assert_float(self) -> Assertion[Any, float]:
        def _assert_float(value: Any) -> float:
            return self._assert_type(value, float)
        return _assert_float

    def assert_number(self) -> Assertion[Any, int | float]:
        return self.assert_or(self.assert_int(), self.assert_float())

    def assert_positive_number(self) -> Assertion[Any, Number]:
        def _assert_positive_number(
            value: Any,
        ) -> Number:
            value = self.assert_number()(value)
            if value <= 0:
                raise AssertionFailed(Str._('This must be a positive number.'))
            return value
        return _assert_positive_number

    def assert_str(self) -> Assertion[Any, str]:
        def _assert_str(value: Any) -> str:
            return self._assert_type(value, str)
        return _assert_str

    def assert_list(self) -> Assertion[Any, list[Any]]:
        def _assert_list(value: Any) -> list[Any]:
            return self._assert_type(value, list)
        return _assert_list

    def assert_dict(self) -> Assertion[Any, dict[str, Any]]:
        def _assert_dict(value: Any) -> dict[str, Any]:
            return self._assert_type(value, dict)
        return _assert_dict

    def assert_assertions(self, assertions: _Assertions[ValueT, ReturnT, Any]) -> Assertion[Any, ReturnT]:
        def _assert_assertions(value: Any) -> ReturnT:
            return assertions(value).value
        return _assert_assertions

    def assert_sequence(self, item_assertion: Assertions[ValueT, ReturnT]) -> Assertion[Any, MutableSequence[ReturnT]]:
        def _assert_sequence(value: ValueT) -> MutableSequence[ReturnT]:
            list_value = self.assert_list()(value)
            sequence = []
            with SerdeErrorCollection().assert_valid() as errors:
                for value_item_index, value_item_value in enumerate(list_value):
                    with errors.catch(Str.plain(value_item_index)):
                        sequence.append(self.assert_assertions(item_assertion)(value_item_value))
            return sequence
        return _assert_sequence

    def assert_mapping(self, item_assertion: Assertions[ValueT, ReturnT]) -> Assertion[Any, MutableMapping[str, ReturnT]]:
        def _assert_mapping(value: ValueT) -> MutableMapping[str, ReturnT]:
            dict_value = self.assert_dict()(value)
            mapping = {}
            with SerdeErrorCollection().assert_valid() as errors:
                for value_item_key, value_item_value in dict_value.items():
                    with errors.catch(Str.plain(value_item_key)):
                        mapping[value_item_key] = self.assert_assertions(item_assertion)(value_item_value)
            return mapping
        return _assert_mapping

    def assert_fields(self, fields: Fields) -> Assertion[Any, MutableMapping[str, Any]]:
        def _assert_fields(value: Any) -> MutableMapping[str, Any]:
            value_dict = self.assert_dict()(value)
            mapping = {}
            with SerdeErrorCollection().assert_valid() as errors:
                for field in fields:
                    with errors.catch(Str.plain(field.name)):
                        if field.name in value_dict:
                            if field.assertion:
                                mapping[field.name] = self.assert_assertions(field.assertion)(value_dict[field.name])
                        elif isinstance(field, RequiredField):
                            raise AssertionFailed(Str._('This field is required.'))
            return mapping
        return _assert_fields

    @overload
    def assert_field(self, field: RequiredField[ValueT, ReturnT]) -> Assertion[ValueT, ReturnT]:
        pass

    @overload
    def assert_field(self, field: OptionalField[ValueT, ReturnT]) -> Assertion[ValueT, ReturnT | type[Void]]:
        pass

    def assert_field(self, field: _Field[ValueT, ReturnT]) -> Assertion[ValueT, ReturnT | type[Void]]:
        def _assert_field(value: Any) -> ReturnT | type[Void]:
            fields = self.assert_fields(Fields(field))(value)
            try:
                return cast('ReturnT | type[Void]', fields[field.name])
            except KeyError:
                if isinstance(field, RequiredField):
                    raise
                return Void
        return _assert_field

    def assert_record(self, fields: Fields) -> Assertion[Any, MutableMapping[str, Any]]:
        if not len(list(fields)):
            raise ValueError('One or more fields are required.')

        def _assert_record(value: Any) -> MutableMapping[str, Any]:
            dict_value = self.assert_dict()(value)
            known_keys = set(map(lambda x: x.name, fields))
            unknown_keys = set(dict_value.keys()) - known_keys
            with SerdeErrorCollection().assert_valid() as errors:
                for unknown_key in unknown_keys:
                    with errors.catch(Str.plain(unknown_key)):
                        raise AssertionFailed(Str._(
                            'Unknown key: {unknown_key}. Did you mean {known_keys}?',
                            unknown_key=f'"{unknown_key}"',
                            known_keys=', '.join(map(lambda x: f'"{x}"', sorted(known_keys)))
                        ))
                return self.assert_fields(fields)(dict_value)
        return _assert_record

    def assert_path(self) -> Assertion[Any, Path]:
        def _assert_path(value: Any) -> Path:
            self.assert_str()(value)
            return Path(value).expanduser().resolve()
        return _assert_path

    def assert_directory_path(self) -> Assertion[Any, Path]:
        def _assert_directory_path(value: Any) -> Path:
            directory_path = self.assert_path()(value)
            if directory_path.is_dir():
                return directory_path
            raise AssertionFailed(Str._(
                '"{path}" is not a directory.',
                path=value,
            ))
        return _assert_directory_path

    def assert_locale(self) -> Assertion[Any, str]:
        def _assert_locale(
            value: Any,
        ) -> str:
            value = self.assert_str()(value)
            try:
                get_data(value)
                return value
            except LocaleNotFoundError:
                raise AssertionFailed(Str._(
                    '"{locale}" is not a valid IETF BCP 47 language tag.',
                    locale=value,
                ))
        return _assert_locale

    def assert_setattr(self, instance: object, attr_name: str) -> Assertion[ValueT, ValueT]:
        def _assert_setattr(value: ValueT) -> ValueT:
            setattr(instance, attr_name, value)
            return value
        return _assert_setattr

    def assert_extension_type(self) -> Assertion[Any, type[Extension]]:
        def _assert_extension_type(
            value: Any,
        ) -> type[Extension]:
            from betty.app.extension import get_extension_type, ExtensionTypeImportError, ExtensionTypeInvalidError, ExtensionTypeError

            self.assert_str()(value)
            try:
                return get_extension_type(value)
            except ExtensionTypeImportError:
                raise AssertionFailed(
                    Str._(
                        'Cannot find and import "{extension_type}".',
                        extension_type=str(value),
                    )
                )
            except ExtensionTypeInvalidError:
                raise AssertionFailed(
                    Str._(
                        '"{extension_type}" is not a valid Betty extension type.',
                        extension_type=str(value),
                    )
                )
            except ExtensionTypeError:
                raise AssertionFailed(
                    Str._(
                        'Cannot determine the extension type for "{extension_type}". Did you perhaps make a typo, or could it be that the extension type comes from another package that is not yet installed?',
                        extension_type=str(value),
                    )
                )
        return _assert_extension_type

    def assert_entity_type(self) -> Assertion[Any, type[Entity]]:
        def _assert_entity_type(
            value: Any,
        ) -> type[Entity]:
            self.assert_str()(value)
            try:
                return get_entity_type(value)
            except EntityTypeImportError:
                raise AssertionFailed(
                    Str._(
                        'Cannot find and import "{entity_type}".',
                        entity_type=str(value),
                    )
                )
            except EntityTypeInvalidError:
                raise AssertionFailed(
                    Str._(
                        '"{entity_type}" is not a valid Betty entity type.',
                        entity_type=str(value),
                    )
                )
            except EntityTypeError:
                raise AssertionFailed(
                    Str._(
                        'Cannot determine the entity type for "{entity_type}". Did you perhaps make a typo, or could it be that the entity type comes from another package that is not yet installed?',
                        entity_type=str(value),
                    )
                )
        return _assert_entity_type
