import pytest

from betty.locale import default_locale_tag
from betty.localizables.static import StaticTranslations
from betty.localizer import Localizer, default_localizer
from betty.locator.operator import Attr, Key
from betty.validation import Invalid, locate


class TestInvalid:
    def test___str__(self) -> None:
        message = "Hello, world!"
        sut = Invalid(message)
        assert str(sut) == message

    def test_localize(self) -> None:
        locale = "nl"
        localized_message = "Hallo, wereld!"
        sut = Invalid(
            StaticTranslations({
                default_locale_tag: "Hello, world!",
                locale: localized_message,
            })
        )
        localizer = Localizer(locale)
        assert sut.localize(localizer) == localized_message

    def test_localize__without_indicators(self) -> None:
        sut = Invalid(StaticTranslations("Something went wrong!"))
        assert sut.localize(default_localizer) == "Something went wrong!"

    def test_localize__with_indicators(self) -> None:
        sut = Invalid(StaticTranslations("Something went wrong!"))
        sut.locate(Attr("my_first_indicator"))
        sut.locate(Attr("my_second_indicator"))
        assert (
            sut.localize(default_localizer)
            == "Something went wrong!\n- data.my_second_indicator.my_first_indicator"
        )

    def test_indicate__with_indicators(self) -> None:
        sut = Invalid(StaticTranslations("Something went wrong!"))
        sut.locate(Attr("my_first_indicator"))
        assert [indicator.format() for indicator in sut.location] == [
            ".my_first_indicator"
        ]


def test_indicate__without_exception() -> None:
    with locate():
        pass


def test_indicate__with_irrelevant_exception() -> None:
    class _Exception(Exception):
        pass

    with pytest.raises(_Exception), locate():
        raise _Exception


def test_indicate__without_contexts() -> None:
    with pytest.raises(Invalid), locate():
        raise Invalid("-")


def test_indicate__with_contexts() -> None:
    context = Key("my_first_key")
    with (
        pytest.raises(Invalid) as exc_info,
        locate(context),
    ):
        raise Invalid("-")
    assert exc_info.value.location == [context]
