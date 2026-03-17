from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.asset import Asset, AssetDefinition
from betty.console import CommandDefinition, SystemExitCode
from betty.plugins.command.update_translations import (
    UpdateTranslations,
)
from betty.test_utils.console import run


class TestUpdateTranslations:
    @pytest.fixture
    async def isolated_app_with_assets(self, tmp_path: Path) -> AsyncIterator[App]:
        @AssetDefinition("dummy", assets=tmp_path)
        class _Dummy(Asset):
            pass

        async with (
            App.new_isolated(
                plugins={
                    CommandDefinition: [UpdateTranslations],
                    AssetDefinition: [_Dummy],
                }
            ) as app,
            app,
        ):
            yield app

    async def test_configure__minimal(
        self,
        mocker: MockerFixture,
        isolated_app_with_assets: App,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        m_update_translations = mocker.patch(
            "betty.locale.translation.update_translations"
        )
        await run(
            isolated_app_with_assets,
            "update-translations",
            "dummy",
            str(source),
        )
        m_update_translations.assert_awaited_once_with(
            ANY, [source], [], user=isolated_app_with_assets.user
        )

    async def test_configure__with_exclude(
        self,
        mocker: MockerFixture,
        isolated_app_with_assets: App,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        excludes = [source / "exclude1", source / "exclude2", source / "exclude3"]
        for exclude in excludes:
            exclude.mkdir()
        m_update_translations = mocker.patch(
            "betty.locale.translation.update_translations"
        )
        await run(
            isolated_app_with_assets,
            "update-translations",
            "dummy",
            str(source),
            *[arg for exclude in excludes for arg in ("--exclude", str(exclude))],
        )
        m_update_translations.assert_awaited_once_with(
            ANY, [source], list(excludes), user=isolated_app_with_assets.user
        )

    async def test_configure__with_unknown_asset(
        self, isolated_app_with_assets: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        await run(
            isolated_app_with_assets,
            "update-translations",
            "unknown-asset-id",
            str(source),
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_asset_not_found(
        self, isolated_app_with_assets: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        await run(
            isolated_app_with_assets,
            "update-translations",
            "dummy-not-found",
            str(source),
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_invalid_source_directory(
        self, isolated_app_with_assets: App, tmp_path: Path
    ) -> None:
        await run(
            isolated_app_with_assets,
            "update-translations",
            "dummy",
            str(tmp_path / "non-existent-source"),
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
