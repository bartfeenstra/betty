from pathlib import Path
from unittest.mock import ANY

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command.commands.extension_update_translations import (
    ExtensionUpdateTranslations,
)
from betty.plugin import PluginDefinition
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandPluginTestBase
from betty.tests.console.command import ExtensionTranslationTestBase


class TestExtensionUpdateTranslationsDefinition(CommandPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return ExtensionUpdateTranslations.plugin


class TestExtensionUpdateTranslations(ExtensionTranslationTestBase):
    async def test_configure__minimal(
        self,
        mocker: MockerFixture,
        temporary_app_with_extensions: App,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        m_update_extension_translations = mocker.patch(
            "betty.locale.translation.project.extension.update_extension_translations"
        )
        await run(
            temporary_app_with_extensions,
            "extension-update-translations",
            "dummy-with-assets",
            str(source),
        )
        m_update_extension_translations.assert_awaited_once_with(ANY, source, None)

    async def test_configure__with_exclude(
        self,
        mocker: MockerFixture,
        temporary_app_with_extensions: App,
        tmp_path: Path,
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        excludes = [source / "exclude1", source / "exclude2", source / "exclude3"]
        for exclude in excludes:
            exclude.mkdir()
        m_update_extension_translations = mocker.patch(
            "betty.locale.translation.project.extension.update_extension_translations"
        )
        await run(
            temporary_app_with_extensions,
            "extension-update-translations",
            "dummy-with-assets",
            str(source),
            *[arg for exclude in excludes for arg in ("--exclude", str(exclude))],
        )
        m_update_extension_translations.assert_awaited_once_with(
            ANY, source, set(excludes)
        )

    async def test_configure__with_unknown_extension(
        self, temporary_app_with_extensions: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        await run(
            temporary_app_with_extensions,
            "extension-update-translations",
            "unknown-extension-id",
            str(source),
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_extension_without_assets_directory(
        self, temporary_app_with_extensions: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        await run(
            temporary_app_with_extensions,
            "extension-update-translations",
            "dummy-without-assets-directory-extension",
            str(source),
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )

    async def test_configure__with_invalid_source_directory(
        self, temporary_app_with_extensions: App, tmp_path: Path
    ) -> None:
        await run(
            temporary_app_with_extensions,
            "extension-update-translations",
            "dummy-with-assets",
            str(tmp_path / "non-existent-source"),
            expected_exit_code=SystemExitCode.ERROR_CONSOLE_USAGE,
        )
