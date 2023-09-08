from __future__ import annotations

from typing import Self
import multiprocessing
import pickle
import threading

import pytest

from betty.app import App
from betty.app.extension import ConfigurableExtension as GenericConfigurableExtension, Extension, CyclicDependencyError
from betty.config import Configuration
from betty.locale import Localizer
from betty.model import Entity
from betty.project import ExtensionConfiguration
from betty.serde.dump import Dump, VoidableDump
from betty.serde.load import Fields, Assertions, RequiredField, Asserter
from betty.task import Task
from betty.tests.test_task import task_success


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
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter(localizer=localizer)
        asserter.assert_record(Fields(
            RequiredField(
                'check',
                Assertions(asserter.assert_int()) | asserter.assert_setattr(configuration, 'check'),
            ),
        ))(dump)
        return configuration

    def dump(self) -> VoidableDump:
        return {
            'check': self.check
        }


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


class ConfigurableExtension(GenericConfigurableExtension[ConfigurableExtensionConfiguration]):
    @classmethod
    def default_configuration(cls) -> ConfigurableExtensionConfiguration:
        return ConfigurableExtensionConfiguration(False)


class TestApp:
    # @todo Remove this? Or not?
    async def test_lets_swim(self) -> None:
        # @todo This appears to fail only when we use both pools. Any other variations?
        # for pool in (sut.thread_pool, sut.process_pool):
        for pool_name in ('thread', 'process'):
        # for pool in (sut.process_pool, sut.process_pool):
        # for pool in (sut.thread_pool,):
        # for pool in (sut.process_pool,):
            async with App() as sut:
                sentinel: threading.Event = multiprocessing.Manager().Event()
                async with getattr(sut, f'{pool_name}_pool').batch() as batch:
                    batch.delegate(Task(task_success, sentinel))
                    # @todo 
                    # foo()
                assert sentinel.is_set()


    async def test_pickle(self) -> None:
        async with App() as sut:
            pickle.loads(pickle.dumps(sut))

    async def test_extensions_with_one_extension(self) -> None:
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(NonConfigurableExtension))
        assert isinstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    async def test_extensions_with_one_configurable_extension(self) -> None:
        check = 1337
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(ConfigurableExtension, True, ConfigurableExtensionConfiguration(
            check=check,
        )))
        assert isinstance(sut.extensions[ConfigurableExtension], ConfigurableExtension)
        assert check == sut.extensions[ConfigurableExtension].configuration.check

    async def test_extensions_with_one_extension_with_single_chained_dependency(self) -> None:
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(DependsOnNonConfigurableExtensionExtensionExtension))
        carrier: list[TrackableExtension] = []
        await sut.dispatcher.dispatch(Tracker)(carrier)
        assert 3 == len(carrier)
        assert isinstance(carrier[0], NonConfigurableExtension)
        assert isinstance(carrier[1], DependsOnNonConfigurableExtensionExtension)
        assert isinstance(carrier[2], DependsOnNonConfigurableExtensionExtensionExtension)

    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(self) -> None:
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(DependsOnNonConfigurableExtensionExtension))
        sut.project.configuration.extensions.append(ExtensionConfiguration(AlsoDependsOnNonConfigurableExtensionExtension))
        carrier: list[TrackableExtension] = []
        await sut.dispatcher.dispatch(Tracker)(carrier)
        assert 3 == len(carrier)
        assert isinstance(carrier[0], NonConfigurableExtension)
        assert DependsOnNonConfigurableExtensionExtension in [type(extension) for extension in carrier]
        assert AlsoDependsOnNonConfigurableExtensionExtension in [type(extension) for extension in carrier]

    async def test_extensions_with_multiple_extensions_with_cyclic_dependencies(self) -> None:
        with pytest.raises(CyclicDependencyError):
            sut = App()
            sut.project.configuration.extensions.append(ExtensionConfiguration(CyclicDependencyOneExtension))
            sut.extensions

    async def test_extensions_with_comes_before_with_other_extension(self) -> None:
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(NonConfigurableExtension))
        sut.project.configuration.extensions.append(ExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
        carrier: list[TrackableExtension] = []
        await sut.dispatcher.dispatch(Tracker)(carrier)
        assert 2 == len(carrier)
        assert isinstance(carrier[0], ComesBeforeNonConfigurableExtensionExtension)
        assert isinstance(carrier[1], NonConfigurableExtension)

    async def test_extensions_with_comes_before_without_other_extension(self) -> None:
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(ComesBeforeNonConfigurableExtensionExtension))
        carrier: list[TrackableExtension] = []
        await sut.dispatcher.dispatch(Tracker)(carrier)
        assert 1 == len(carrier)
        assert isinstance(carrier[0], ComesBeforeNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_with_other_extension(self) -> None:
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
        sut.project.configuration.extensions.append(ExtensionConfiguration(NonConfigurableExtension))
        carrier: list[TrackableExtension] = []
        await sut.dispatcher.dispatch(Tracker)(carrier)
        assert 2 == len(carrier)
        assert isinstance(carrier[0], NonConfigurableExtension)
        assert isinstance(carrier[1], ComesAfterNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_without_other_extension(self) -> None:
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(ComesAfterNonConfigurableExtensionExtension))
        carrier: list[TrackableExtension] = []
        await sut.dispatcher.dispatch(Tracker)(carrier)
        assert 1 == len(carrier)
        assert isinstance(carrier[0], ComesAfterNonConfigurableExtensionExtension)

    async def test_extensions_addition_to_configuration(self) -> None:
        sut = App()
        # Get the extensions before making configuration changes to warm the cache.
        sut.extensions
        sut.project.configuration.extensions.append(ExtensionConfiguration(NonConfigurableExtension))
        assert isinstance(sut.extensions[NonConfigurableExtension], NonConfigurableExtension)

    async def test_extensions_removal_from_configuration(self) -> None:
        sut = App()
        sut.project.configuration.extensions.append(ExtensionConfiguration(NonConfigurableExtension))
        # Get the extensions before making configuration changes to warm the cache.
        sut.extensions
        del sut.project.configuration.extensions[NonConfigurableExtension]
        assert NonConfigurableExtension not in sut.extensions
