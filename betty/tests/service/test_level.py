import pytest

from betty.exception import HumanFacingException
from betty.service.level import ServiceLevel
from betty.test_utils.data import DummyData
from betty.test_utils.service.level import DummyDataManufacturable


class _TargetType:
    pass


def _sync_callable_target() -> _TargetType:
    return _TargetType()


async def _async_callable_target() -> _TargetType:
    return _TargetType()


class TestServiceLevel:
    def test_plugins(self) -> None:
        sut = ServiceLevel()
        assert len(list(sut.plugins.types))

    async def test_new_target__with_class(self) -> None:
        sut = ServiceLevel()
        assert isinstance(await sut.new_target(_TargetType), _TargetType)

    async def test_new_target__with_sync_callable(self) -> None:
        sut = ServiceLevel()
        assert isinstance(await sut.new_target(_sync_callable_target), _TargetType)

    async def test_new_target__with_async_callable(self) -> None:
        sut = ServiceLevel()
        assert isinstance(await sut.new_target(_async_callable_target), _TargetType)

    async def test_new_target__with_data_manufacturable_without_configuration(
        self,
    ) -> None:
        sut = ServiceLevel()
        instance = await sut.new_target(DummyDataManufacturable)
        assert isinstance(instance, DummyDataManufacturable)

    async def test_new_target__without_data_manufacturable_with_configuration(
        self,
    ) -> None:
        """
        We don't really test for errors here, except for this one.

        This allows code such as :py:class:`betty.plugin.config.PluginConfiguration` to forward their target and
        configuration straight into new_target() for it to handle.
        """
        sut = ServiceLevel()
        with pytest.raises(HumanFacingException):
            await sut.new_target(object, DummyData())
        with pytest.raises(HumanFacingException):
            await sut.new_target(object, {})

    async def test_new_target__with_data_manufacturable_and_configuration(self) -> None:
        configuration = DummyData("Hello, world~")
        sut = ServiceLevel()
        instance = await sut.new_target(DummyDataManufacturable, configuration)
        assert isinstance(instance, DummyDataManufacturable)
        assert instance.configuration is configuration

    async def test_new_target__with_data_manufacturable_and_portable_configuration(
        self,
    ) -> None:
        value = "Hello, world~"
        sut = ServiceLevel()
        instance = await sut.new_target(DummyDataManufacturable, {"value": value})
        assert isinstance(instance, DummyDataManufacturable)
        assert instance.configuration.value == value
