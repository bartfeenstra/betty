"""
Provide the Configuration API.
"""

from __future__ import annotations

import inspect
import weakref
from collections import OrderedDict
from collections.abc import Callable
from contextlib import suppress, chdir
from pathlib import Path
from reprlib import recursive_repr
from tempfile import TemporaryDirectory
from typing import (
    Generic,
    Iterable,
    Iterator,
    SupportsIndex,
    Hashable,
    MutableSequence,
    MutableMapping,
    TypeVar,
    Any,
    Sequence,
    overload,
    cast,
    Self,
    TypeAlias,
    TYPE_CHECKING,
)

import aiofiles
from aiofiles.os import makedirs
from typing_extensions import override

from betty.asyncio import wait_to_thread
from betty.classtools import repr_instance
from betty.functools import slice_to_range
from betty.locale import Str
from betty.serde.dump import Dumpable, Dump, minimize, VoidableDump, Void
from betty.serde.error import SerdeErrorCollection
from betty.serde.format import FormatRepository
from betty.serde.load import Assertion, assert_dict, assert_mapping, assert_sequence

if TYPE_CHECKING:
    from _weakref import ReferenceType


_ConfigurationListener: TypeAlias = Callable[[], None]
ConfigurationListener: TypeAlias = "Configuration | _ConfigurationListener"


