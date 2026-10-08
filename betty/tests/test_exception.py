import pytest

from betty.exception import HumanFacingException, do_raise, reraise_with_locator
from betty.locale import default_locale_tag
from betty.localizables.static import StaticTranslations
from betty.localizer import Localizer, default_localizer
from betty.operator import Attr, Key
from betty.user.location import format_


def test_do_raise() -> None:
    expected = RuntimeError()
    try:
        do_raise(expected)
    except BaseException as actual:
        assert actual is expected  # noqa: PT017


class _DummyHumanFacingException(HumanFacingException):
    pass


class TestHumanFacingException:
    def test___str__(self) -> None:
        message = "Hello, world!"
        sut = HumanFacingException(message)
        assert str(sut) == message

    def test_localize(self) -> None:
        locale = "nl"
        localized_message = "Hallo, wereld!"
        sut = HumanFacingException(
            StaticTranslations({
                default_locale_tag: "Hello, world!",
                locale: localized_message,
            })
        )
        localizer = Localizer(locale)
        assert sut.localize(localizer) == localized_message

    def test_localize__without_locators(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        assert sut.localize(default_localizer) == "Something went wrong!"

    def test_localize__with_locators(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        sut.with_locator(Attr("my_first_locator"))
        sut.with_locator(Attr("my_second_locator"))
        assert (
            sut.localize(default_localizer)
            == "Something went wrong!\n- data.my_second_locator.my_first_locator"
        )

    def test_with_locator__and_locators(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        sut.with_locator(Attr("my_first_locator"))
        assert format_(*sut.locators, localizer=default_localizer) == (
            ".my_first_locator",
        )


def test_reraise_with_locator__without_exception() -> None:
    with reraise_with_locator():
        pass


def test_reraise_with_locator__with_irrelevant_exception() -> None:
    class _Exception(Exception):
        pass

    with pytest.raises(_Exception), reraise_with_locator():
        raise _Exception


def test_reraise_with_locator__without_contexts() -> None:
    with pytest.raises(HumanFacingException), reraise_with_locator():
        raise HumanFacingException("-")


def test_reraise_with_locator__with_contexts() -> None:
    context = Key("my_first_key")
    with (
        pytest.raises(HumanFacingException) as exc_info,
        reraise_with_locator(context),
    ):
        raise HumanFacingException("-")
    assert exc_info.value.locators == [context]
