from typing import override

import pytest

from betty.localizable import CountableLocalizable, Localizable, LocalizableCount
from betty.localizables.static import StaticTranslations
from betty.localized import LocalizedStr
from betty.localizer import Localizer, default_localizer


class TestLocalizable:
    class _Sut(Localizable):
        @override
        def localize(self, localizer: Localizer, /) -> LocalizedStr:
            return LocalizedStr("{format_placeholder}")

    def test_format(self) -> None:
        sut = self._Sut()
        assert (
            sut.format(format_placeholder="format-value").localize(default_localizer)
            == "format-value"
        )

    def test___str__(self) -> None:
        sut = self._Sut()
        with pytest.warns(
            UserWarning,  # noqa: PT030
        ):
            assert str(sut) == "{format_placeholder}"


class TestCountableLocalizable:
    class _Sut(CountableLocalizable):
        @override
        def count(self, count: LocalizableCount, /) -> Localizable:
            return StaticTranslations("{format_placeholder}")

    def test_format(self) -> None:
        sut = self._Sut()
        assert (
            sut
            .count(9)
            .format(format_placeholder="format-value")
            .localize(default_localizer)
            == "format-value"
        )
