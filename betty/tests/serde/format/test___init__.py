from collections.abc import Sequence
from importlib.metadata import EntryPoint, EntryPoints

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition, PluginNotFound
from betty.serde.dump import Dump
from betty.serde.format import (
    Format,
    FormatDefinition,
    FormatError,
    FormatRepository,
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
    def load(self, dump: str) -> Dump:
        return None  # pragma: nocover

    @override
    def dump(self, dump: Voidable[Dump]) -> str:
        return ""  # pragma: nocover


@FormatDefinition(
    id="one",
    label=Plain("One"),
)
class FormatOne(_Format):
    @override
    @classmethod
    def extensions(cls) -> Sequence[str]:
        return [".one"]


@FormatDefinition(
    id="two",
    label=Plain("Two"),
)
class FormatTwo(_Format):
    @override
    @classmethod
    def extensions(cls) -> Sequence[str]:
        return [".two"]


class TestFormatRepository:
    @pytest.fixture(autouse=True)
    def _formats(self, mocker: MockerFixture) -> None:
        entry_point_group = "betty.serde_format"
        mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=FormatOne.plugin.id,
                        value=f"{FormatOne.__module__}:{FormatOne.__qualname__}.plugin",
                        group=entry_point_group,
                    ),
                    EntryPoint(
                        name=FormatTwo.plugin.id,
                        value=f"{FormatTwo.__module__}:{FormatTwo.__qualname__}.plugin",
                        group=entry_point_group,
                    ),
                ]
            ),
        )

    async def test___aiter__(self) -> None:
        sut = FormatRepository()
        assert [serde_format async for serde_format in sut] == [
            FormatOne.plugin,
            FormatTwo.plugin,
        ]

    async def test_extensions(self) -> None:
        sut = FormatRepository()
        assert await sut.extensions() == [".one", ".two"]

    async def test_get(self) -> None:
        sut = FormatRepository()
        assert await sut.get("one") is FormatOne.plugin

    async def test_get_with_unknown_plugin_id(self) -> None:
        sut = FormatRepository()
        with pytest.raises(PluginNotFound):
            await sut.get("three")


class TestFormatStr:
    def test_localize(self) -> None:
        sut = FormatStr([FormatOne.plugin, FormatTwo.plugin])
        assert sut.localize(DEFAULT_LOCALIZER) == ".one (One), .two (Two)"


async def test_format_for__with_known_format() -> None:
    assert format_for([FormatOne.plugin], ".one") is FormatOne.plugin


async def test_format_for_with_unknown_format() -> None:
    with pytest.raises(FormatError):
        format_for([], ".unknown")
