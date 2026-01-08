from betty.data.simple import SimpleDefinition
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestSimpleDefinition:
    def test_load(self) -> None:
        sut = SimpleDefinition(cls=str, label=DUMMY_LOCALIZABLE)
        value = "Hello, world!"
        assert sut.load(value) == value

    def test_dump(self) -> None:
        sut = SimpleDefinition(cls=str, label=DUMMY_LOCALIZABLE)
        value = "Hello, world!"
        assert sut.dump(value) == value
