from typing import Self

from typing_extensions import override

from betty.assertion import assert_int
from betty.config import Configurable, Configuration
from betty.portable import PortableData
from betty.test_utils.config import DummyConfiguration


class TestConfiguration:
    class _DummyConfiguration(Configuration):
        def __init__(self, value: int, /):
            super().__init__()
            self.value = value

        @override
        @classmethod
        def load(cls, portable: PortableData, /) -> Self:
            return cls(assert_int()(portable))

        @override
        def dump(self) -> PortableData:
            return self.value


class TestConfigurable:
    class _DummyConfigurable(Configurable[DummyConfiguration]):
        @override
        @classmethod
        def configuration_cls(cls) -> type[DummyConfiguration]:
            return DummyConfiguration

    def test_configuration(self) -> None:
        configuration = DummyConfiguration()
        sut = self._DummyConfigurable(configuration=configuration)
        assert sut.configuration is configuration
