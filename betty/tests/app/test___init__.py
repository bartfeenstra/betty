from __future__ import annotations

from typing import Self, TYPE_CHECKING

import pytest

from betty.app import App
from betty.app.extension import (
    ConfigurableExtension as GenericConfigurableExtension,
    Extension,
    CyclicDependencyError,
)
from betty.config import Configuration
from betty.model import Entity
from betty.project import ExtensionConfiguration
from betty.serde.load import (
    RequiredField,
    assert_record,
    assert_int,
    assert_setattr,
)

if TYPE_CHECKING:
    from betty.serde.dump import Dump, VoidableDump


class DummyEntity(Entity):
    pass


class Tracker:
    async def track(self, carrier: list[Self]) -> None:
        raise NotImplementedError(repr(self))


class TrackableExtension(Extension, Tracker):
    async def track(self, carrier: list[Self]) -> None:
        carrier.append(self)


class NonConfigurableExtension(TrackableExtension):
    pass


class ConfigurableExtensionConfiguration(Configuration):
    def __init__(self, check: int = 0):
        super().__init__()
        self.check = check

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        assert_record(
            RequiredField(
                "check", assert_int() | assert_setattr(configuration, "check")
            )
        )(dump)
        return configuration

    def dump(self) -> VoidableDump:
        return {"check": self.check}


class CyclicDependencyOneExtension(Extension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {CyclicDependencyTwoExtension}


class CyclicDependencyTwoExtension(Extension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {CyclicDependencyOneExtension}


class DependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {NonConfigurableExtension}


class AlsoDependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {NonConfigurableExtension}


class DependsOnNonConfigurableExtensionExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {DependsOnNonConfigurableExtensionExtension}


class ComesBeforeNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_before(cls) -> set[type[Extension]]:
        return {NonConfigurableExtension}


class ComesAfterNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_after(cls) -> set[type[Extension]]:
        return {NonConfigurableExtension}


class ConfigurableExtension(
    GenericConfigurableExtension[ConfigurableExtensionConfiguration]
):
    @classmethod
    def default_configuration(cls) -> ConfigurableExtensionConfiguration:
        return ConfigurableExtensionConfiguration(False)


class TestApp:
    async def test_extensions_with_one_extension(self) -> None:
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(NonConfigurableExtension)
            )
            assert isinstance(
                sut.extensions[NonConfigurableExtension], NonConfigurableExtension
            )

    async def test_extensions_with_one_configurable_extension(self) -> None:
        check = 1337
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(
                    ConfigurableExtension,
                    extension_configuration=ConfigurableExtensionConfiguration(
                        check=check,
                    ),
                )
            )
            assert isinstance(
                sut.extensions[ConfigurableExtension], ConfigurableExtension
            )
            assert check == sut.extensions[ConfigurableExtension].configuration.check

    async def test_extensions_with_one_extension_with_single_chained_dependency(
        self,
    ) -> None:
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(
                    DependsOnNonConfigurableExtensionExtensionExtension
                )
            )
            carrier: list[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert len(carrier) == 3
            assert isinstance(carrier[0], NonConfigurableExtension)
            assert isinstance(carrier[1], DependsOnNonConfigurableExtensionExtension)
            assert isinstance(
                carrier[2], DependsOnNonConfigurableExtensionExtensionExtension
            )

    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(
        self,
    ) -> None:
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(DependsOnNonConfigurableExtensionExtension)
            )
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(AlsoDependsOnNonConfigurableExtensionExtension)
            )
            carrier: list[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert len(carrier) == 3
            assert isinstance(carrier[0], NonConfigurableExtension)
            assert DependsOnNonConfigurableExtensionExtension in [
                type(extension) for extension in carrier
            ]
            assert AlsoDependsOnNonConfigurableExtensionExtension in [
                type(extension) for extension in carrier
            ]

    async def test_extensions_with_multiple_extensions_with_cyclic_dependencies(
        self,
    ) -> None:
        async with App.new_temporary() as sut, sut:
            with pytest.raises(CyclicDependencyError):  # noqa PT012
                sut.project.configuration.extensions.append(
                    ExtensionConfiguration(CyclicDependencyOneExtension)
                )
                sut.extensions  # noqa B018

    async def test_extensions_with_comes_before_with_other_extension(self) -> None:
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(NonConfigurableExtension)
            )
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension)
            )
            carrier: list[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert len(carrier) == 2
            assert isinstance(carrier[0], ComesBeforeNonConfigurableExtensionExtension)
            assert isinstance(carrier[1], NonConfigurableExtension)

    async def test_extensions_with_comes_before_without_other_extension(self) -> None:
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension)
            )
            carrier: list[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert len(carrier) == 1
            assert isinstance(carrier[0], ComesBeforeNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_with_other_extension(self) -> None:
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension)
            )
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(NonConfigurableExtension)
            )
            carrier: list[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert len(carrier) == 2
            assert isinstance(carrier[0], NonConfigurableExtension)
            assert isinstance(carrier[1], ComesAfterNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_without_other_extension(self) -> None:
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension)
            )
            carrier: list[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert len(carrier) == 1
            assert isinstance(carrier[0], ComesAfterNonConfigurableExtensionExtension)

    async def test_extensions_addition_to_configuration(self) -> None:
        async with App.new_temporary() as sut, sut:
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions  # noqa B018
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(NonConfigurableExtension)
            )
            assert isinstance(
                sut.extensions[NonConfigurableExtension], NonConfigurableExtension
            )

    async def test_extensions_removal_from_configuration(self) -> None:
        async with App.new_temporary() as sut, sut:
            sut.project.configuration.extensions.append(
                ExtensionConfiguration(NonConfigurableExtension)
            )
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions  # noqa B018
            del sut.project.configuration.extensions[NonConfigurableExtension]
            assert NonConfigurableExtension not in sut.extensions

    async def test_fetcher(self) -> None:
        async with App.new_temporary() as sut, sut:
            assert sut.fetcher is not None
