from typing_extensions import override

from betty.locale.localizable import CountableLocalizable, Localizable, LocalizableCount
from betty.locale.localizable.plain import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER


class TestCountableLocalizable:
    class _Sut(CountableLocalizable):
        @override
        def count(self, count: LocalizableCount, /) -> Localizable:
            return Plain("{format_placeholder}")

    def test_format(self) -> None:
        sut = self._Sut()
        assert (
            sut.count(9)
            .format(format_placeholder="format-value")
            .localize(DEFAULT_LOCALIZER)
            == "format-value"
        )
