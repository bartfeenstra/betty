from gettext import NullTranslations

import pytest

from betty.document import Document
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable import ResolvableLocalizable
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import Localizer
from betty.plugins.content.render import Render, RenderData
from betty.render import RenderDispatcher
from betty.renderers.plain_text import PlainText
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestRenderData(DataTestBase[RenderData]):
    sut_cls = RenderData

    def test_content(self) -> None:
        content = DUMMY_LOCALIZABLE
        sut = RenderData(content)
        assert sut.content is content


class TestRender:
    @pytest.mark.parametrize(
        ("expected", "content", "locale"),
        [
            (
                "<p>One<br>\nTwo<br>\nThree</p>",
                "One\nTwo\nThree",
                DEFAULT_LOCALE,
            ),
            (
                "<p>Een<br>\nTwee<br>\nDrie</p>",
                StaticTranslations(
                    {DEFAULT_LOCALE_TAG: "One\nTwo\nThree", "nl": "Een\nTwee\nDrie"},  # ty:ignore[invalid-argument-type]
                ),
                "nl",
            ),
        ],
    )
    async def test_build(
        self, expected: str, content: ResolvableLocalizable, locale: str
    ) -> None:
        sut = Render(content=content, renderer=RenderDispatcher(PlainText()))
        assert (
            await sut.build(
                document=Document(localizer=Localizer(locale, NullTranslations()))
            )
            == expected
        )
