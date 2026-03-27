from pathlib import Path

from betty.asset import StaticAssetRepository
from betty.cache.file import BinaryFileCache
from betty.document import Document
from betty.locale.translation import AssetTranslationRepository
from betty.plugins.content.raspberry_mint_incomplete_translation_warning import (
    IncompleteTranslationWarning,
)
from betty.test_utils.conftest import IsolatedAppFactory, IsolatedProjectFactory


class TestIncompleteTranslationWarning:
    async def test_build_template__with_complete_translations(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            support_plugins=[IncompleteTranslationWarning]
        ) as project:
            sut = await IncompleteTranslationWarning.new(project)
            actual = await sut.build(document=Document())
        assert actual is None

    async def test_build_template__with_incomplete_translations(
        self,
        tmp_path: Path,
        isolated_app_factory: IsolatedAppFactory,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_app_factory(
                translations=AssetTranslationRepository(
                    StaticAssetRepository(), BinaryFileCache(tmp_path)
                ),
            ) as app,
            app,
            isolated_project_factory(
                app=app, locales=["nl"], support_plugins=[IncompleteTranslationWarning]
            ) as project,
        ):
            sut = await IncompleteTranslationWarning.new(project)
            actual = await sut.build(document=Document())
        assert actual is not None
