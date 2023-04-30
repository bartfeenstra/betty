from __future__ import annotations

import inspect
from contextlib import contextmanager
from os import path
from pathlib import Path
from typing import Iterator, Type, Dict, Union, Callable, Optional, Tuple, Any, ContextManager, List, \
    Generic

from betty.config.dump import DumpedConfiguration, DumpedConfigurationT, DumpedConfigurationU, \
    DumpedConfigurationTypeT, DumpedConfigurationType, DumpedConfigurationDict, DumpedConfigurationList
from betty.config.error import ConfigurationError, ConfigurationErrorCollection
from betty.locale import DEFAULT_LOCALIZER, LocaleNotFoundError, get_data

try:
    from typing_extensions import TypeAlias, TypeGuard
except ModuleNotFoundError:  # pragma: no cover
    from typing import TypeAlias, TypeGuard  # type: ignore  # pragma: no cover


class ConfigurationLoadError(ConfigurationError):
    pass


class ConfigurationValidationError(ConfigurationLoadError):
    pass


class ConfigurationFormatError(ConfigurationLoadError):
    pass


_TYPE_VIOLATION_ERROR_MESSAGE_BUILDERS: Dict[Type, Callable[[], str]] = {
    bool: lambda: DEFAULT_LOCALIZER._('This must be a boolean.'),
    int: lambda: DEFAULT_LOCALIZER._('This must be an integer.'),
    float: lambda: DEFAULT_LOCALIZER._('This must be a decimal number.'),
    str: lambda: DEFAULT_LOCALIZER._('This must be a string.'),
    list: lambda: DEFAULT_LOCALIZER._('This must be a list.'),
    dict: lambda: DEFAULT_LOCALIZER._('This must be a key-value mapping.'),
}


ConfigurationValueAssertFunction: TypeAlias = Callable[
    [
        DumpedConfiguration,
        'Loader',
    ],
    TypeGuard[DumpedConfigurationT],
]


ConfigurationValueAssertLoaderMethod: TypeAlias = Callable[
    [
        DumpedConfiguration,
    ],
    TypeGuard[DumpedConfigurationT],
]


ConfigurationValueAssert: TypeAlias = Union[
    ConfigurationValueAssertFunction[DumpedConfigurationT],
    ConfigurationValueAssertLoaderMethod[DumpedConfigurationT],
]


ConfigurationKeyAndValueAssert: TypeAlias = Callable[
    [
        DumpedConfiguration,
        'Loader',
        str,
    ],
    TypeGuard[DumpedConfigurationT],
]


ConfigurationAssert: TypeAlias = Union[
    ConfigurationValueAssert[DumpedConfigurationT],
    ConfigurationKeyAndValueAssert[DumpedConfigurationT],
]


Committer = Callable[[], None]


FieldCommitter = Callable[[DumpedConfigurationT], None]


class Field(Generic[DumpedConfigurationT]):
    def __init__(
            self,
            required: bool,
            configuration_assert: ConfigurationAssert[DumpedConfigurationT],
            committer: Optional[FieldCommitter[DumpedConfigurationT]] = None,
    ):
        self._required = required
        self._configuration_assert = configuration_assert
        self._committer = committer

    @property
    def required(self) -> bool:
        return self._required

    @property
    def configuration_assert(self) -> ConfigurationAssert[DumpedConfigurationT]:
        return self._configuration_assert

    def commit(self, dumped_configuration: DumpedConfigurationT) -> None:
        if self._committer:
            self._committer(dumped_configuration)


