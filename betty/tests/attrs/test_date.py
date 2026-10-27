from __future__ import annotations

from betty.attrs.date import HasAnyDate


class TestHasAnyDate:
    def test_date(self) -> None:
        sut = HasAnyDate()
        assert sut.date is None
