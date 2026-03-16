from collections.abc import Iterable, Mapping
from gettext import NullTranslations
from pathlib import Path
from typing import Any, override

import aiofiles
from aiofiles.os import makedirs

from betty.app import App
from betty.content import ContentDefinition
from betty.document import Document
from betty.job import Context
from betty.locale.localize import Localizer
from betty.plugins.content.template import Template
from betty.project import Project
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestTemplate:
    async def test_build(
        self,
        isolated_app: App,
    ) -> None:
        template_name = "my/first/template.html.j2"
        template_path = Path(*template_name.split("/"))
        template = """
{{ document.localizer.locale }}
{{ document.resource }}
{{ document.context.id }}
"""
        context = Context()
        async with Project.new_isolated(isolated_app) as project, project:
            templates_directory_path = project.assets_directory / "templates"
            await makedirs(templates_directory_path)
            template_file_path = templates_directory_path / template_path
            await makedirs(template_file_path.parent)
            async with aiofiles.open(template_file_path, "w") as f:
                await f.write(template)

            @ContentDefinition("my-first-template", label=DUMMY_LOCALIZABLE)
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

            sut = _Template(jinja=await project.jinja)
            provided_content = await sut.build(
                document=Document(
                    "my-first-page-resource",
                    localizer=Localizer("nl-NL", NullTranslations()),
                    context=context,
                )
            )
            assert provided_content is not None
            assert (
                provided_content.strip()
                == f"nl_NL\nmy-first-page-resource\n{context.id}"
            )
