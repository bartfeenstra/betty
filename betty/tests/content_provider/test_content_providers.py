from gettext import NullTranslations
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import pytest
from aiofiles.os import makedirs
from typing_extensions import override

from betty.ancestry.note import Note
from betty.app import App
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.content_provider.content_providers import (
    Notes,
    Render,
    RenderConfiguration,
    Template,
)
from betty.document import Document
from betty.exception import HumanFacingException
from betty.job import Context as JobContext
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable import LocalizableLike
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.media_type.media_types import HTML, PLAIN_TEXT
from betty.project import Project
from betty.render import RenderDispatcher
from betty.render.plain_text import PlainText
from betty.test_utils.config.factory import ConfigurationDependentSelfFactoryTestBase
from betty.test_utils.content_provider import ContentProviderTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.tests.ancestry.test_has_notes import DummyHasNotes

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestRenderConfiguration:
    def test_content(self) -> None:
        content = DUMMY_LOCALIZABLE
        sut = RenderConfiguration(content)
        assert sut.content is content

    def test_load__without_text(self) -> None:
        dump: Dump = {}
        with pytest.raises(HumanFacingException):
            RenderConfiguration.load(dump)

    def test_load__minimal(self) -> None:
        content = "Hello, world!"
        dump: Dump = {
            "content": content,
        }
        sut = RenderConfiguration.load(dump)
        assert sut.content.localize(DEFAULT_LOCALIZER) == content
        assert sut.media_type == PLAIN_TEXT

    def test_load__with_media_type(self) -> None:
        dump: Dump = {
            "content": "Hello, world!",
            "media_type": "text/html",
        }
        sut = RenderConfiguration.load(dump)
        assert sut.media_type == HTML

    def test_dump__minimal(self) -> None:
        text = "Hello, world!"
        sut = RenderConfiguration(text)
        assert sut.dump() == {
            "content": text,
            "media_type": str(PLAIN_TEXT),
        }

    def test_dump__with_media_type(self) -> None:
        text = "Hello, world!"
        sut = RenderConfiguration(text, HTML)
        assert sut.dump() == {
            "content": text,
            "media_type": str(HTML),
        }


class TestRender(
    ConfigurationDependentSelfFactoryTestBase[RenderConfiguration],
    ContentProviderTestBase,
):
    @override
    @pytest.fixture
    async def sut(self) -> ContentProvider:
        return Render(
            configuration=RenderConfiguration("Hello, world!"),
            renderer=RenderDispatcher(PlainText()),
        )

    @override
    @pytest.fixture
    async def configuration_dependent_self_factory_sut(
        self,
    ) -> type[ConfigurationDependentSelfFactory[RenderConfiguration]]:
        return Render

    @override
    @pytest.fixture
    def configuration_dependent_self_factory_sut_configuration(
        self,
    ) -> RenderConfiguration:
        return RenderConfiguration(DUMMY_LOCALIZABLE)

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
                    {DEFAULT_LOCALE_TAG: "One\nTwo\nThree", "nl": "Een\nTwee\nDrie"}
                ),
                "nl",
            ),
        ],
    )
    async def test_provide(
        self, expected: str, content: LocalizableLike, locale: str
    ) -> None:
        sut = Render(
            configuration=RenderConfiguration(content),
            renderer=RenderDispatcher(PlainText()),
        )
        assert (
            await sut.provide(
                document=Document(localizer=Localizer(locale, NullTranslations()))
            )
            == expected
        )


class TestTemplate:
    async def test_provide(
        self,
        isolated_app: App,
    ) -> None:
        template_name = "content/my-first-template.html.j2"
        template_path = Path(*template_name.split("/"))
        template = """
{{ document.localizer.locale }}
{{ document.resource }}
{{ document.job_context.id }}
"""
        job_context = JobContext()
        async with Project.new_isolated(isolated_app) as project, project:
            templates_directory_path = project.assets_directory_path / "templates"
            await makedirs(templates_directory_path)
            template_file_path = templates_directory_path / template_path
            await makedirs(template_file_path.parent)
            async with aiofiles.open(template_file_path, "w") as f:
                await f.write(template)

            @ContentProviderDefinition("my-first-template", label=DUMMY_LOCALIZABLE)
            class _Jinja2TemplateContentProvider(Template):
                pass

            sut = await _Jinja2TemplateContentProvider.new_for_project(project)
            provided_content = await sut.provide(
                document=Document(
                    "my-first-page-resource",
                    localizer=Localizer("nl-NL", NullTranslations()),
                    job_context=job_context,
                )
            )
            assert provided_content is not None
            assert (
                provided_content.strip()
                == f"nl_NL\nmy-first-page-resource\n{job_context.id}"
            )


class TestNotes(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Notes(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_has_notes_resource(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Notes.new_for_project(project)
            assert await sut.provide(document=Document()) is None

    async def test_provide__without_notes(self, isolated_app: App) -> None:
        has_notes = DummyHasNotes()
        async with Project.new_isolated(isolated_app) as project, project:
            project.ancestry.add(has_notes)
            sut = await Notes.new_for_project(project)
            assert await sut.provide(document=Document(has_notes)) is None

    async def test_provide__with_notes(self, isolated_app: App) -> None:
        note_text = "Hello, world!"
        has_notes = DummyHasNotes(notes=[Note(note_text)])
        async with Project.new_isolated(isolated_app) as project, project:
            project.ancestry.add(has_notes)
            sut = await Notes.new_for_project(project)
            actual = await sut.provide(document=Document(has_notes))
            assert actual is not None
            assert note_text in actual
