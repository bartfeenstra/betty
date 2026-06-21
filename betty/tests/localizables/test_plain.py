import pytest
from babel import Locale

from betty.localizables.plain import Plain
from betty.localizer import default_localizer


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
        assert Plain(string).localize(default_localizer) == string
