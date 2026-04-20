import pytest

from betty.exception import HumanFacingException
from betty.factory import Factory
from betty.service_level import ServiceLevel
from betty.test_utils.data import DummyData
from betty.test_utils.factory import DummyDataManufacturable
from betty.universe import UNIVERSE


class _TargetType:
    pass


def _sync_callable_target_without_services() -> _TargetType:
    return _TargetType()


def _sync_callable_target_with_services(services: ServiceLevel, /) -> _TargetType:
    return _TargetType()


async def _async_callable_target_without_services() -> _TargetType:
    return _TargetType()


async def _async_callable_target_with_services(
    services: ServiceLevel, /
) -> _TargetType:
    return _TargetType()


class TestFactory:
    async def test_new__with_class(self) -> None:
        sut = Factory(UNIVERSE)
        assert isinstance(await sut.new(_TargetType), _TargetType)

    async def test_new__with_sync_callable_without_services(self) -> None:
        sut = Factory(UNIVERSE)
        assert isinstance(
            await sut.new(_sync_callable_target_without_services), _TargetType
        )

    async def test_new__with_sync_callable_with_services(self) -> None:
        sut = Factory(UNIVERSE)
        assert isinstance(
            await sut.new(_sync_callable_target_with_services), _TargetType
        )

    async def test_new__with_async_callable_without_services(self) -> None:
        sut = Factory(UNIVERSE)
        assert isinstance(
            await sut.new(_async_callable_target_without_services), _TargetType
        )

    async def test_new__with_async_callable_with_services(self) -> None:
        sut = Factory(UNIVERSE)
        assert isinstance(
            await sut.new(_async_callable_target_with_services), _TargetType
        )

    async def test_new__with_data_manufacturable_without_data(
        self,
    ) -> None:
        sut = Factory(UNIVERSE)
        instance = await sut.new(DummyDataManufacturable)
        assert isinstance(instance, DummyDataManufacturable)

    async def test_new__without_data_manufacturable_with_data(
        self,
    ) -> None:
        """
        We don't really test for errors here, except for this one.

        This allows code such as :py:class:`betty.plugin.factory.PluginManufacturer` to forward their target and
        data straight into new() for it to handle.
        """
        sut = Factory(UNIVERSE)
        with pytest.raises(HumanFacingException):
            await sut.new(object, DummyData())
        with pytest.raises(HumanFacingException):
            await sut.new(object, {})

    async def test_new__with_data_manufacturable_and_data(self) -> None:
        data = DummyData("Hello, world~")
        sut = Factory(UNIVERSE)
        instance = await sut.new(DummyDataManufacturable, data)
        assert isinstance(instance, DummyDataManufacturable)
        assert instance.data is data

    async def test_new__with_data_manufacturable_and_portable_data(
        self,
    ) -> None:
        value = "Hello, world~"
        sut = Factory(UNIVERSE)
        instance = await sut.new(DummyDataManufacturable, {"value": value})
        assert isinstance(instance, DummyDataManufacturable)
        assert instance.data.value == value
