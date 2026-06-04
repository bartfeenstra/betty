from gettext import NullTranslations

import pytest

from betty.exception import (
    HumanFacingException,
    do_raise,
    reraise_with_indicator,
)
from betty.indicator.selector import Attr, Key
from betty.locale import default_locale_tag
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import Localizer, default_localizer


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
            StaticTranslations(
                {
                    default_locale_tag: "Hello, world!",
                    locale: localized_message,
                }  # ty:ignore[invalid-argument-type]
            )
        )
        localizer = Localizer(locale, NullTranslations())
        assert sut.localize(localizer) == localized_message

    def test_localize__without_indicators(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        assert sut.localize(default_localizer) == "Something went wrong!"

    def test_localize__with_indicators(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        sut.with_indicator(Attr("my_first_indicator"))
        sut.with_indicator(Attr("my_second_indicator"))
        assert (
            sut.localize(default_localizer)
            == "Something went wrong!\n- data.my_second_indicator.my_first_indicator"
        )

    def test_with_indicator__and_indicators(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        sut.with_indicator(Attr("my_first_indicator"))
        assert [indicator.format() for indicator in sut.indicators] == [
            ".my_first_indicator"
        ]


def test_reraise_with_indicator__without_exception() -> None:
    with reraise_with_indicator():
        pass


def test_reraise_with_indicator__with_irrelevant_exception() -> None:
    class _Exception(Exception):
        pass

    with pytest.raises(_Exception), reraise_with_indicator():
        raise _Exception


def test_reraise_with_indicator__without_contexts() -> None:
    with pytest.raises(HumanFacingException), reraise_with_indicator():
        raise HumanFacingException("-")


def test_reraise_with_indicator__with_contexts() -> None:
    context = Key("my_first_key")
    with (
        pytest.raises(HumanFacingException) as exc_info,
        reraise_with_indicator(context),
    ):
        raise HumanFacingException("-")
    assert exc_info.value.indicators == [context]
