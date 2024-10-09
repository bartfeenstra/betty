import pytest
from importlib.metadata import EntryPoints, EntryPoint

from pytest_mock import MockerFixture
from typing_extensions import override

from betty.locale.localizable import plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import ShorthandPluginBase, PluginNotFound
from betty.serde.dump import Dump
from betty.serde.format import (
    FormatStr,
    Format,
    FormatRepository,
    FormatError,
    format_for,
)
from betty.typing import Voidable


class _Format(ShorthandPluginBase, Format):
    @override
    def load(self, dump: str) -> Dump:
        return None  # pragma: nocover

    @override
    def dump(self, dump: Voidable[Dump]) -> str:
        return ""  # pragma: nocover


class FormatOne(_Format):
    _plugin_id = "one"
    _plugin_label = plain("One")

    @override
    @classmethod
    def extensions(cls) -> set[str]:
        return {".one"}


class FormatTwo(_Format):
    _plugin_id = "two"
    _plugin_label = plain("Two")

    @override
    @classmethod
    def extensions(cls) -> set[str]:
        return {".two"}


class TestFormatRepository:
    @pytest.fixture(autouse=True)
    def _formats(self, mocker: MockerFixture) -> None:
        entry_point_group = "betty.serde_format"
        mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=FormatOne.plugin_id(),
                        value=f"{FormatOne.__module__}:{FormatOne.__qualname__}",
                        group=entry_point_group,
                    ),
                    EntryPoint(
                        name=FormatTwo.plugin_id(),
                        value=f"{FormatTwo.__module__}:{FormatTwo.__qualname__}",
                        group=entry_point_group,
                    ),
                ]
            ),
        )

    async def test___aiter__(self) -> None:
        sut = FormatRepository()
        assert [serde_format async for serde_format in sut] == [FormatOne, FormatTwo]

    async def test_extensions(self) -> None:
        sut = FormatRepository()
        assert await sut.extensions() == {".one", ".two"}

    async def test_get(self) -> None:
        sut = FormatRepository()
        assert await sut.get("one") is FormatOne

    async def test_get_with_unknown_plugin_id(self) -> None:
        sut = FormatRepository()
        with pytest.raises(PluginNotFound):
            await sut.get("three")


class TestFormatStr:
    def test_localize(self) -> None:
        sut = FormatStr([FormatOne, FormatTwo])
        assert sut.localize(DEFAULT_LOCALIZER) == ".one (One), .two (Two)"


class TestFormatFor:
    async def test_with_known_format(self) -> None:
        assert format_for([FormatOne], ".one") is FormatOne

    async def test_format_for_with_unknown_format(self) -> None:
        with pytest.raises(FormatError):
            assert format_for([], ".unknown")
