from gettext import NullTranslations
from pathlib import Path

import aiofiles
import pytest
from aiofiles.os import makedirs

from betty.ancestry.note import Note
from betty.app import App
from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import (
    Notes,
    PlainText,
    Template,
)
from betty.job import Context
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import Plain, ShorthandStaticTranslations
from betty.locale.localizer import Localizer
from betty.project import Project
from betty.resource import new_context
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
        self, expected: str, configuration: ShorthandStaticTranslations, locale: str
    ) -> None:
        sut = await PlainText.new()
        sut.configuration.replace(configuration)
        assert (
            await sut.provide(
                resource=new_context(localizer=Localizer(locale, NullTranslations()))
            )
            == expected
        )


class TestTemplate:
    async def test_provide(
        self,
        temporary_app: App,
    ) -> None:
        template_name = "content/my-first-template.html.j2"
        template_path = Path(*template_name.split("/"))
        template = """
{{ resource.localizer.locale }}
{{ resource.resource }}
{{ resource.job_context.id }}
"""
        job_context = Context()
        async with Project.new_temporary(temporary_app) as project, project:
            templates_directory_path = (
                project.configuration.assets_directory_path / "templates"
            )
            await makedirs(templates_directory_path)
            template_file_path = templates_directory_path / template_path
            await makedirs(template_file_path.parent)
            async with aiofiles.open(template_file_path, "w") as f:
                await f.write(template)

            @ContentProviderDefinition(id="my-first-template", label=Plain(""))
            class _Jinja2TemplateContentProvider(Template):
                pass

            sut = await _Jinja2TemplateContentProvider.new_for_project(project)
            provided_content = await sut.provide(
                resource=new_context(
                    "my-first-page-resource",
                    localizer=Localizer("nl-NL", NullTranslations()),
                    job_context=job_context,
                )
            )
            assert provided_content is not None
            assert (
                provided_content.strip()
                == f"nl-NL\nmy-first-page-resource\n{job_context.id}"
            )


class TestNotes:
    async def test_provide__without_has_notes_resource(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Notes.new_for_project(project)
            assert await sut.provide(resource=new_context()) is None

    async def test_provide__without_notes(self, temporary_app: App) -> None:
        has_notes = DummyHasNotes()
        async with Project.new_temporary(temporary_app) as project, project:
            project.ancestry.add(has_notes)
            sut = await Notes.new_for_project(project)
            assert await sut.provide(resource=new_context(has_notes)) is None

    async def test_provide__with_notes(self, temporary_app: App) -> None:
        note_text = "Hello, world!"
        has_notes = DummyHasNotes(notes=[Note(Plain(note_text))])
        async with Project.new_temporary(temporary_app) as project, project:
            project.ancestry.add(has_notes)
            sut = await Notes.new_for_project(project)
            actual = await sut.provide(resource=new_context(has_notes))
            assert actual is not None
            assert note_text in actual
