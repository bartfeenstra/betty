from pathlib import Path

from betty.app import App
from betty.asset import StaticAssetRepository
from betty.cache.file import BinaryFileCache
from betty.document import Document
from betty.locale.translation import AssetTranslationRepository
from betty.plugins.content.raspberry_mint_incomplete_translation_warning import (
    IncompleteTranslationWarning,
)
from betty.project import Project


class TestIncompleteTranslationWarning:
    async def test_build_template__with_complete_translations(
        self, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(
                isolated_app, support_plugins=[IncompleteTranslationWarning]
            ) as project,
            project,
        ):
            sut = await IncompleteTranslationWarning.new(project)
            actual = await sut.build(document=Document())
        assert actual is None

    async def test_build_template__with_incomplete_translations(
        self, tmp_path: Path
    ) -> None:
        async with (
            App.new_isolated(
                cache_directory=tmp_path,
                translations=AssetTranslationRepository(
                    StaticAssetRepository(), BinaryFileCache(tmp_path)
                ),
            ) as app,
            app,
            Project.new_isolated(
                app, support_plugins=[IncompleteTranslationWarning]
            ) as project,
        ):
            project.configuration.locales = ["nl"]
            async with project:
                sut = await IncompleteTranslationWarning.new(project)
                actual = await sut.build(document=Document())
        assert actual is not None
