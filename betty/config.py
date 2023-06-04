from __future__ import annotations

import os
from collections import OrderedDict
from contextlib import suppress
from pathlib import Path
from typing import Generic, Optional, Iterable, Iterator, Union, SupportsIndex, Hashable, \
    MutableSequence, MutableMapping, Type, Tuple, TypeVar, Any, Sequence, overload

from ordered_set import OrderedSet
from reactives import scope
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property

from betty.classtools import Repr, repr_instance
from betty.serde.error import SerdeErrorCollection
from betty.functools import slice_to_range
from betty.locale import Localizer, Localizable
from betty.os import ChDir
from betty.serde.dump import Dumpable, Dump, minimize, VoidableDump, Void
from betty.serde.format import FormatRepository
from betty.serde.load import Asserter, Assertion, LoadError, Assertions
from betty.tempfile import TemporaryDirectory

try:
    from typing_extensions import Self, TypeAlias
except ModuleNotFoundError:
    from typing import Self, TypeAlias  # type: ignore


class Configuration(ReactiveInstance, Repr, Localizable, Dumpable):
    def __init__(self, *args, localizer: Localizer | None = None, **kwargs):
        super().__init__(*args, **kwargs, localizer=localizer)
        self._asserter = Asserter(localizer=self._localizer)

    def update(self, other: Self) -> None:
        raise NotImplementedError

    @classmethod
    def load(
            cls,
            dump: Dump,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        """
        Load dumped configuration into a new configuration instance.
        """

        raise NotImplementedError

    @classmethod
    def assert_load(cls: Type[ConfigurationT], configuration: ConfigurationT | None = None) -> Assertion[Dump, ConfigurationT]:
        def _assert_load(dump: Dump) -> ConfigurationT:
            return cls.load(dump, configuration)
        _assert_load.__qualname__ = f'{_assert_load.__qualname__} for {cls.__module__}.{cls.__qualname__}.load'
        return _assert_load


ConfigurationT = TypeVar('ConfigurationT', bound=Configuration)


class FileBasedConfiguration(Configuration):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._project_directory: Optional[TemporaryDirectory] = None
        self._configuration_file_path: Path | None = None
        self._autowrite = False

    def _assert_configuration_file_path(self) -> None:
        if self.configuration_file_path is None:
            raise LoadError(self.localizer._('The configuration must have a configuration file path.'))

    @property
    def autowrite(self) -> bool:
        return self._autowrite

    @autowrite.setter
    def autowrite(self, autowrite: bool) -> None:
        if autowrite:
            self._assert_configuration_file_path()
            if not self._autowrite:
                self.react.react_weakref(self.write)
        else:
            self.react.shutdown(self.write)
        self._autowrite = autowrite

    def write(self, configuration_file_path: Optional[Path] = None) -> None:
        if configuration_file_path is None:
            self._assert_configuration_file_path()
        else:
            self.configuration_file_path = configuration_file_path  # type: ignore[assignment]

        self._write(self.configuration_file_path)

    def _write(self, configuration_file_path: Path) -> None:
        # Change the working directory to allow absolute paths to be turned relative to the configuration file's directory
        # path.
        formats = FormatRepository(localizer=self._localizer)
        with ChDir(configuration_file_path.parent):
            dump = formats.format_for(configuration_file_path.suffix[1:]).dump(self.dump())
            try:
                with open(configuration_file_path, mode='w') as f:
                    f.write(dump)
            except FileNotFoundError:
                os.makedirs(configuration_file_path.parent)
                self.write()
        self._configuration_file_path = configuration_file_path

    def read(self, configuration_file_path: Optional[Path] = None) -> None:
        if configuration_file_path is None:
            self._assert_configuration_file_path()
        else:
            self.configuration_file_path = configuration_file_path  # type: ignore[assignment]

        formats = FormatRepository(localizer=self._localizer)
        with SerdeErrorCollection().assert_valid() as errors:
            # Change the working directory to allow relative paths to be resolved against the configuration file's directory
            # path.
            with ChDir(self.configuration_file_path.parent):
                with open(self.configuration_file_path) as f:
                    read_configuration = f.read()
                with errors.catch(f'in {self.configuration_file_path.resolve()}'):
                    loaded_configuration = self.load(
                        formats.format_for(self.configuration_file_path.suffix[1:]).load(read_configuration)
                    )
        self.update(loaded_configuration)

    def __del__(self):
        if hasattr(self, '_project_directory') and self._project_directory is not None:
            self._project_directory.cleanup()

    @property
    @reactive_property
    def configuration_file_path(self) -> Path:
        if self._configuration_file_path is None:
            if self._project_directory is None:
                self._project_directory = TemporaryDirectory()
            self._write(Path(self._project_directory.name) / f'{type(self).__name__}.json')
        return self._configuration_file_path  # type: ignore

    @configuration_file_path.setter
    def configuration_file_path(self, configuration_file_path: Path) -> None:
        if configuration_file_path == self._configuration_file_path:
            return
        formats = FormatRepository(localizer=self._localizer)
        formats.format_for(configuration_file_path.suffix[1:])
        self._configuration_file_path = configuration_file_path

    @configuration_file_path.deleter
    def configuration_file_path(self) -> None:
        if self._autowrite:
            raise RuntimeError('Cannot remove the configuration file path while autowrite is enabled.')
        self._configuration_file_path = None


ConfigurationKey: TypeAlias = Union[SupportsIndex, Hashable, Type]
ConfigurationKeyT = TypeVar('ConfigurationKeyT', bound=ConfigurationKey)


class ConfigurationCollection(Configuration, Generic[ConfigurationKeyT, ConfigurationT]):
    _configurations: MutableSequence[ConfigurationT] | MutableMapping[ConfigurationKeyT, ConfigurationT]

    def __init__(
            self,
            configurations: Iterable[ConfigurationT] | None = None,
            *,
            localizer: Localizer | None = None,
    ):
        super().__init__(localizer=localizer)
        if configurations is not None:
            self.append(*configurations)

    @scope.register_self
    def __iter__(self) -> Iterator[ConfigurationKeyT] | Iterator[ConfigurationT]:
        raise NotImplementedError

    @scope.register_self
    def __contains__(self, item: Any) -> bool:
        return item in self._configurations

    def __getitem__(self, configuration_key: ConfigurationKeyT) -> ConfigurationT:
        raise NotImplementedError

    def __delitem__(self, configuration_key: ConfigurationKeyT) -> None:
        self.remove(configuration_key)

    @scope.register_self
    def __len__(self) -> int:
        return len(self._configurations)

    @scope.register_self
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        scope.register(other)
        if list(self.keys()) != list(other.keys()):
            return False
        if list(self.values()) != list(other.values()):
            return False
        return True

    def __repr__(self) -> str:
        return repr_instance(self, configurations=list(self.values()))

    def _remove_without_trigger(self, *configuration_keys: ConfigurationKeyT) -> None:
        for configuration_key in configuration_keys:
            with suppress(LookupError):
                self._on_remove(self._configurations[configuration_key])  # type: ignore[call-overload]
            del self._configurations[configuration_key]  # type: ignore[call-overload]

    def remove(self, *configuration_keys: ConfigurationKeyT) -> None:
        self._remove_without_trigger(*configuration_keys)
        self.react.trigger()

    def _clear_without_trigger(self) -> None:
        self._remove_without_trigger(*self.keys())

    def clear(self) -> None:
        self._clear_without_trigger()
        self.react.trigger()

    def _on_add(self, configuration: ConfigurationT) -> None:
        configuration.react(self)

    def _on_remove(self, configuration: ConfigurationT) -> None:
        configuration.react.shutdown(self)

    def to_index(self, configuration_key: ConfigurationKeyT) -> int:
        raise NotImplementedError

    def to_indices(self, *configuration_keys: ConfigurationKeyT) -> Iterator[int]:
        for configuration_key in configuration_keys:
            yield self.to_index(configuration_key)

    def to_key(self, index: int) -> ConfigurationKeyT:
        raise NotImplementedError

    def to_keys(self, *indices: int | slice) -> Iterator[ConfigurationKeyT]:
        unique_indices = set()
        for index in indices:
            if isinstance(index, slice):
                for slice_index in slice_to_range(index, self._configurations):
                    unique_indices.add(slice_index)
            else:
                unique_indices.add(index)
        for index in sorted(unique_indices):
            yield self.to_key(index)

    @classmethod
    def _item_type(cls) -> Type[ConfigurationT]:
        raise NotImplementedError

    @classmethod
    def _create_default_item(cls, configuration_key: ConfigurationKeyT) -> ConfigurationT:
        raise NotImplementedError

    def keys(self) -> Iterator[ConfigurationKeyT]:
        raise NotImplementedError

    def values(self) -> Iterator[ConfigurationT]:
        raise NotImplementedError

    def prepend(self, *configurations: ConfigurationT) -> None:
        raise NotImplementedError

    def append(self, *configurations: ConfigurationT) -> None:
        raise NotImplementedError

    def insert(self, index: int, *configurations: ConfigurationT) -> None:
        raise NotImplementedError

    def move_to_beginning(self, *configuration_keys: ConfigurationKeyT) -> None:
        raise NotImplementedError

    def move_towards_beginning(self, *configuration_keys: ConfigurationKeyT) -> None:
        raise NotImplementedError

    def move_to_end(self, *configuration_keys: ConfigurationKeyT) -> None:
        raise NotImplementedError

    def move_towards_end(self, *configuration_keys: ConfigurationKeyT) -> None:
        raise NotImplementedError


class ConfigurationSequence(ConfigurationCollection[int, ConfigurationT], Generic[ConfigurationT]):
    def __init__(
        self,
        configurations: Iterable[ConfigurationT] | None = None,
        *,
        localizer: Localizer | None = None,
    ):
        self._configurations: MutableSequence[ConfigurationT] = []
        super().__init__(configurations, localizer=localizer)

    def to_index(self, configuration_key: int) -> int:
        return configuration_key

    def to_key(self, index: int) -> int:
        return index

    @overload
    def __getitem__(self, configuration_key: int) -> ConfigurationT:
        pass

    @overload
    def __getitem__(self, configuration_key: slice) -> Sequence[ConfigurationT]:
        pass

    def __getitem__(self, configuration_key: int | slice) -> ConfigurationT | Sequence[ConfigurationT]:
        return self._configurations[configuration_key]

    @scope.register_self
    def __iter__(self) -> Iterator[ConfigurationT]:
        return (configuration for configuration in self._configurations)

    @scope.register_self
    def keys(self) -> Iterator[int]:
        return iter(range(0, len(self._configurations)))

    @scope.register_self
    def values(self) -> Iterator[ConfigurationT]:
        yield from self._configurations

    def update(self, other: Self) -> None:
        raise NotImplementedError

    @classmethod
    def load(
            cls,
            dump: Dump,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        else:
            configuration._clear_without_trigger()
        asserter = Asserter(localizer=localizer)
        with SerdeErrorCollection().assert_valid():
            configuration.append(*asserter.assert_sequence(Assertions(cls._item_type().assert_load()))(dump))
        return configuration

    def dump(self) -> VoidableDump:
        return minimize([
            configuration.dump()
            for configuration in self._configurations
        ])

    def prepend(self, *configurations: ConfigurationT) -> None:
        for configuration in configurations:
            self._on_add(configuration)
            self._configurations.insert(0, configuration)
        self.react.trigger()

    def append(self, *configurations: ConfigurationT) -> None:
        for configuration in configurations:
            self._on_add(configuration)
            self._configurations.append(configuration)
        self.react.trigger()

    def insert(self, index: int, *configurations: ConfigurationT) -> None:
        for configuration in reversed(configurations):
            self._on_add(configuration)
            self._configurations.insert(index, configuration)
        self.react.trigger()

    def move_to_beginning(self, *configuration_keys: int) -> None:
        self.move_to_end(
            *configuration_keys,
            *[
                index
                for index
                in range(0, len(self._configurations))
                if index not in configuration_keys
            ]
        )

    def move_towards_beginning(self, *configuration_keys: int) -> None:
        for index in configuration_keys:
            self._configurations.insert(index - 1, self._configurations.pop(index))
        self.react.trigger()

    def move_to_end(self, *configuration_keys: int) -> None:
        for index in configuration_keys:
            self._configurations.append(self._configurations[index])
        for index in reversed(configuration_keys):
            self._configurations.pop(index)
        self.react.trigger()

    def move_towards_end(self, *configuration_keys: int) -> None:
        for index in reversed(configuration_keys):
            self._configurations.insert(index + 1, self._configurations.pop(index))
        self.react.trigger()


class ConfigurationMapping(ConfigurationCollection[ConfigurationKeyT, ConfigurationT], Generic[ConfigurationKeyT, ConfigurationT]):
    def __init__(
        self,
        configurations: Iterable[ConfigurationT] | None = None,
        *,
        localizer: Localizer | None = None,
    ):
        self._configurations: OrderedDict[ConfigurationKeyT, ConfigurationT] = OrderedDict()
        super().__init__(configurations, localizer=localizer)

    def _minimize_item_dump(self) -> bool:
        return False

    def to_index(self, configuration_key: ConfigurationKeyT) -> int:
        return list(self._configurations.keys()).index(configuration_key)

    def to_key(self, index: int) -> ConfigurationKeyT:
        return list(self._configurations.keys())[index]

    @scope.register_self
    def __getitem__(self, configuration_key: ConfigurationKeyT) -> ConfigurationT:
        try:
            return self._configurations[configuration_key]
        except KeyError:
            self.append(self._create_default_item(configuration_key))
            return self._configurations[configuration_key]

    @scope.register_self
    def __iter__(self) -> Iterator[ConfigurationKeyT]:
        return (configuration_key for configuration_key in self._configurations)

    def _keys_without_scope(self) -> Iterator[ConfigurationKeyT]:
        return (configuration_key for configuration_key in self._configurations.keys())

    @scope.register_self
    def keys(self) -> Iterator[ConfigurationKeyT]:
        return self._keys_without_scope()

    @scope.register_self
    def values(self) -> Iterator[ConfigurationT]:
        yield from self._configurations.values()

    def update(self, other: Self) -> None:
        self.replace(*other.values())

    def replace(self, *values: ConfigurationT) -> None:
        self_keys = OrderedSet(self.keys())
        other = {
            self._get_key(value): value
            for value in values
        }
        other_values = list(values)
        other_keys = OrderedSet(map(self._get_key, other_values))

        # Update items that are kept.
        for key in self_keys & other_keys:
            self[key].update(other[key])

        # Add items that are new.
        self._append_without_trigger(*(other[key] for key in (other_keys - self_keys)))

        # Remove items that should no longer be present.
        self._remove_without_trigger(*(self_keys - other_keys))

        # Ensure everything is in the correct order. This will also trigger reactors.
        self.move_to_beginning(*other_keys)

    @classmethod
    def load(
            cls,
            dump: Dump,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter(localizer=localizer)
        dict_dump = asserter.assert_dict()(dump)
        mapping = asserter.assert_mapping(Assertions(cls._item_type().load))({
            key: cls._load_key(value, key, localizer=localizer)
            for key, value
            in dict_dump.items()
        })
        configuration.replace(*mapping.values())
        return configuration

    def dump(self) -> VoidableDump:
        dump = {}
        for configuration_item in self._configurations.values():
            item_dump = configuration_item.dump()
            if item_dump is not Void:
                item_dump, configuration_key = self._dump_key(item_dump)
                if self._minimize_item_dump():
                    item_dump = minimize(item_dump)
                if item_dump is not Void:
                    dump[configuration_key] = item_dump
        return minimize(dump)

    def prepend(self, *configurations: ConfigurationT) -> None:
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            self._configurations[configuration_key] = configuration
            configuration.react(self)
        self.move_to_beginning(*map(self._get_key, configurations))

    def _append_without_trigger(self, *configurations: ConfigurationT) -> None:
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            self._configurations[configuration_key] = configuration
            configuration.react(self)
        self._move_to_end_without_trigger(*map(self._get_key, configurations))

    def append(self, *configurations: ConfigurationT) -> None:
        self._append_without_trigger(*configurations)
        self.react.trigger()

    def _insert_without_trigger(self, index: int, *configurations: ConfigurationT) -> None:
        current_configuration_keys = list(self._keys_without_scope())
        self._append_without_trigger(*configurations)
        self._move_to_end_without_trigger(
            *current_configuration_keys[0:index],
            *map(self._get_key, configurations),
            *current_configuration_keys[index:]
        )

    def insert(self, index: int, *configurations: ConfigurationT) -> None:
        self._insert_without_trigger(index, *configurations)
        self.react.trigger()

    def move_to_beginning(self, *configuration_keys: ConfigurationKeyT) -> None:
        for configuration_key in reversed(configuration_keys):
            self._configurations.move_to_end(configuration_key, False)
        self.react.trigger()

    def move_towards_beginning(self, *configuration_keys: ConfigurationKeyT) -> None:
        self._move_by_offset(-1, *configuration_keys)

    def _move_to_end_without_trigger(self, *configuration_keys: ConfigurationKeyT) -> None:
        for configuration_key in configuration_keys:
            self._configurations.move_to_end(configuration_key)

    def move_to_end(self, *configuration_keys: ConfigurationKeyT) -> None:
        self._move_to_end_without_trigger(*configuration_keys)
        self.react.trigger()

    def move_towards_end(self, *configuration_keys: ConfigurationKeyT) -> None:
        self._move_by_offset(1, *configuration_keys)

    def _move_by_offset(self, offset: int, *configuration_keys: ConfigurationKeyT) -> None:
        current_configuration_keys = list(self._keys_without_scope())
        indices = list(self.to_indices(*configuration_keys))
        if offset > 0:
            indices.reverse()
        for index in indices:
            self._insert_without_trigger(index + offset, self._configurations.pop(current_configuration_keys[index]))
        self.react.trigger()

    def _get_key(self, configuration: ConfigurationT) -> ConfigurationKeyT:
        raise NotImplementedError

    @classmethod
    def _load_key(
        cls,
        item_dump: Dump,
        key_dump: str,
        *,
        localizer: Localizer | None = None,
    ) -> Dump:
        raise NotImplementedError

    def _dump_key(self, item_dump: VoidableDump) -> Tuple[VoidableDump, str]:
        raise NotImplementedError


class Configurable(Generic[ConfigurationT]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configuration: ConfigurationT

    @property
    def configuration(self) -> ConfigurationT:
        if self._configuration is None:
            raise RuntimeError(f'{self} has no configuration. {type(self)}.__init__() must ensure it is set.')
        return self._configuration
