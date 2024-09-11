from pathlib import Path
from unittest.mock import ANY

from pytest_mock import MockerFixture

from betty.app import App
from betty.test_utils.cli import run
from betty.tests.cli.commands import ExtensionTranslationTestBase


class TestExtensionUpdateTranslations(ExtensionTranslationTestBase):
    async def test(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        m_update_extension_translations = mocker.patch(
            "betty.locale.translation.update_extension_translations"
        )
        await run(
            new_temporary_app,
            "extension-update-translations",
            "with-assets",
            str(source),
        )
        m_update_extension_translations.assert_awaited_once_with(ANY, source, set())

    async def test_with_exclude(
        self, mocker: MockerFixture, new_temporary_app: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        excludes = [source / "exclude1", source / "exclude2", source / "exclude3"]
        for exclude in excludes:
            exclude.mkdir()
        m_update_extension_translations = mocker.patch(
            "betty.locale.translation.update_extension_translations"
        )
        await run(
            new_temporary_app,
            "extension-update-translations",
            "with-assets",
            str(source),
            *[arg for exclude in excludes for arg in ("--exclude", str(exclude))],
        )
        m_update_extension_translations.assert_awaited_once_with(
            ANY, source, set(excludes)
        )

    async def test_with_unknown_extension(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        await run(
            new_temporary_app,
            "extension-update-translations",
            "unknown-extension-id",
            str(source),
            expected_exit_code=2,
        )

    async def test_with_extension_without_assets_directory(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        source = tmp_path / "source"
        source.mkdir()
        await run(
            new_temporary_app,
            "extension-update-translations",
            "without-assets",
            str(source),
            expected_exit_code=2,
        )

    async def test_with_invalid_source_directory(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        await run(
            new_temporary_app,
            "extension-update-translations",
            "with-assets",
            str(tmp_path / "non-existent-source"),
            expected_exit_code=2,
        )
