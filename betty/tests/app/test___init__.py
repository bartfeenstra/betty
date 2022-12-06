from typing import Type, List, Set

import pytest

from betty.app import Extension, App, CyclicDependencyError
from betty.app.extension import ConfigurableExtension as GenericConfigurableExtension
from betty.config import Configuration, DumpedConfigurationImport, DumpedConfigurationExport
from betty.config.load import Loader
from betty.project import ExtensionConfiguration


class Tracker:
    async def track(self, carrier: List):
        raise NotImplementedError


class TrackableExtension(Extension, Tracker):
    async def track(self, carrier: List):
        carrier.append(self)


class NonConfigurableExtension(TrackableExtension):
    pass  # pragma: no cover


class ConfigurableExtensionConfiguration(Configuration):
    def __init__(self, check):
        super().__init__()
        self.check = check

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        with loader.assert_required_key(
            dumped_configuration,
            'check',
            loader.assert_int,  # type: ignore
        ) as (dumped_check, valid):
            if valid:
                loader.assert_setattr(self, 'check', dumped_check)

    def dump(self) -> DumpedConfigurationExport:
        return {
            'check': self.check
        }


class CyclicDependencyOneExtension(Extension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {CyclicDependencyTwoExtension}


class CyclicDependencyTwoExtension(Extension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {CyclicDependencyOneExtension}


class DependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class AlsoDependsOnNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class DependsOnNonConfigurableExtensionExtensionExtension(TrackableExtension):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {DependsOnNonConfigurableExtensionExtension}


class ComesBeforeNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_before(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class ComesAfterNonConfigurableExtensionExtension(TrackableExtension):
    @classmethod
    def comes_after(cls) -> Set[Type[Extension]]:
        return {NonConfigurableExtension}


class ConfigurableExtension(GenericConfigurableExtension[ConfigurableExtensionConfiguration]):
    @classmethod
    def default_configuration(cls) -> ConfigurableExtensionConfiguration:
        return ConfigurableExtensionConfiguration(False)


class TestApp:
    def test_extensions_with_one_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
            assert isinstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    def test_extensions_with_one_configurable_extension(self) -> None:
        check = 1337
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(ConfigurableExtension, True, ConfigurableExtensionConfiguration(
                check=check,
            )))
            assert isinstance(sut.extensions[ConfigurableExtension], ConfigurableExtension)
            assert check == sut.extensions[ConfigurableExtension].configuration.check

    async def test_extensions_with_one_extension_with_single_chained_dependency(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(DependsOnNonConfigurableExtensionExtensionExtension))
            carrier: List[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert 3 == len(carrier)
            assert isinstance(carrier[0], NonConfigurableExtension)
            assert isinstance(carrier[1], DependsOnNonConfigurableExtensionExtension)
            assert isinstance(carrier[2], DependsOnNonConfigurableExtensionExtensionExtension)

    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(DependsOnNonConfigurableExtensionExtension))
            sut.project.configuration.extensions.add(ExtensionConfiguration(AlsoDependsOnNonConfigurableExtensionExtension))
            carrier: List[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert 3 == len(carrier)
            assert isinstance(carrier[0], NonConfigurableExtension)
            assert DependsOnNonConfigurableExtensionExtension in [type(extension) for extension in carrier]
            assert AlsoDependsOnNonConfigurableExtensionExtension in [type(extension) for extension in carrier]

    def test_extensions_with_multiple_extensions_with_cyclic_dependencies(self) -> None:
        with pytest.raises(CyclicDependencyError):
            with App() as sut:
                sut.project.configuration.extensions.add(ExtensionConfiguration(CyclicDependencyOneExtension))
                sut.extensions

    async def test_extensions_with_comes_before_with_other_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
            sut.project.configuration.extensions.add(ExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
            carrier: List[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert 2 == len(carrier)
            assert isinstance(carrier[0], ComesBeforeNonConfigurableExtensionExtension)
            assert isinstance(carrier[1], NonConfigurableExtension)

    async def test_extensions_with_comes_before_without_other_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
            carrier: List[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert 1 == len(carrier)
            assert isinstance(carrier[0], ComesBeforeNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_with_other_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
            sut.project.configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
            carrier: List[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert 2 == len(carrier)
            assert isinstance(carrier[0], NonConfigurableExtension)
            assert isinstance(carrier[1], ComesAfterNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_without_other_extension(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
            carrier: List[TrackableExtension] = []
            await sut.dispatcher.dispatch(Tracker)(carrier)
            assert 1 == len(carrier)
            assert isinstance(carrier[0], ComesAfterNonConfigurableExtensionExtension)

    def test_extensions_addition_to_configuration(self) -> None:
        with App() as sut:
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            sut.project.configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
            assert isinstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    def test_extensions_removal_from_configuration(self) -> None:
        with App() as sut:
            sut.project.configuration.extensions.add(ExtensionConfiguration(NonConfigurableExtension))
            # Get the extensions before making configuration changes to warm the cache.
            sut.extensions
            del sut.project.configuration.extensions[NonConfigurableExtension]
            assert NonConfigurableExtension not in sut.extensions
