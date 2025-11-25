import pytest
from typing_extensions import override

from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.plugin import PluginDefinition
from betty.serde.dump import Dump
from betty.serde.format import (
    Format,
    FormatDefinition,
    FormatError,
    FormatStr,
    format_for,
)
from betty.test_utils.plugin import PluginDefinitionClassTestBase
from betty.typing import Voidable


class TestFormatDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return FormatDefinition


class _Format(Format):
    @override
    def load(self, dump: str, /) -> Dump:
        return None  # pragma: nocover

    @override
    def dump(self, dump: Voidable[Dump], /) -> str:
        return ""  # pragma: nocover


@FormatDefinition(
    id="one",
    label="One",
)
class FormatOne(_Format):
    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return MediaType("text/x.betty.test.one", extensions=[".one"])


@FormatDefinition(
    id="two",
    label="Two",
)
class FormatTwo(_Format):
    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return MediaType("text/x.betty.test.two", extensions=[".two"])


class TestFormatStr:
    def test_localize(self) -> None:
        sut = FormatStr([FormatOne.plugin, FormatTwo.plugin])
        assert sut.localize(DEFAULT_LOCALIZER) == ".one (One), .two (Two)"


def test_format_for__with_known_format() -> None:
    assert format_for([FormatOne.plugin], ".one") is FormatOne.plugin


def test_format_for_with_unknown_format() -> None:
    with pytest.raises(FormatError):
        format_for([], ".unknown")
