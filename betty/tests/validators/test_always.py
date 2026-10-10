from betty.localizer import default_localizer
from betty.operator import Key
from betty.validators.always import AlwaysInvalid


class TestAlwaysInvalid:
    def test(self) -> None:
        value = object()
        sut = AlwaysInvalid(value)
        assert sut.value is value
        assert default_localizer.localize(sut.message)

    def test__with_message(self) -> None:
        message = "Hello, world!"
        sut = AlwaysInvalid(object(), message=message)
        assert default_localizer.localize(sut.message) == message

    def test__with_location(self) -> None:
        location = [Key("foo"), Key("foo")]
        sut = AlwaysInvalid(object(), location=location)
        assert list(sut.location) == location
