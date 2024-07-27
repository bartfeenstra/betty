from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Generic,
    Iterable,
    TypeAlias,
    TypeVar,
    SupportsIndex,
    Hashable,
    Any,
    TYPE_CHECKING,
)

from betty.config import Configuration

if TYPE_CHECKING:
    from betty.config.collections import ConfigurationCollection

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
ConfigurationKey: TypeAlias = SupportsIndex | Hashable | type[Any]
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)


class ConfigurationCollectionTestBase(
    Generic[_ConfigurationKeyT, _ConfigurationT], ABC
):
    @abstractmethod
    def get_sut(
        self, configurations: Iterable[_ConfigurationT] | None = None
    ) -> ConfigurationCollection[_ConfigurationKeyT, _ConfigurationT]:
        pass

    @abstractmethod
    def get_configuration_keys(
        self,
    ) -> tuple[
        _ConfigurationKeyT, _ConfigurationKeyT, _ConfigurationKeyT, _ConfigurationKeyT
    ]:
        pass

    @abstractmethod
    def get_configurations(
        self,
    ) -> tuple[_ConfigurationT, _ConfigurationT, _ConfigurationT, _ConfigurationT]:
        pass

    async def test_replace_without_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 0
        self.get_configurations()
        sut.replace()
        assert len(sut) == 0

    async def test_replace_with_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 0
        configurations = self.get_configurations()
        sut.replace(*configurations)
        assert len(sut) == len(configurations)

    async def test___getitem__(self) -> None:
        configuration = self.get_configurations()[0]
        sut = self.get_sut([configuration])
        assert [configuration] == list(sut.values())

    async def test_keys(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        assert [*self.get_configuration_keys()] == list(sut.keys())

    async def test_values(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        assert [*configurations] == list(sut.values())

    async def test___delitem__(self) -> None:
        configuration = self.get_configurations()[0]
        sut = self.get_sut([configuration])
        del sut[self.get_configuration_keys()[0]]
        assert list(sut.values()) == []

    async def test_iter(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        assert tuple(iter(sut)) == configurations
        assert list(sut.values()) == []

    async def test_len(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert len(sut) == 2

    async def test___eq__(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        other = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert other == sut

    async def test_prepend(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[1],
            ]
        )
        sut.prepend(configurations[0])
        assert [configurations[0], configurations[1]] == list(sut.values())

    async def test_append(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
            ]
        )
        sut.append(configurations[1], configurations[2])
        assert [configurations[0], configurations[1], configurations[2]] == list(
            sut.values()
        )

    async def test_insert(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        sut.insert(1, configurations[2], configurations[3])
        assert [
            configurations[0],
            configurations[2],
            configurations[3],
            configurations[1],
        ] == list(sut.values())

    async def test_move_to_beginning(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        sut.move_to_beginning(
            self.get_configuration_keys()[2], self.get_configuration_keys()[3]
        )
        assert [
            configurations[2],
            configurations[3],
            configurations[0],
            configurations[1],
        ] == list(sut.values())

    async def test_move_towards_beginning(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        sut.move_towards_beginning(
            self.get_configuration_keys()[2], self.get_configuration_keys()[3]
        )
        assert [
            configurations[0],
            configurations[2],
            configurations[3],
            configurations[1],
        ] == list(sut.values())

    async def test_move_to_end(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        sut.move_to_end(
            self.get_configuration_keys()[0], self.get_configuration_keys()[1]
        )
        assert [
            configurations[2],
            configurations[3],
            configurations[0],
            configurations[1],
        ] == list(sut.values())

    async def test_move_towards_end(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        sut.move_towards_end(
            self.get_configuration_keys()[0], self.get_configuration_keys()[1]
        )
        assert [
            configurations[2],
            configurations[0],
            configurations[1],
            configurations[3],
        ] == list(sut.values())
