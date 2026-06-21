from pathlib import Path

from betty.asset import StaticAssetRepository
from betty.caches.file import BinaryFileCache
from betty.content_builders.raspberry_mint_incomplete_translation_warning import (
    IncompleteTranslationWarning,
)
from betty.document import Document
from betty.gettext import AssetTranslationRepository
from betty.test_utils.conftest import IsolatedAppFactory, IsolatedProjectFactory


class TestIncompleteTranslationWarning:
    async def test_build_template__with_complete_translations(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            supported_plugins=[IncompleteTranslationWarning]
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
            isolated_project_factory(
                app=app,
                locales=["nl"],
                supported_plugins=[IncompleteTranslationWarning],
            ) as project,
        ):
            sut = await IncompleteTranslationWarning.new(project)
            actual = await sut.build(document=Document())
        assert actual is not None
