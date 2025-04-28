"""
Test utilities for :py:mod:`betty.config.collections`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from betty.config import Configuration
from betty.config.collections import ConfigurationCollection, ConfigurationKey

if TYPE_CHECKING:
    from collections.abc import Iterable

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)


class ConfigurationCollectionTestBase(Generic[_ConfigurationKeyT, _ConfigurationT]):
    """
    A base class for testing :py:class:`betty.config.collections.ConfigurationCollection` implementations.
    """

    async def get_sut(
        self, configurations: Iterable[_ConfigurationT] | None = None
    ) -> ConfigurationCollection[_ConfigurationKeyT, _ConfigurationT]:
        """
        Produce the collection under test.
        """
        raise NotImplementedError

    def get_configuration_keys(
        self,
    ) -> tuple[
        _ConfigurationKeyT, _ConfigurationKeyT, _ConfigurationKeyT, _ConfigurationKeyT
    ]:
        """
        Produce four configuration keys to test the collection with.
        """
        raise NotImplementedError

    async def get_configurations(
        self,
    ) -> tuple[_ConfigurationT, _ConfigurationT, _ConfigurationT, _ConfigurationT]:
        """
        Produce four configuration items to test the collection with.
        """
        raise NotImplementedError

    async def test_replace__without_items(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.replace` implementations.
        """
        sut = await self.get_sut()
        sut.clear()
        assert len(sut) == 0
        await self.get_configurations()
        sut.replace()
        assert len(sut) == 0

    async def test_replace__with_items(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.replace` implementations.
        """
        sut = await self.get_sut()
        sut.clear()
        assert len(sut) == 0
        configurations = await self.get_configurations()
        sut.replace(*configurations)
        assert len(sut) == len(configurations)

    async def test___getitem__(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.__getitem__` implementations.
        """
        configuration = (await self.get_configurations())[0]
        sut = await self.get_sut([configuration])
        assert list(sut.values()) == [configuration]

    async def test_keys(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.keys` implementations.
        """
        configurations = await self.get_configurations()
        sut = await self.get_sut(configurations)
        assert list(sut.keys()) == [*self.get_configuration_keys()]

    async def test_values(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.values` implementations.
        """
        configurations = await self.get_configurations()
        sut = await self.get_sut(configurations)
        assert list(sut.values()) == [*configurations]

    async def test___delitem__(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.__delitem__` implementations.
        """
        configuration = (await self.get_configurations())[0]
        sut = await self.get_sut([configuration])
        del sut[self.get_configuration_keys()[0]]
        assert list(sut.values()) == []

    async def test___iter__(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.__iter__` implementations.
        """
        raise NotImplementedError

    async def test___len__(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.__len__` implementations.
        """
        configurations = await self.get_configurations()
        sut = await self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert len(sut) == 2

    async def test_prepend(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.prepend` implementations.
        """
        configurations = await self.get_configurations()
        sut = await self.get_sut(
            [
                configurations[1],
            ]
        )
        sut.prepend(configurations[0])
        assert list(sut.values()) == [configurations[0], configurations[1]]

    async def test_append(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.append` implementations.
        """
        configurations = await self.get_configurations()
        sut = await self.get_sut(
            [
                configurations[0],
            ]
        )
        sut.append(configurations[1], configurations[2])
        assert [configurations[0], configurations[1], configurations[2]] == list(
            sut.values()
        )

    async def test_insert(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.insert` implementations.
        """
        configurations = await self.get_configurations()
        sut = await self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        sut.insert(1, configurations[2], configurations[3])
        assert list(sut.values()) == [
            configurations[0],
            configurations[2],
            configurations[3],
            configurations[1],
        ]
