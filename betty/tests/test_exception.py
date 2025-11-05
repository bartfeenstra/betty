from gettext import NullTranslations

from betty.data import Attr
from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import Plain, StaticTranslations
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer


class _DummyHumanFacingException(HumanFacingException):
    pass


class TestHumanFacingException:
    def test___str__(self) -> None:
        message = "Hello, world!"
        sut = HumanFacingException(Plain(message))
        assert str(sut) == message

    def test_localize(self) -> None:
        locale = "nl"
        localized_message = "Hallo, wereld!"
        message = {
            DEFAULT_LOCALE: "Hello, world!",
            locale: localized_message,
        }
        sut = HumanFacingException(StaticTranslations(message))
        localizer = Localizer(locale, NullTranslations())
        assert sut.localize(localizer) == localized_message

    def test_localize__without_contexts(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    def test_localize__with_contexts(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        sut.within_context(Attr("my_first_context"), Attr("my_second_context"))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- data.my_second_context.my_first_context"
        )

    def test_within_context__and_contexts(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        sut.within_context(Attr("my_first_context"))
        assert [context.localize(DEFAULT_LOCALIZER) for context in sut.contexts] == [
            ".my_first_context"
        ]
