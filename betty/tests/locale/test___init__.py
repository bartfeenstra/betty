from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.locale import negotiate_locale, Localey, to_locale

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestNegotiateLocale:
    @pytest.mark.parametrize(
        ("expected", "preferred_locale", "available_locales"),
        [
            ("nl", "nl", ["nl"]),
            ("nl-NL", "nl", ["nl-NL"]),
            ("nl", "nl-NL", ["nl"]),
            ("nl-NL", "nl-NL", ["nl", "nl-BE", "nl-NL"]),
            ("nl", "nl", ["nl", "en"]),
            ("nl", "nl", ["en", "nl"]),
            ("nl-NL", "nl-BE", ["nl-NL"]),
        ],
    )
    async def test(
        self,
        expected: Localey | None,
        preferred_locale: Localey,
        available_locales: Sequence[Localey],
    ) -> None:
        actual = negotiate_locale(preferred_locale, available_locales)
        assert expected == (to_locale(actual) if actual else actual)
