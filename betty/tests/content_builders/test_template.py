from asyncio import to_thread
from collections.abc import Iterable, Mapping
from gettext import NullTranslations
from pathlib import Path
from typing import Any, override

from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template
from betty.document import Document
from betty.file import write
from betty.job import Context
from betty.locale.localize import Localizer
from betty.project import Project


class TestTemplate:
    async def test_build(self, isolated_project: Project) -> None:
        template_name = "my/first/template.html.j2"
        template_path = Path(*template_name.split("/"))
        template = """
{{ document.localizer.locale }}
{{ document.resource }}
{{ document.context.id }}
"""
        context = Context()
        templates_directory = isolated_project.asset_directory / "templates"
        await to_thread(templates_directory.mkdir, exist_ok=True, parents=True)
        template_file = templates_directory / template_path
        await to_thread(template_file.parent.mkdir, exist_ok=True, parents=True)
        await write(template_file, template)

        @ContentBuilderDefinition("my-first-template", label="-")
        class _Template(Template):
            @override
            async def build_template(
                self, document: Document
            ) -> (
                str
                | Iterable[str]
                | tuple[str | Iterable[str], Mapping[str, Any]]
                | None
            ):
                return template_name

        sut = _Template(jinja=await isolated_project.jinja)
        provided_content = await sut.build(
            document=Document(
                "my-first-page-resource",
                localizer=Localizer("nl-NL", NullTranslations()),
                context=context,
            )
        )
        assert provided_content is not None
        assert (
            provided_content.strip() == f"nl_NL\nmy-first-page-resource\n{context.id}"
        )
