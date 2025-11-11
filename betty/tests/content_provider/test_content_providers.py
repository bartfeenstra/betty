import aiofiles
import pytest
from aiofiles.os import makedirs

from betty.ancestry.note import Note
from betty.app import App
from betty.content_provider.content_providers import (
    Jinja2TemplateContentProvider,
    Notes,
    PlainText,
)
from betty.job import Context
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import Plain, ShorthandStaticTranslations
from betty.project import Project
from betty.tests.ancestry.test_has_notes import DummyHasNotes


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


class TestJinja2TemplateContentProvider:
    async def test_provide(
        self,
        temporary_app: App,
    ) -> None:
        template_name = "my-first-template.html.j2"
        template = """
{{ localizer.locale }}
{{ page_resource }}
{{ job_context.id }}
"""
        job_context = Context()
        async with Project.new_temporary(temporary_app) as project, project:
            templates_directory_path = (
                project.configuration.assets_directory_path / "templates"
            )
            await makedirs(templates_directory_path)
            async with aiofiles.open(
                templates_directory_path / template_name, "w"
            ) as f:
                await f.write(template)

            class _Jinja2TemplateContentProvider(Jinja2TemplateContentProvider):
                _template = template_name

            sut = await _Jinja2TemplateContentProvider.new_for_project(project)
            provided_content = await sut.provide(
                locale="nl-NL",
                page_resource="my-first-page-resource",
                job_context=job_context,
            )
            assert provided_content is not None
            assert (
                provided_content.strip()
                == f"nl-NL\nmy-first-page-resource\n{job_context.id}"
            )


class TestNotes:
    async def test_provide__without_has_notes_page_resource(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Notes.new_for_project(project)
            assert await sut.provide(locale=DEFAULT_LOCALE, page_resource=None) is None

    async def test_provide__without_notes(self, temporary_app: App) -> None:
        page_resource = DummyHasNotes()
        async with Project.new_temporary(temporary_app) as project, project:
            project.ancestry.add(page_resource)
            sut = await Notes.new_for_project(project)
            assert (
                await sut.provide(locale=DEFAULT_LOCALE, page_resource=page_resource)
                is None
            )

    async def test_provide__with_notes(self, temporary_app: App) -> None:
        note_text = "Hello, world!"
        page_resource = DummyHasNotes(notes=[Note(Plain(note_text))])
        async with Project.new_temporary(temporary_app) as project, project:
            project.ancestry.add(page_resource)
            sut = await Notes.new_for_project(project)
            actual = await sut.provide(
                locale=DEFAULT_LOCALE, page_resource=page_resource
            )
            assert actual is not None
            assert note_text in actual
