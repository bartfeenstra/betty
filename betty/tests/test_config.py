from typing import Self

import pytest
from typing_extensions import override

from betty.config import Configurable, ConfigurationDependentSelfFactory, new_target
from betty.factory import FactoryError
from betty.service.level.factory import ServiceLevelTarget
from betty.service.level.universal import universe
from betty.test_utils.data import DummyData


class TestConfigurable:
    class _DummyConfigurable(Configurable[DummyData]):
        @override
        @classmethod
        def configuration_cls(cls) -> type[DummyData]:
            return DummyData

    def test_configuration(self) -> None:
        configuration = DummyData()
        sut = self._DummyConfigurable(configuration=configuration)
        assert sut.configuration is configuration


class _DummyConfiguration(DummyData):
    pass


class _DummyConfigurable(Configurable[DummyData]):
    @override
    @classmethod
    def configuration_cls(cls) -> type[DummyData]:
        return _DummyConfiguration


class _OptionalDummyConfigurable(_DummyConfigurable):
    def __init__(self):
        super().__init__(configuration=_DummyConfiguration())


class _RequiredDummyConfigurable(
    _DummyConfigurable, ConfigurationDependentSelfFactory[_DummyConfiguration]
):
    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: _DummyConfiguration
    ) -> ServiceLevelTarget[Self]:
        return lambda: cls(configuration=configuration)


async def test_new_target__with_configurable_with_configuration() -> None:
    configuration = _DummyConfiguration()
    instance = await universe.new_target(
        new_target(_RequiredDummyConfigurable, configuration)
    )
    assert isinstance(instance, _RequiredDummyConfigurable)
    assert instance.configuration is configuration


async def test_new_target__with_configurable_without_configuration() -> None:
    instance = await universe.new_target(new_target(_OptionalDummyConfigurable))
    assert isinstance(instance, _OptionalDummyConfigurable)


def test_new_target__with_non_configurable_with_configuration() -> None:
    with pytest.raises(FactoryError):
        new_target(object, _DummyConfiguration())


async def test_new_target__with_non_configurable_without_configuration() -> None:
    instance = await universe.new_target(new_target(object))
    assert isinstance(instance, object)


async def test_new_target__with_configuration_of_wrong_type() -> None:
    configuration = DummyData()
    with pytest.raises(FactoryError):
        new_target(_RequiredDummyConfigurable, configuration)