class Configuration(Dumpable):
    """
    Any configuration object.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._on_change_listeners: MutableSequence[
            ReferenceType[_ConfigurationListener]
        ] = []

    def _dispatch_change(self) -> None:
        for listener_reference in self._on_change_listeners:
            listener = listener_reference()
            if listener is None:
                continue
            listener()

    def _prepare_listener(
        self, listener: ConfigurationListener
    ) -> ReferenceType[_ConfigurationListener]:
        if isinstance(listener, Configuration):
            listener = listener._dispatch_change
        if inspect.ismethod(listener):  # type: ignore[redundant-expr]
            return weakref.WeakMethod(listener)  # type: ignore[unreachable]
        return weakref.ref(listener)

    def on_change(self, listener: ConfigurationListener) -> None:
        """
        Add an on-change listener.
        """
        self._on_change_listeners.append(self._prepare_listener(listener))

    def remove_on_change(self, listener: ConfigurationListener) -> None:
        """
        Remove an on-change listener.
        """
        self._on_change_listeners.append(self._prepare_listener(listener))

    def update(self, other: Self) -> None:
        """
        Update this configuration with the values from ``other``.
        """
        raise NotImplementedError(repr(self))

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        """
        Load dumped configuration into a new configuration instance.
        """
        raise NotImplementedError(repr(cls))

    @classmethod
    def assert_load(
        cls: type[_ConfigurationT], configuration: _ConfigurationT | None = None
    ) -> Assertion[Dump, _ConfigurationT]:
        """
        Assert that the dumped configuration can be loaded.
        """

        def _assert_load(dump: Dump) -> _ConfigurationT:
            return cls.load(dump, configuration)

        _assert_load.__qualname__ = (
            f"{_assert_load.__qualname__} for {cls.__module__}.{cls.__qualname__}.load"
        )
        return _assert_load


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class FileBasedConfiguration(Configuration):
    """
    Any configuration that is stored in a file on disk.
    """

    def __init__(self):
        super().__init__()
        self._configuration_directory: TemporaryDirectory | None = None  # type: ignore[type-arg]
        self._configuration_file_path: Path | None = None
        self._autowrite = False

    @property
    def autowrite(self) -> bool:
        """
        Whether to write this configuration to file whenever it changes.
        """
        return self._autowrite

    @autowrite.setter
    def autowrite(self, autowrite: bool) -> None:
        if autowrite:
            if not self._autowrite:
                self.on_change(self._on_change_write)
        else:
            self.remove_on_change(self._on_change_write)
        self._autowrite = autowrite

    def _on_change_write(self) -> None:
        wait_to_thread(self.write())

    async def write(self, configuration_file_path: Path | None = None) -> None:
        """
        Write the configuration to file.

        If a configuration file path is given, it will become this configuration's new
        file path, and it will be written to.

        If no configuration file path is given, the previously set file path will be
        written to, if that file exists.
        """
        if configuration_file_path is not None:
            self.configuration_file_path = configuration_file_path

        await self._write(self.configuration_file_path)

    async def _write(self, configuration_file_path: Path) -> None:
        # Change the working directory to allow absolute paths to be turned relative to the configuration file's directory
        # path.
        formats = FormatRepository()
        dump = formats.format_for(configuration_file_path.suffix[1:]).dump(self.dump())
        try:
            async with aiofiles.open(configuration_file_path, mode="w") as f:
                await f.write(dump)
        except FileNotFoundError:
            await makedirs(configuration_file_path.parent)
            await self.write()
        self._configuration_file_path = configuration_file_path

    async def read(self, configuration_file_path: Path | None = None) -> None:
        """
        Read the configuration from file.

        If a configuration file path is given, it will become this configuration's new
        file path, and its contents will be read.

        If no configuration file path is given, the previously set file path will be read,
        if that file exists.
        """
        if configuration_file_path is not None:
            self.configuration_file_path = configuration_file_path

        formats = FormatRepository()
        with (
            SerdeErrorCollection().assert_valid() as errors,
            # Change the working directory to allow relative paths to be resolved
            # against the configuration file's directory path.
            chdir(self.configuration_file_path.parent),
        ):
            async with aiofiles.open(self.configuration_file_path) as f:
                read_configuration = await f.read()
            with errors.catch(
                Str.plain(
                    "in {configuration_file_path}",
                    configuration_file_path=str(self.configuration_file_path.resolve()),
                )
            ):
                loaded_configuration = self.load(
                    formats.format_for(self.configuration_file_path.suffix[1:]).load(
                        read_configuration
                    ),
                    self,
                )
        self.update(loaded_configuration)

    def __del__(self) -> None:
        if (
            hasattr(self, "_configuration_directory")
            and self._configuration_directory is not None
        ):
            self._configuration_directory.cleanup()

    @property
    def configuration_file_path(self) -> Path:
        """
        The path to the configuration's file.
        """
        if self._configuration_file_path is None:
            if self._configuration_directory is None:
                self._configuration_directory = TemporaryDirectory()
            wait_to_thread(
                self._write(
                    Path(self._configuration_directory.name)
                    / f"{type(self).__name__}.json"
                )
            )
        return cast(Path, self._configuration_file_path)

    @configuration_file_path.setter
    def configuration_file_path(self, configuration_file_path: Path) -> None:
        if configuration_file_path == self._configuration_file_path:
            return
        formats = FormatRepository()
        formats.format_for(configuration_file_path.suffix[1:])
        self._configuration_file_path = configuration_file_path

    @configuration_file_path.deleter
    def configuration_file_path(self) -> None:
        if self._autowrite:
            raise RuntimeError(
                "Cannot remove the configuration file path while autowrite is enabled."
            )
        self._configuration_file_path = None


ConfigurationKey: TypeAlias = SupportsIndex | Hashable | type[Any]
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)


class ConfigurationCollection(
    Configuration, Generic[_ConfigurationKeyT, _ConfigurationT]
):
    """
    Any collection of :py:class:`betty.config.Configuration` values.
    """

    _configurations: (
        MutableSequence[_ConfigurationT]
        | MutableMapping[_ConfigurationKeyT, _ConfigurationT]
    )

    def __init__(
        self,
        configurations: Iterable[_ConfigurationT] | None = None,
    ):
        super().__init__()
        if configurations is not None:
            self.append(*configurations)

    def __iter__(self) -> Iterator[_ConfigurationKeyT] | Iterator[_ConfigurationT]:
        raise NotImplementedError(repr(self))

    def __contains__(self, item: Any) -> bool:
        return item in self._configurations

    def __getitem__(self, configuration_key: _ConfigurationKeyT) -> _ConfigurationT:
        raise NotImplementedError(repr(self))

    def __delitem__(self, configuration_key: _ConfigurationKeyT) -> None:
        self.remove(configuration_key)

    def __len__(self) -> int:
        return len(self._configurations)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        if list(self.keys()) != list(other.keys()):
            return False
        if list(self.values()) != list(other.values()):
            return False
        return True

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, configurations=list(self.values()))

    def _remove_without_dispatch(self, *configuration_keys: _ConfigurationKeyT) -> None:
        for configuration_key in configuration_keys:
            with suppress(LookupError):
                self._on_remove(self._configurations[configuration_key])  # type: ignore[call-overload]
            del self._configurations[configuration_key]  # type: ignore[call-overload]

    def remove(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Remove the given keys from the collection.
        """
        self._remove_without_dispatch(*configuration_keys)
        self._dispatch_change()

    def _clear_without_dispatch(self) -> None:
        self._remove_without_dispatch(*self.keys())

    def clear(self) -> None:
        """
        Clear all items from the collection.
        """
        self._clear_without_dispatch()
        self._dispatch_change()

    def _on_add(self, configuration: _ConfigurationT) -> None:
        configuration.on_change(self)

    def _on_remove(self, configuration: _ConfigurationT) -> None:
        configuration.remove_on_change(self)

    def to_index(self, configuration_key: _ConfigurationKeyT) -> int:
        """
        Get the index for the given key.
        """
        raise NotImplementedError(repr(self))

    def to_indices(self, *configuration_keys: _ConfigurationKeyT) -> Iterator[int]:
        """
        Get the indices for the given keys.
        """
        for configuration_key in configuration_keys:
            yield self.to_index(configuration_key)

    def to_key(self, index: int) -> _ConfigurationKeyT:
        """
        Get the key for the item at the given index.
        """
        raise NotImplementedError(repr(self))

    def to_keys(self, *indices: int | slice) -> Iterator[_ConfigurationKeyT]:
        """
        Get the keys for the items at the given indices.
        """
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
    def _item_type(cls) -> type[_ConfigurationT]:
        raise NotImplementedError(repr(cls))

    def keys(self) -> Iterator[_ConfigurationKeyT]:
        """
        Get all keys in this collection.
        """
        raise NotImplementedError(repr(self))

    def values(self) -> Iterator[_ConfigurationT]:
        """
        Get all values in this collection.
        """
        raise NotImplementedError(repr(self))

    def prepend(self, *configurations: _ConfigurationT) -> None:
        """
        Prepend the given values to the beginning of the sequence.
        """
        raise NotImplementedError(repr(self))

    def append(self, *configurations: _ConfigurationT) -> None:
        """
        Append the given values to the end of the sequence.
        """
        raise NotImplementedError(repr(self))

    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        """
        Insert the given values at the given index.
        """
        raise NotImplementedError(repr(self))

    def move_to_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) to the beginning of the sequence.
        """
        raise NotImplementedError(repr(self))

    def move_towards_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) one place towards the beginning of the sequence.
        """
        raise NotImplementedError(repr(self))

    def move_to_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) to the end of the sequence.
        """
        raise NotImplementedError(repr(self))

    def move_towards_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) one place towards the end of the sequence.
        """
        raise NotImplementedError(repr(self))


