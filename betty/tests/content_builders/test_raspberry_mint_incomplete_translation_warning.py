from pathlib import Path

from babel import Locale

from betty.content_builders.raspberry_mint_incomplete_translation_warning import (
    IncompleteTranslationWarning,
)
from betty.document import Document
from betty.localizer import Localizer
from betty.test_utils.conftest import NewIsolatedProject


class TestIncompleteTranslationWarning:
    async def test_build_template__with_default_locale(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(
                supported_plugins=[IncompleteTranslationWarning]
            ) as project,
            project,
        ):
            sut = await IncompleteTranslationWarning.new(project)
            actual = await sut.build(document=Document())
        assert actual is None

    async def test_build_template__with_missing_translations(
        self, tmp_path: Path, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with new_isolated_project(
            supported_plugins=[IncompleteTranslationWarning]
        ) as project:
            project.locales = ["nl"]
            async with project:
                sut = await IncompleteTranslationWarning.new(project)
                actual = await sut.build(
                    document=Document(localizer=Localizer(Locale("nl")))
                )
        assert actual is not None
        assert "0%" in actual
