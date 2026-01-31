from typing_extensions import override

from betty.config import HasConfiguration
from betty.test_utils.data import DummyData


class _HasConfiguration(HasConfiguration[DummyData]):
    @override
    @classmethod
    def configuration_cls(cls) -> type[DummyData]:
        return DummyData


class TestHasConfiguration:
    def test_configuration(self) -> None:
        configuration = DummyData()
        sut = _HasConfiguration(configuration=configuration)
        assert sut.configuration is configuration
