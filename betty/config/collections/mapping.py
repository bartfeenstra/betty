"""
Define and provide key-value mappings of :py:class:`betty.config.Configuration` instances.
"""

from __future__ import annotations

from abc import abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Self

from typing_extensions import TypeVar, override

from betty.assertion import assert_sequence
from betty.config import Configuration
from betty.config.collections import ConfigurationCollection, ConfigurationKey

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, MutableMapping

    from betty.portable import PortableData, PortableSequence

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)
_ResolvableConfigurationKeyT = TypeVar("_ResolvableConfigurationKeyT")


class _ConfigurationMapping(
    ConfigurationCollection[
        _ConfigurationKeyT, _ResolvableConfigurationKeyT, _ConfigurationT
    ]
):
    _configurations: MutableMapping[_ConfigurationKeyT, _ConfigurationT]

    def __init__(self, configurations: Iterable[_ConfigurationT] | None = None, /):
        self._configurations: MutableMapping[_ConfigurationKeyT, _ConfigurationT] = {}
        super().__init__(configurations)

    def __contains__(
        self, configuration_key: _ConfigurationKeyT | _ResolvableConfigurationKeyT
    ) -> bool:
        return self._resolve_key(configuration_key) in self._configurations

    @override
    def __getitem__(
        self, configuration_key: _ConfigurationKeyT | _ResolvableConfigurationKeyT
    ) -> _ConfigurationT:
        return self._configurations[self._resolve_key(configuration_key)]

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
    def replace(self, *configurations: _ConfigurationT) -> None:
        self.clear()
        self.append(*configurations)

    @override
    def prepend(self, *configurations: _ConfigurationT) -> None:
        self.insert(0, *configurations)

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            with suppress(KeyError):
                del self._configurations[configuration_key]
            self._configurations[configuration_key] = configuration

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        self.remove(*map(self._get_key, configurations))
        existing_configurations = list(self.values())
        self._configurations = {
            self._get_key(configuration): configuration
            for configuration in (
                *existing_configurations[:index],
                *configurations,
                *existing_configurations[index:],
            )
        }

    @abstractmethod
    def _get_key(self, configuration: _ConfigurationT, /) -> _ConfigurationKeyT:
        pass


class OrderedConfigurationMapping(
    _ConfigurationMapping[
        _ConfigurationKeyT, _ResolvableConfigurationKeyT, _ConfigurationT
    ]
):
    """
    An ordered key-value mapping where values are :py:class:`betty.config.Configuration`.

    To test your own subclasses, use :py:class:`betty.test_utils.config.collections.mapping.OrderedConfigurationMappingTestBase`.
    """

    @override
    def __eq__(self, other: Any) -> bool:
        eq = super().__eq__(other)
        if eq is not True:
            return eq
        if not isinstance(other, type(self)):
            return NotImplemented
        return list(self.keys()) == list(other.keys())

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(assert_sequence(cls._item_cls().load)(portable))

    @override
    def dump(self) -> PortableSequence:
        return [
            configuration_item.dump()
            for configuration_item in self._configurations.values()
        ]
