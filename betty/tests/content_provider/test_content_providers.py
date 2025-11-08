import pytest

from betty.app import App
from betty.content_provider.content_providers import PlainText
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import ShorthandStaticTranslations
from betty.project import Project


class TestPlainText:
    @pytest.mark.parametrize(
        ("expected", "configuration", "locale"),
        [
            ("<p>One<br>\nTwo<br>\nThree</p>", "One\nTwo\nThree", DEFAULT_LOCALE),
            (
                "<p>Een<br>\nTwee<br>\nDrie</p>",
                {DEFAULT_LOCALE: "One\nTwo\nThree", "nl": "Een\nTwee\nDrie"},
                "nl",
            ),
        ],
    )
    async def test_provide(
        self,
        expected: str,
        configuration: ShorthandStaticTranslations,
        locale: str,
        temporary_app: App,
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await PlainText.new_for_project(project)
            sut.configuration.replace(configuration)
            assert await sut.provide(locale=locale, page_resource=None) == expected
