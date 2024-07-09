"""
Provide the Configuration API.
"""

from __future__ import annotations

from abc import abstractmethod
from collections import OrderedDict
from collections.abc import Callable
from contextlib import chdir
from reprlib import recursive_repr
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
    Self,
    TypeAlias,
    TYPE_CHECKING,
)

import aiofiles
from aiofiles.os import makedirs
from typing_extensions import override

from betty.assertion import (
    assert_dict,
    assert_sequence,
    AssertionChain,
    assert_file_path,
)
from betty.assertion.error import AssertionFailedGroup
from betty.classtools import repr_instance
from betty.functools import slice_to_range
from betty.locale.localizable import plain
from betty.serde.dump import Dumpable, Dump, minimize, VoidableDump
from betty.serde.format import FormatRepository
from betty.typing import Void

if TYPE_CHECKING:
    from pathlib import Path


_ConfigurationListener: TypeAlias = Callable[[], None]
ConfigurationListener: TypeAlias = "Configuration | _ConfigurationListener"


class Configuration(Dumpable):
    """
    Any configuration object.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def update(self, other: Self) -> None:
        """
        Update this configuration with the values from ``other``.
        """
        pass

    @abstractmethod
    def load(self, dump: Dump) -> None:
        """
        Load dumped configuration.
        """
        pass


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


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

    @abstractmethod
    def __iter__(self) -> Iterator[_ConfigurationKeyT] | Iterator[_ConfigurationT]:
        pass

    def __contains__(self, item: Any) -> bool:
        return item in self._configurations

    @abstractmethod
    def __getitem__(self, configuration_key: _ConfigurationKeyT) -> _ConfigurationT:
        pass

    def __delitem__(self, configuration_key: _ConfigurationKeyT) -> None:
        self.remove(configuration_key)

    def __len__(self) -> int:
        return len(self._configurations)

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, configurations=list(self.values()))

    @abstractmethod
    def replace(self, *values: _ConfigurationT) -> None:
        """
        Replace any existing values with the given ones.
        """
        pass

    def remove(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Remove the given keys from the collection.
        """
        for configuration_key in configuration_keys:
            configuration = self._configurations[configuration_key]  # type: ignore[call-overload]
            del self._configurations[configuration_key]  # type: ignore[call-overload]
            self._on_remove(configuration)

    def clear(self) -> None:
        """
        Clear all items from the collection.
        """
        self.remove(*self.keys())

    def _on_add(self, configuration: _ConfigurationT) -> None:
        pass

    def _on_remove(self, configuration: _ConfigurationT) -> None:
        pass

    @abstractmethod
    def to_index(self, configuration_key: _ConfigurationKeyT) -> int:
        """
        Get the index for the given key.
        """
        pass

    def to_indices(self, *configuration_keys: _ConfigurationKeyT) -> Iterator[int]:
        """
        Get the indices for the given keys.
        """
        for configuration_key in configuration_keys:
            yield self.to_index(configuration_key)

    @abstractmethod
    def to_key(self, index: int) -> _ConfigurationKeyT:
        """
        Get the key for the item at the given index.
        """
        pass

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

    @abstractmethod
    def load_item(self, dump: Dump) -> _ConfigurationT:
        """
        Create and load a new item from the given dump, or raise an assertion error.

        :raise betty.assertion.error.AssertionFailed: Raised when the dump is invalid and cannot be loaded.
        """
        pass

    @abstractmethod
    def keys(self) -> Iterator[_ConfigurationKeyT]:
        """
        Get all keys in this collection.
        """
        pass

    @abstractmethod
    def values(self) -> Iterator[_ConfigurationT]:
        """
        Get all values in this collection.
        """
        pass

    @abstractmethod
    def prepend(self, *configurations: _ConfigurationT) -> None:
        """
        Prepend the given values to the beginning of the sequence.
        """
        pass

    @abstractmethod
    def append(self, *configurations: _ConfigurationT) -> None:
        """
        Append the given values to the end of the sequence.
        """
        pass

    @abstractmethod
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        """
        Insert the given values at the given index.
        """
        pass

    @abstractmethod
    def move_to_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) to the beginning of the sequence.
        """
        pass

    @abstractmethod
    def move_towards_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) one place towards the beginning of the sequence.
        """
        pass

    @abstractmethod
    def move_to_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) to the end of the sequence.
        """
        pass

    @abstractmethod
    def move_towards_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) one place towards the end of the sequence.
        """
        pass


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
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return list(self.values()) == list(other.values())

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
        self.clear()
        self.append(*other)

    @override
    def replace(self, *values: _ConfigurationT) -> None:
        self.clear()
        self.append(*values)

    @override
    def load(self, dump: Dump) -> None:
        self.replace(*assert_sequence(self.load_item)(dump))

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

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            self._on_add(configuration)
            self._configurations.append(configuration)

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        for configuration in reversed(configurations):
            self._on_add(configuration)
            self._configurations.insert(index, configuration)

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

    @override
    def move_to_end(self, *configuration_keys: int) -> None:
        for index in configuration_keys:
            self._configurations.append(self._configurations[index])
        for index in reversed(configuration_keys):
            self._configurations.pop(index)

    @override
    def move_towards_end(self, *configuration_keys: int) -> None:
        for index in reversed(configuration_keys):
            self._configurations.insert(index + 1, self._configurations.pop(index))


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

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return {
            self._get_key(configuration): configuration
            for configuration in self.values()
        } == {
            self._get_key(configuration): configuration
            for configuration in other.values()
        }

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

    @override
    def keys(self) -> Iterator[_ConfigurationKeyT]:
        return (configuration_key for configuration_key in self._configurations)

    @override
    def values(self) -> Iterator[_ConfigurationT]:
        yield from self._configurations.values()

    @override
    def update(self, other: Self) -> None:
        self.replace(*other.values())

    @override
    def replace(self, *values: _ConfigurationT) -> None:
        self_keys = list(self.keys())
        other = {self._get_key(value): value for value in values}
        other_values = list(values)
        other_keys = list(map(self._get_key, other_values))

        # Update items that are kept.
        for key in self_keys:
            if key in other_keys:
                self[key].update(other[key])

        # Add items that are new.
        self.append(*(other[key] for key in other_keys if key not in self_keys))

        # Remove items that should no longer be present.
        self.remove(*(key for key in self_keys if key not in other_keys))

        # Ensure everything is in the correct order.
        self.move_to_beginning(*other_keys)

    @override
    def load(self, dump: Dump) -> None:
        self.clear()
        self.replace(
            *assert_sequence(self.load_item)(
                [
                    self._load_key(item_value_dump, item_key_dump)
                    for item_key_dump, item_value_dump in assert_dict()(dump).items()
                ]
            )
        )

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
        self.move_to_beginning(*map(self._get_key, configurations))

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            self._configurations[configuration_key] = configuration
        self.move_to_end(*map(self._get_key, configurations))

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        current_configuration_keys = list(self.keys())
        self.append(*configurations)
        self.move_to_end(
            *current_configuration_keys[0:index],
            *map(self._get_key, configurations),
            *current_configuration_keys[index:],
        )

    @override
    def move_to_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        for configuration_key in reversed(configuration_keys):
            self._configurations.move_to_end(configuration_key, False)

    @override
    def move_towards_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        self._move_by_offset(-1, *configuration_keys)

    @override
    def move_to_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        for configuration_key in configuration_keys:
            self._configurations.move_to_end(configuration_key)

    @override
    def move_towards_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        self._move_by_offset(1, *configuration_keys)

    def _move_by_offset(
        self, offset: int, *configuration_keys: _ConfigurationKeyT
    ) -> None:
        current_configuration_keys = list(self.keys())
        indices = list(self.to_indices(*configuration_keys))
        if offset > 0:
            indices.reverse()
        for index in indices:
            self.insert(
                index + offset,
                self._configurations.pop(current_configuration_keys[index]),
            )

    @abstractmethod
    def _get_key(self, configuration: _ConfigurationT) -> _ConfigurationKeyT:
        pass

    @abstractmethod
    def _load_key(
        self,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        pass

    @abstractmethod
    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        pass


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


def assert_configuration_file(
    configuration: _ConfigurationT,
) -> AssertionChain[Path, _ConfigurationT]:
    """
    Assert that configuration can be loaded from a file.
    """

    def _assert(configuration_file_path: Path) -> _ConfigurationT:
        formats = FormatRepository()
        with (
            AssertionFailedGroup().assert_valid() as errors,
            # Change the working directory to allow relative paths to be resolved
            # against the configuration file's directory path.
            chdir(configuration_file_path.parent),
        ):
            with open(configuration_file_path) as f:
                read_configuration = f.read()
            with errors.catch(plain(f"in {str(configuration_file_path.resolve())}")):
                configuration.load(
                    formats.format_for(configuration_file_path.suffix[1:]).load(
                        read_configuration
                    )
                )
            return configuration

    return assert_file_path() | _assert


async def write_configuration_file(
    configuration: Configuration, configuration_file_path: Path
) -> None:
    """
    Write configuration to file.
    """
    formats = FormatRepository()
    dump = formats.format_for(configuration_file_path.suffix[1:]).dump(
        configuration.dump()
    )
    await makedirs(configuration_file_path.parent, exist_ok=True)
    async with aiofiles.open(configuration_file_path, mode="w") as f:
        await f.write(dump)
