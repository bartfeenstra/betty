from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Type, Dict, Union, Callable, Any, List, \
    Generic, TYPE_CHECKING, TypeVar, MutableSequence, MutableMapping, overload, Tuple

from betty.config.dump import DumpedConfigurationType, DumpedConfigurationTypeT
from betty.config.error import ConfigurationError, ConfigurationErrorCollection
from betty.functools import _Result
from betty.locale import LocaleNotFoundError, get_data, Localizable
from betty.model import Entity, get_entity_type, EntityTypeImportError, EntityTypeInvalidError, EntityTypeError
from betty.typing import Void

try:
    from typing_extensions import TypeAlias
except ModuleNotFoundError:  # pragma: no cover
    from typing import TypeAlias  # type: ignore  # pragma: no cover

if TYPE_CHECKING:
    from betty.app.extension import Extension

T = TypeVar('T')
ValueT = TypeVar('ValueT')
ReturnT = TypeVar('ReturnT')
CallValueT = TypeVar('CallValueT')
CallReturnT = TypeVar('CallReturnT')
FValueT = TypeVar('FValueT')
MapReturnT = TypeVar('MapReturnT')
Number: TypeAlias = Union[int, float]
NumberT = TypeVar('NumberT', bound=Number)


class ConfigurationLoadError(ConfigurationError):
    pass


class ConfigurationValidationError(ConfigurationLoadError):
    pass


class ConfigurationFormatError(ConfigurationLoadError):
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
        raise NotImplementedError


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
    def __init__(self, *fields: _Field):
        self._fields = fields

    def __iter__(self) -> Iterator[_Field]:
        return (field for field in self._fields)


_AssertionBuilderFunction = Callable[[ValueT], ReturnT]
_AssertionBuilderMethod = Callable[[object, ValueT], ReturnT]
_AssertionBuilder = Union[_AssertionBuilderFunction, _AssertionBuilderMethod]


