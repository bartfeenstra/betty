"""
Utilities for testing Jinja2 templates.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Callable, TYPE_CHECKING

import aiofiles
import html5lib
from html5lib.html5parser import ParseError

from betty.app import App
from betty.jinja2 import Environment
from betty.json.schema import ProjectSchema
from betty.project import Project
from betty.project.extension import Extension

if TYPE_CHECKING:
    from betty.locale import Localey
    from jinja2 import Template


class TemplateTestBase:
    """
    A base class for testing Jinja2 templates.
    """

    template_string: str | None = None
    """
    The template to test, as a string.
    
    Exactly one of ``template_string`` or ``template_file`` must be set.
    """

    template_file: str | None = None
    """
    The template to test, as a template path.
    
    Exactly one of ``template_file`` or ``template_string`` must be set.
    """

    extensions = set[type[Extension]]()
    """
    The extensions to enable before rendering the template.
    """

    @asynccontextmanager
    async def _render(
        self,
        *,
        data: dict[str, Any] | None = None,
        template_file: str | None = None,
        template_string: str | None = None,
        locale: Localey | None = None,
    ) -> AsyncIterator[tuple[str, Project]]:
        if self.template_string is not None and self.template_file is not None:
            class_name = self.__class__.__name__
            raise RuntimeError(
                f"{class_name} must define either `{class_name}.template_string` or `{class_name}.template_file`, but not both."
            )

        if template_string is not None and template_file is not None:
            raise RuntimeError(
                "You must define either `template_string` or `template_file`, but not both."
            )
        template_factory: Callable[..., Template]
        if template_string is not None:
            template = template_string
            template_factory = Environment.from_string
        elif template_file is not None:
            template = template_file
            template_factory = Environment.get_template
        elif self.template_string is not None:
            template = self.template_string
            template_factory = Environment.from_string
        elif self.template_file is not None:
            template = self.template_file
            template_factory = Environment.get_template
        else:
            class_name = self.__class__.__name__
            raise RuntimeError(
                f"You must define one of `template_string`, `template_file`, `{class_name}.template_string`, or `{class_name}.template_file`."
            )
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project:
            project.configuration.debug = True
            if data is None:
                data = {}
            if locale is not None:
                data["localizer"] = await app.localizers.get(locale)
            project.configuration.extensions.enable(*self.extensions)
            async with project:
                rendered = await template_factory(
                    project.jinja2_environment, template
                ).render_async(**data)
                yield rendered, project


async def assert_betty_html(project: Project, url_path: str) -> Path:
    """
    Assert that an entity's HTML resource exists and is valid.
    """
    betty_html_file_path = project.configuration.www_directory_path / Path(
        url_path.lstrip("/")
    )
    async with aiofiles.open(betty_html_file_path) as f:
        betty_html = await f.read()
    try:
        html5lib.HTMLParser(strict=True).parse(betty_html)
    except ParseError as e:
        raise ValueError(
            f'HTML parse error "{e}" in:\n{betty_html}'
        ) from None  # pragma: no cover

    return betty_html_file_path


async def assert_betty_json(project: Project, url_path: str) -> Path:
    """
    Assert that an entity's JSON resource exists and is valid.
    """
    import json

    betty_json_file_path = project.configuration.www_directory_path / Path(
        url_path.lstrip("/")
    )
    async with aiofiles.open(betty_json_file_path) as f:
        betty_json = await f.read()
    betty_json_data = json.loads(betty_json)
    schema = await ProjectSchema.new(project)
    schema.validate(betty_json_data)

    return betty_json_file_path