class Loader:
    def __init__(self):
        self._errors: ConfigurationErrorCollection[ConfigurationLoadError] = ConfigurationErrorCollection()
        self._committers = []
        self._committed = False

    @property
    def errors(self) -> ConfigurationErrorCollection:
        return self._errors

    def _assert_uncommitted(self) -> None:
        if self._committed:
            raise RuntimeError('This load was committed already.')

    def on_commit(self, committer: Committer) -> None:
        self._assert_uncommitted()
        self._committers.append(committer)

    def error(self, *errors: ConfigurationLoadError) -> None:
        self._errors.append(*errors)

    @contextmanager
    def catch(self) -> Iterator[None]:
        try:
            yield
        except ConfigurationLoadError as e:
            self.error(e)

    @contextmanager
    def context(self, context: Optional[str] = None) -> Iterator[ConfigurationErrorCollection]:
        context_errors: ConfigurationErrorCollection = ConfigurationErrorCollection()
        if context:
            context_errors = context_errors.with_context(context)
        previous_errors = self._errors
        self._errors = context_errors
        yield context_errors
        self._errors = previous_errors
        self.error(*context_errors)

    def commit(self) -> None:
        if not self._errors.valid:
            raise self._errors
        if not self._committed:
            self._committed = True
            for committer in self._committers:
                committer()

    def _assert(self, dumped_configuration: DumpedConfiguration, configuration_assert: ConfigurationAssert[DumpedConfigurationT], configuration_key: Optional[str] = None) -> TypeGuard[DumpedConfigurationT]:
        args: List[Any] = [dumped_configuration]
        if configuration_assert not in map(lambda x: x[1], inspect.getmembers(self)):
            args.append(self)
        if configuration_key and len(inspect.signature(configuration_assert).parameters) > len(args):
            args.append(configuration_key)
        return configuration_assert(*args)

    def _assert_type(self, dumped_configuration: DumpedConfigurationU, configuration_value_required_type: Type[DumpedConfigurationTypeT], configuration_value_disallowed_type: Optional[Type[DumpedConfigurationType]] = None) -> TypeGuard[DumpedConfigurationTypeT]:
        if isinstance(dumped_configuration, configuration_value_required_type) and (not configuration_value_disallowed_type or not isinstance(dumped_configuration, configuration_value_disallowed_type)):
            return True
        self.error(ConfigurationValidationError(_TYPE_VIOLATION_ERROR_MESSAGE_BUILDERS[configuration_value_required_type]()))
        return False

    def assert_bool(self, dumped_configuration: DumpedConfiguration) -> TypeGuard[bool]:
        return self._assert_type(dumped_configuration, bool)

    def assert_int(self, dumped_configuration: DumpedConfiguration) -> TypeGuard[int]:
        return self._assert_type(dumped_configuration, int, bool)

    def assert_float(self, dumped_configuration: DumpedConfiguration) -> TypeGuard[float]:
        return self._assert_type(dumped_configuration, float)

    def assert_str(self, dumped_configuration: DumpedConfiguration) -> TypeGuard[str]:
        return self._assert_type(dumped_configuration, str)

    def assert_list(self, dumped_configuration: DumpedConfiguration) -> TypeGuard[DumpedConfigurationList]:
        return self._assert_type(dumped_configuration, list)

    def assert_sequence(self, dumped_configuration: DumpedConfiguration, configuration_value_assert: ConfigurationValueAssert[DumpedConfigurationT]) -> TypeGuard[DumpedConfigurationList[DumpedConfigurationT]]:
        with self.context() as errors:
            if self.assert_list(dumped_configuration):
                for i, dumped_configuration_item in enumerate(dumped_configuration):
                    with self.context(str(i)):
                        self._assert(dumped_configuration_item, configuration_value_assert)
        return errors.valid

    def assert_dict(self, dumped_configuration: DumpedConfiguration) -> TypeGuard[DumpedConfigurationDict[int]]:
        return self._assert_type(dumped_configuration, dict)

    @contextmanager
    def _assert_key(
        self,
        dumped_configuration: DumpedConfiguration,
        configuration_key: str,
        configuration_assert: ConfigurationAssert[DumpedConfigurationT],
        required: bool,
    ) -> Iterator[Tuple[DumpedConfiguration, bool]]:
        if self.assert_dict(dumped_configuration):
            with self.context(configuration_key):
                if configuration_key in dumped_configuration:
                    dumped_configuration_item = dumped_configuration[configuration_key]
                    if self._assert(dumped_configuration_item, configuration_assert, configuration_key):
                        yield dumped_configuration_item, True
                        return
                elif required:
                    self.error(ConfigurationValidationError(DEFAULT_LOCALIZER._('The key "{configuration_key}" is required.').format(
                        configuration_key=configuration_key
                    )))
        yield None, False

    def assert_required_key(
        self,
        dumped_configuration: DumpedConfiguration,
        configuration_key: str,
        configuration_assert: ConfigurationAssert[DumpedConfigurationT],
    ) -> ContextManager[Tuple[DumpedConfiguration, bool]]:
        return self._assert_key(  # type: ignore
            dumped_configuration,
            configuration_key,
            configuration_assert,
            True,
        )

    def assert_optional_key(
        self,
        dumped_configuration: DumpedConfiguration,
        configuration_key: str,
        configuration_assert: ConfigurationAssert[DumpedConfigurationT],
    ) -> ContextManager[Tuple[Optional[DumpedConfigurationT], bool]]:
        return self._assert_key(  # type: ignore
            dumped_configuration,
            configuration_key,
            configuration_assert,
            False,
        )

    def assert_mapping(self, dumped_configuration: DumpedConfiguration, configuration_assert: ConfigurationAssert[DumpedConfigurationT]) -> TypeGuard[Dict[str, DumpedConfigurationT]]:
        with self.context() as errors:
            if self.assert_dict(dumped_configuration):
                for configuration_key, dumped_configuration_item in dumped_configuration.items():
                    with self.context(configuration_key):
                        self._assert(dumped_configuration_item, configuration_assert, configuration_key)
        return errors.valid

    def assert_record(
            self,
            dumped_configuration: DumpedConfiguration,
            fields: Dict[str, Field],
    ) -> TypeGuard[Dict[str, DumpedConfiguration]]:
        if not fields:
            raise ValueError('One or more fields are required.')
        with self.context() as errors:
            if self.assert_dict(dumped_configuration):
                known_configuration_keys = set(fields.keys())
                unknown_configuration_keys = set(dumped_configuration.keys()) - known_configuration_keys
                for unknown_configuration_key in unknown_configuration_keys:
                    with self.context(unknown_configuration_key):
                        self.error(ConfigurationValidationError(DEFAULT_LOCALIZER._('Unknown key: {unknown_configuration_key}. Did you mean {known_configuration_keys}?').format(
                            unknown_configuration_key=f'"{unknown_configuration_key}"',
                            known_configuration_keys=', '.join(map(lambda x: f'"{x}"', sorted(known_configuration_keys)))
                        )))
                for field_name, field in fields.items():
                    configuration_item_assert = self.assert_required_key if field.required else self.assert_optional_key
                    with configuration_item_assert(dumped_configuration, field_name, field._configuration_assert) as (dumped_configuration_item, valid):
                        if valid:
                            field.commit(dumped_configuration_item)
        return errors.valid

    def assert_path(self, dumped_path: DumpedConfiguration) -> TypeGuard[str]:
        if self.assert_str(dumped_path):
            Path(dumped_path).expanduser().resolve()
            return True
        return False

    def assert_locale(self, dumped_locale: DumpedConfiguration) -> TypeGuard[str]:
        if self.assert_str(dumped_locale):
            try:
                get_data(dumped_locale)
                return True
            except LocaleNotFoundError as e:
                self.error(ConfigurationValidationError(DEFAULT_LOCALIZER._('"{locale}" is not a valid IETF BCP 47 language tag.').format(locale=e.locale)))
        return False

    def assert_directory_path(self, dumped_path: DumpedConfiguration) -> TypeGuard[str]:
        if self.assert_str(dumped_path):
            self.assert_path(dumped_path)
            if path.isdir(dumped_path):
                return True
            self.error(ConfigurationValidationError(DEFAULT_LOCALIZER._('"{path}" is not a directory.').format(path=dumped_path)))
        return False

    def assert_setattr(self, instance: Any, attr_name: str, value: Any) -> None:
        # Ensure that the attribute exists.
        getattr(instance, attr_name)

        def _setattr() -> None:
            with self.catch():
                setattr(instance, attr_name, value)
        self.on_commit(_setattr)