class Asserter(Localizable):
    def _assert_type_violation_error_message(
            self,
            asserted_type: Type[DumpedConfigurationType] | Tuple[Type[DumpedConfigurationType], ...],
    ) -> str:
        message_builders = {
            bool: lambda localizer: localizer._('This must be a boolean.'),
            int: lambda localizer: localizer._('This must be an integer.'),
            float: lambda localizer: localizer._('This must be a decimal number.'),
            (float, int): lambda localizer: localizer._('This must be a number.'),
            str: lambda localizer: localizer._('This must be a string.'),
            list: lambda localizer: localizer._('This must be a list.'),
            dict: lambda localizer: localizer._('This must be a key-value mapping.'),
        }
        return message_builders[asserted_type](self.localizer)

    def _assert_type(
        self,
        value: DumpedConfigurationTypeT,
        value_required_type: Type[DumpedConfigurationType] | Tuple[Type[DumpedConfigurationType], ...],
        value_disallowed_type: Type[DumpedConfigurationType] | None = None,
    ) -> DumpedConfigurationTypeT:
        if isinstance(
            value,
            tuple(value_required_type)  # type: ignore[arg-type]
                if isinstance(value_required_type, set)
                else value_required_type,
        ) and (value_disallowed_type is None or not isinstance(
            value,
            value_disallowed_type,
        )):
            return value
        raise ConfigurationValidationError(self._assert_type_violation_error_message(value_required_type))

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
        def _assert_number(value: Any) -> int | float:
            return self._assert_type(value, (float, int), bool)
        return _assert_number

    def assert_positive_number(self) -> Assertion[Any, NumberT]:
        def _assert_positive_number(  # type: ignore
            value: NumberT | Any,
        ) -> NumberT:
            self.assert_number()(value)
            if value <= 0:
                raise ConfigurationValidationError(self.localizer._('This must be a positive number.'))
            return value
        return _assert_positive_number

    def assert_str(self) -> Assertion[Any, str]:
        def _assert_str(value: Any) -> str:
            return self._assert_type(value, str)
        return _assert_str

    def assert_list(self) -> Assertion[Any, List]:
        def _assert_list(value: Any) -> List:
            return self._assert_type(value, list)
        return _assert_list

    def assert_dict(self) -> Assertion[Any, Dict]:
        def _assert_dict(value: Any) -> Dict:
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
            with ConfigurationErrorCollection().assert_valid() as errors:
                for value_item_index, value_item_value in enumerate(list_value):
                    with errors.catch(str(value_item_index)):
                        sequence.append(self.assert_assertions(item_assertion)(value_item_value))
            return sequence
        return _assert_sequence

    def assert_mapping(self, item_assertion: Assertions[ValueT, ReturnT]) -> Assertion[Any, MutableMapping[str, ReturnT]]:
        def _assert_mapping(value: ValueT) -> MutableMapping[str, ReturnT]:
            dict_value = self.assert_dict()(value)
            mapping = {}
            with ConfigurationErrorCollection().assert_valid() as errors:
                for value_item_key, value_item_value in dict_value.items():
                    with errors.catch(value_item_key):
                        mapping[value_item_key] = self.assert_assertions(item_assertion)(value_item_value)
            return mapping
        return _assert_mapping

    def assert_fields(self, fields: Fields) -> Assertion[Any, MutableMapping[str, Any]]:
        def _assert_fields(value: Any) -> MutableMapping[str, Any]:
            value_dict = self.assert_dict()(value)
            mapping = {}
            with ConfigurationErrorCollection().assert_valid() as errors:
                for field in fields:
                    with errors.catch(field.name):
                        if field.name in value_dict:
                            if field.assertion:
                                mapping[field.name] = self.assert_assertions(field.assertion)(value_dict[field.name])
                        elif isinstance(field, RequiredField):
                            raise ConfigurationValidationError(self.localizer._('This field is required.'))
            return mapping
        return _assert_fields

    @overload
    def assert_field(self, field: RequiredField[ValueT, ReturnT]) -> Assertion[ValueT, ReturnT]:
        pass

    @overload
    def assert_field(self, field: OptionalField[ValueT, ReturnT]) -> Assertion[ValueT, ReturnT | Type[Void]]:
        pass

    def assert_field(self, field: _Field[ValueT, ReturnT]) -> Assertion[ValueT, ReturnT | Type[Void]]:
        def _assert_field(value: Any) -> ReturnT | Type[Void]:
            fields = self.assert_fields(Fields(field))(value)
            try:
                return fields[field.name]
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
            with ConfigurationErrorCollection().assert_valid() as errors:
                for unknown_key in unknown_keys:
                    with errors.catch(unknown_key):
                        raise ConfigurationValidationError(self.localizer._('Unknown key: {unknown_key}. Did you mean {known_keys}?').format(
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
            if directory_path := self.assert_path()(value):
                if directory_path.is_dir():
                    return directory_path
            raise ConfigurationValidationError(self.localizer._('"{path}" is not a directory.').format(
                path=value,
            ))
        return _assert_directory_path

    def assert_locale(self) -> Assertion[Any, str]:
        def _assert_locale(  # type: ignore
            value: Any,
        ) -> str:
            self.assert_str()(value)
            try:
                get_data(value)
                return value
            except LocaleNotFoundError:
                raise ConfigurationValidationError(self.localizer._('"{locale}" is not a valid IETF BCP 47 language tag.').format(
                    locale=value,
                ))
        return _assert_locale

    def assert_setattr(self, instance: object, attr_name: str) -> Assertion[ValueT, ValueT]:
        def _assert_setattr(value: ValueT) -> ValueT:
            setattr(instance, attr_name, value)
            return value
        return _assert_setattr

    def assert_extension_type(self) -> Assertion[Any, Type[Extension]]:
        def _assert_extension_type(
            value: Any,
        ) -> Type[Extension]:
            from betty.app.extension import get_extension_type, ExtensionTypeImportError, ExtensionTypeInvalidError, ExtensionTypeError

            self.assert_str()(value)
            try:
                return get_extension_type(value)
            except ExtensionTypeImportError:
                raise ConfigurationValidationError(
                    self.localizer._('Cannot find and import "{extension_type}".').format(
                        extension_type=str(value),
                    )
                )
            except ExtensionTypeInvalidError:
                raise ConfigurationValidationError(
                    self.localizer._('"{extension_type}" is not a valid Betty extension type.').format(
                        extension_type=str(value),
                    )
                )
            except ExtensionTypeError:
                raise ConfigurationValidationError(
                    self.localizer._('Cannot determine the extension type for "{extension_type}". Did you perhaps make a typo, or could it be that the extension type comes from another package that is not yet installed?').format(
                        extension_type=str(value),
                    )
                )
        return _assert_extension_type

    def assert_entity_type(self) -> Assertion[Any, Type[Entity]]:
        def _assert_entity_type(
            value: Any,
        ) -> Type[Entity]:
            self.assert_str()(value)
            try:
                return get_entity_type(value)
            except EntityTypeImportError:
                raise ConfigurationValidationError(
                    self.localizer._('Cannot find and import "{entity_type}".').format(
                        entity_type=str(value),
                    )
                )
            except EntityTypeInvalidError:
                raise ConfigurationValidationError(
                    self.localizer._('"{entity_type}" is not a valid Betty entity type.').format(
                        entity_type=str(value),
                    )
                )
            except EntityTypeError:
                raise ConfigurationValidationError(
                    self.localizer._('Cannot determine the entity type for "{entity_type}". Did you perhaps make a typo, or could it be that the entity type comes from another package that is not yet installed?').format(
                        entity_type=str(value),
                    )
                )
        return _assert_entity_type
