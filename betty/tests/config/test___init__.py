from typing_extensions import override

from betty.assertion import assert_int
from betty.config import Configurable, Configuration
from betty.serde.dump import Dump
from betty.test_utils.config import DummyConfiguration


class TestConfiguration:
    class _DummyConfiguration(Configuration):
        def __init__(self, value: int):
            super().__init__()
            self.value = value

        @override
        def load(self, dump: Dump, /) -> None:
            self.value = assert_int()(dump)

        @override
        def dump(self) -> Dump:
            return self.value


class TestConfigurable:
    class _DummyConfigurable(Configurable[DummyConfiguration]):
        pass

    def test_configuration(self) -> None:
        configuration = DummyConfiguration()
        sut = self._DummyConfigurable(configuration=configuration)
        assert sut.configuration is configuration
