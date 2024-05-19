from __future__ import annotations

from typing import Self

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
from betty.serde.dump import Dump, VoidableDump
from betty.serde.load import Fields, Assertions, RequiredField, Asserter


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
        asserter = Asserter()
        asserter.assert_record(
            Fields(
                RequiredField(
                    "check",
                    Assertions(asserter.assert_int())
                    | asserter.assert_setattr(configuration, "check"),
                ),
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
    async def test_extensions_with_one_extension(self, new_temporary_app: App) -> None:
        new_temporary_app.project.configuration.extensions.enable(
            NonConfigurableExtension
        )
        assert isinstance(
            new_temporary_app.extensions[NonConfigurableExtension],
            NonConfigurableExtension,
        )

    async def test_extensions_with_one_configurable_extension(
        self, new_temporary_app: App
    ) -> None:
        check = 1337
        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(
                ConfigurableExtension,
                extension_configuration=ConfigurableExtensionConfiguration(
                    check=check,
                ),
            )
        )
        assert isinstance(
            new_temporary_app.extensions[ConfigurableExtension], ConfigurableExtension
        )
        assert (
            check
            == new_temporary_app.extensions[ConfigurableExtension].configuration.check
        )

    async def test_extensions_with_one_extension_with_single_chained_dependency(
        self, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(
            DependsOnNonConfigurableExtensionExtensionExtension
        )
        carrier: list[TrackableExtension] = []
        await new_temporary_app.dispatcher.dispatch(Tracker)(carrier)
        assert 3 == len(carrier)
        assert isinstance(carrier[0], NonConfigurableExtension)
        assert isinstance(carrier[1], DependsOnNonConfigurableExtensionExtension)
        assert isinstance(
            carrier[2], DependsOnNonConfigurableExtensionExtensionExtension
        )

    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(
        self, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(
            DependsOnNonConfigurableExtensionExtension,
            AlsoDependsOnNonConfigurableExtensionExtension,
        )
        carrier: list[TrackableExtension] = []
        await new_temporary_app.dispatcher.dispatch(Tracker)(carrier)
        assert 3 == len(carrier)
        assert isinstance(carrier[0], NonConfigurableExtension)
        assert DependsOnNonConfigurableExtensionExtension in [
            type(extension) for extension in carrier
        ]
        assert AlsoDependsOnNonConfigurableExtensionExtension in [
            type(extension) for extension in carrier
        ]

    async def test_extensions_with_multiple_extensions_with_cyclic_dependencies(
        self, new_temporary_app: App
    ) -> None:
        with pytest.raises(CyclicDependencyError):
            new_temporary_app.project.configuration.extensions.enable(
                CyclicDependencyOneExtension
            )
            new_temporary_app.extensions

    async def test_extensions_with_comes_before_with_other_extension(
        self, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(
            NonConfigurableExtension, ComesBeforeNonConfigurableExtensionExtension
        )
        carrier: list[TrackableExtension] = []
        await new_temporary_app.dispatcher.dispatch(Tracker)(carrier)
        assert 2 == len(carrier)
        assert isinstance(carrier[0], ComesBeforeNonConfigurableExtensionExtension)
        assert isinstance(carrier[1], NonConfigurableExtension)

    async def test_extensions_with_comes_before_without_other_extension(
        self, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(
            ComesBeforeNonConfigurableExtensionExtension
        )
        carrier: list[TrackableExtension] = []
        await new_temporary_app.dispatcher.dispatch(Tracker)(carrier)
        assert 1 == len(carrier)
        assert isinstance(carrier[0], ComesBeforeNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_with_other_extension(
        self, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(
            ComesAfterNonConfigurableExtensionExtension, NonConfigurableExtension
        )
        carrier: list[TrackableExtension] = []
        await new_temporary_app.dispatcher.dispatch(Tracker)(carrier)
        assert 2 == len(carrier)
        assert isinstance(carrier[0], NonConfigurableExtension)
        assert isinstance(carrier[1], ComesAfterNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_without_other_extension(
        self, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(
            ComesAfterNonConfigurableExtensionExtension
        )
        carrier: list[TrackableExtension] = []
        await new_temporary_app.dispatcher.dispatch(Tracker)(carrier)
        assert 1 == len(carrier)
        assert isinstance(carrier[0], ComesAfterNonConfigurableExtensionExtension)

    async def test_extensions_addition_to_configuration(
        self, new_temporary_app: App
    ) -> None:
        # Get the extensions before making configuration changes to warm the cache.
        new_temporary_app.extensions
        new_temporary_app.project.configuration.extensions.enable(
            NonConfigurableExtension
        )
        assert isinstance(
            new_temporary_app.extensions[NonConfigurableExtension],
            NonConfigurableExtension,
        )

    async def test_extensions_removal_from_configuration(
        self, new_temporary_app: App
    ) -> None:
        new_temporary_app.project.configuration.extensions.enable(
            NonConfigurableExtension
        )
        # Get the extensions before making configuration changes to warm the cache.
        new_temporary_app.extensions
        del new_temporary_app.project.configuration.extensions[NonConfigurableExtension]
        assert NonConfigurableExtension not in new_temporary_app.extensions
