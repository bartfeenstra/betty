from typing import Self

from typing_extensions import override

from betty.assertion import assert_int
from betty.config import Configurable, Configuration
from betty.serde.dump import Dump
from betty.test_utils.config import DummyConfiguration


class TestConfiguration:
    class _DummyConfiguration(Configuration):
        def __init__(self, value: int, /):
            super().__init__()
            self.value = value

        @override
        @classmethod
        def load(cls, dump: Dump, /) -> Self:
            return cls(assert_int()(dump))

        @override
        def dump(self) -> Dump:
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
