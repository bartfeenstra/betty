from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import ANY

import pytest
from babel import Locale
from pytest_mock import MockerFixture

from betty.app import App
from betty.asset import AssetDirectoryDefinition
from betty.console import SystemExitCode
from betty.console.command import CommandDefinition
from betty.plugins.command.new_translation import (
    NewTranslation,
)
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.console import run


class TestNewTranslation:
    @pytest.fixture
    async def isolated_app_with_assets(
        self, isolated_app_factory: IsolatedAppFactory, tmp_path: Path
    ) -> AsyncIterator[App]:
        _DUMMY = AssetDirectoryDefinition("dummy", assets=tmp_path)

        async with isolated_app_factory(
            plugins={
                CommandDefinition: [NewTranslation],
                AssetDirectoryDefinition: [_DUMMY],
            }
        ) as app:
            yield app

    async def test_configure__minimal(
        self,
        mocker: MockerFixture,
        isolated_app_with_assets: App,
    ) -> None:
        locale = "nl"
        m_new_translation = mocker.patch("betty.locale.translation.new_translation")
        await run(
            isolated_app_with_assets,
            "new-translation",
            "dummy",
            locale,
        )
        m_new_translation.assert_awaited_once_with(ANY, Locale(locale), user=ANY)

    async def test_configure__with_unknown_asset(
        self, isolated_app_with_assets: App
    ) -> None:
        await run(
            isolated_app_with_assets,
            "new-translation",
            "unknown-asset-id",
            "nl-NL",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_invalid_locale(
        self, isolated_app_with_assets: App
    ) -> None:
        await run(
            isolated_app_with_assets,
            "new-translation",
            "dummy",
            "",
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
