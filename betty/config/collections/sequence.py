"""
Define and provide sequences of :py:class:`betty.config.Configuration` instances.
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Generic,
    TypeVar,
    overload,
)

from typing_extensions import override

from betty.assertion import assert_sequence
from betty.config import Configuration
from betty.config.collections import ConfigurationCollection

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, MutableSequence, Sequence

    from betty.serde.dump import Dump, DumpSequence

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ConfigurationSequence(
    ConfigurationCollection[int, _ConfigurationT], Generic[_ConfigurationT]
):
    """
    A sequence of configuration values.

    To test your own subclasses, use :py:class:`betty.test_utils.config.collections.sequence.ConfigurationSequenceTestBase`.
    """

    def __init__(self, configurations: Iterable[_ConfigurationT] | None = None, /):
        self._configurations: MutableSequence[_ConfigurationT] = []
        super().__init__(configurations)

    def __contains__(self, configuration: _ConfigurationT) -> bool:
        return configuration in self._configurations

    @override
    @overload
    def __getitem__(self, configuration_key: int) -> _ConfigurationT:
        pass

    @override
    @overload
    def __getitem__(self, configuration_key: slice) -> Sequence[_ConfigurationT]:
        pass

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
        return iter(range(len(self._configurations)))

    @override
    def values(self) -> Iterator[_ConfigurationT]:
        yield from self._configurations

    @override
    def replace(self, *configurations: _ConfigurationT) -> None:
        self.assert_mutable()
        self.clear()
        self.append(*configurations)

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        self.replace(*assert_sequence(self._load_item)(dump))

    @override
    def dump(self) -> DumpSequence[Dump]:
        return [configuration.dump() for configuration in self._configurations]

    @override
    def prepend(self, *configurations: _ConfigurationT) -> None:
        self.assert_mutable()
        for configuration in configurations:
            self._pre_add(configuration)
            self._configurations.insert(0, configuration)

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        self.assert_mutable()
        for configuration in configurations:
            self._pre_add(configuration)
            self._configurations.append(configuration)

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        self.assert_mutable()
        for configuration in reversed(configurations):
            self._pre_add(configuration)
            self._configurations.insert(index, configuration)