class ConfigurationSequence(
    ConfigurationCollection[int, _ConfigurationT], Generic[_ConfigurationT]
):
    """
    A sequence of configuration values.
    """

    def __init__(
        self,
        configurations: Iterable[_ConfigurationT] | None = None,
    ):
        self._configurations: MutableSequence[_ConfigurationT] = []
        super().__init__(configurations)

    @override
    def to_index(self, configuration_key: int) -> int:
        return configuration_key

    @override
    def to_key(self, index: int) -> int:
        return index

    @override
    @overload
    def __getitem__(self, configuration_key: int) -> _ConfigurationT:
        pass  # pragma: no cover

    @override
    @overload
    def __getitem__(self, configuration_key: slice) -> Sequence[_ConfigurationT]:
        pass  # pragma: no cover

    @override
    def __getitem__(
        self, configuration_key: int | slice
    ) -> _ConfigurationT | Sequence[_ConfigurationT]:
        return self._configurations[configuration_key]

    @override
    def __iter__(self) -> Iterator[_ConfigurationT]:
        return (configuration for configuration in self._configurations)

    @override
    def keys(self) -> Iterator[int]:
        return iter(range(0, len(self._configurations)))

    @override
    def values(self) -> Iterator[_ConfigurationT]:
        yield from self._configurations

    @override
    def update(self, other: Self) -> None:
        self._clear_without_dispatch()
        self.append(*other)

    @override
    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        else:
            configuration._clear_without_dispatch()
        with SerdeErrorCollection().assert_valid():
            configuration.append(*assert_sequence(cls._item_type().load)(dump))
        return configuration

    @override
    def dump(self) -> VoidableDump:
        return minimize(
            [configuration.dump() for configuration in self._configurations]
        )

    @override
    def prepend(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            self._on_add(configuration)
            self._configurations.insert(0, configuration)
        self._dispatch_change()

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            self._on_add(configuration)
            self._configurations.append(configuration)
        self._dispatch_change()

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        for configuration in reversed(configurations):
            self._on_add(configuration)
            self._configurations.insert(index, configuration)
        self._dispatch_change()

    @override
    def move_to_beginning(self, *configuration_keys: int) -> None:
        self.move_to_end(
            *configuration_keys,
            *[
                index
                for index in range(0, len(self._configurations))
                if index not in configuration_keys
            ],
        )

    @override
    def move_towards_beginning(self, *configuration_keys: int) -> None:
        for index in configuration_keys:
            self._configurations.insert(index - 1, self._configurations.pop(index))
        self._dispatch_change()

    @override
    def move_to_end(self, *configuration_keys: int) -> None:
        for index in configuration_keys:
            self._configurations.append(self._configurations[index])
        for index in reversed(configuration_keys):
            self._configurations.pop(index)
        self._dispatch_change()

    @override
    def move_towards_end(self, *configuration_keys: int) -> None:
        for index in reversed(configuration_keys):
            self._configurations.insert(index + 1, self._configurations.pop(index))
        self._dispatch_change()


class ConfigurationMapping(
    ConfigurationCollection[_ConfigurationKeyT, _ConfigurationT],
    Generic[_ConfigurationKeyT, _ConfigurationT],
):
    """
    A key-value mapping where values are :py:class:`betty.config.Configuration`.
    """

    def __init__(
        self,
        configurations: Iterable[_ConfigurationT] | None = None,
    ):
        self._configurations: OrderedDict[_ConfigurationKeyT, _ConfigurationT] = (
            OrderedDict()
        )
        super().__init__(configurations)

    def _minimize_item_dump(self) -> bool:
        return False

    @override
    def to_index(self, configuration_key: _ConfigurationKeyT) -> int:
        return list(self._configurations.keys()).index(configuration_key)

    @override
    def to_key(self, index: int) -> _ConfigurationKeyT:
        return list(self._configurations.keys())[index]

    @override
    def __getitem__(self, configuration_key: _ConfigurationKeyT) -> _ConfigurationT:
        return self._configurations[configuration_key]

    @override
    def __iter__(self) -> Iterator[_ConfigurationKeyT]:
        return (configuration_key for configuration_key in self._configurations)

    def _keys_without_scope(self) -> Iterator[_ConfigurationKeyT]:
        return (configuration_key for configuration_key in self._configurations)

    @override
    def keys(self) -> Iterator[_ConfigurationKeyT]:
        return self._keys_without_scope()

    @override
    def values(self) -> Iterator[_ConfigurationT]:
        yield from self._configurations.values()

    @override
    def update(self, other: Self) -> None:
        self.replace(*other.values())

    def replace(self, *values: _ConfigurationT) -> None:
        """
        Replace any existing values with the given ones.
        """
        self_keys = list(self.keys())
        other = {self._get_key(value): value for value in values}
        other_values = list(values)
        other_keys = list(map(self._get_key, other_values))

        # Update items that are kept.
        for key in self_keys:
            if key in other_keys:
                self[key].update(other[key])

        # Add items that are new.
        self._append_without_trigger(
            *(other[key] for key in other_keys if key not in self_keys)
        )

        # Remove items that should no longer be present.
        self._remove_without_dispatch(
            *(key for key in self_keys if key not in other_keys)
        )

        # Ensure everything is in the correct order. This will also trigger reactors.
        self.move_to_beginning(*other_keys)

    @override
    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        dict_dump = assert_dict()(dump)
        mapping = assert_mapping(cls._item_type().load)(
            {key: cls._load_key(value, key) for key, value in dict_dump.items()}
        )
        configuration.replace(*mapping.values())
        return configuration

    @override
    def dump(self) -> VoidableDump:
        dump = {}
        for configuration_item in self._configurations.values():
            item_dump = configuration_item.dump()
            if item_dump is not Void:
                item_dump, configuration_key = self._dump_key(item_dump)
                if self._minimize_item_dump():
                    item_dump = minimize(item_dump)
                dump[configuration_key] = item_dump
        return minimize(dump)

    @override
    def prepend(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            self._configurations[configuration_key] = configuration
            configuration.on_change(self)
        self.move_to_beginning(*map(self._get_key, configurations))

    def _append_without_trigger(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            self._configurations[configuration_key] = configuration
            configuration.on_change(self)
        self._move_to_end_without_trigger(*map(self._get_key, configurations))

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        self._append_without_trigger(*configurations)
        self._dispatch_change()

    def _insert_without_trigger(
        self, index: int, *configurations: _ConfigurationT
    ) -> None:
        current_configuration_keys = list(self._keys_without_scope())
        self._append_without_trigger(*configurations)
        self._move_to_end_without_trigger(
            *current_configuration_keys[0:index],
            *map(self._get_key, configurations),
            *current_configuration_keys[index:],
        )

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        self._insert_without_trigger(index, *configurations)
        self._dispatch_change()

    @override
    def move_to_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        for configuration_key in reversed(configuration_keys):
            self._configurations.move_to_end(configuration_key, False)
        self._dispatch_change()

    @override
    def move_towards_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        self._move_by_offset(-1, *configuration_keys)

    def _move_to_end_without_trigger(
        self, *configuration_keys: _ConfigurationKeyT
    ) -> None:
        for configuration_key in configuration_keys:
            self._configurations.move_to_end(configuration_key)

    @override
    def move_to_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        self._move_to_end_without_trigger(*configuration_keys)
        self._dispatch_change()

    @override
    def move_towards_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        self._move_by_offset(1, *configuration_keys)

    def _move_by_offset(
        self, offset: int, *configuration_keys: _ConfigurationKeyT
    ) -> None:
        current_configuration_keys = list(self._keys_without_scope())
        indices = list(self.to_indices(*configuration_keys))
        if offset > 0:
            indices.reverse()
        for index in indices:
            self._insert_without_trigger(
                index + offset,
                self._configurations.pop(current_configuration_keys[index]),
            )
        self._dispatch_change()

    def _get_key(self, configuration: _ConfigurationT) -> _ConfigurationKeyT:
        raise NotImplementedError(repr(self))

    @classmethod
    def _load_key(
        cls,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        raise NotImplementedError(repr(cls))

    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        raise NotImplementedError(repr(self))


class Configurable(Generic[_ConfigurationT]):
    """
    Any configurable object.
    """

    _configuration: _ConfigurationT

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    @property
    def configuration(self) -> _ConfigurationT:
        """
        The object's configuration.
        """
        if not hasattr(self, "_configuration"):
            raise RuntimeError(
                f"{self} has no configuration. {type(self)}.__init__() must ensure it is set."
            )
        return self._configuration
