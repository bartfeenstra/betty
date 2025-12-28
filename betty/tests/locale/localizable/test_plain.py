import pytest
from babel import Locale

from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER


class TestPlain:
    def test_text(self) -> None:
        text = "Hello, world!"
        assert Plain(text).text == text

    def test_locale(self) -> None:
        locale = Locale("nl")
        assert Plain("-", locale).locale is locale

    @pytest.mark.parametrize(
        "string",
        [
            "Hello, world!",
            "Hallo, wereld!",
        ],
    )
    def test_localize(self, string: str) -> None:
        assert Plain(string).localize(DEFAULT_LOCALIZER) == string
