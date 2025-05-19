from gettext import NullTranslations

from betty.exception import UserFacingException, do_raise
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import plain, static
from betty.locale.localizer import Localizer


def test_do_raise() -> None:
    expected = RuntimeError()
    try:
        do_raise(expected)
    except BaseException as actual:
        assert actual is expected  # noqa PT017


class TestUserFacingException:
    def test___str__(self) -> None:
        message = "Hello, world!"
        sut = UserFacingException(plain(message))
        assert str(sut) == message

    def test_localize(self) -> None:
        locale = "nl"
        localized_message = "Hallo, wereld!"
        message = {
            DEFAULT_LOCALE: "Hello, world!",
            locale: localized_message,
        }
        sut = UserFacingException(static(message))
        localizer = Localizer(locale, NullTranslations())
        assert sut.localize(localizer) == localized_message
