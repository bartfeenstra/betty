from typing_extensions import override

from betty.config import Configurable
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
