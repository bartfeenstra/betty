"""
Utilities for testing Jinja2 templates.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, TYPE_CHECKING, AsyncContextManager

import aiofiles
import html5lib
from html5lib.html5parser import ParseError

from betty.app import App
from betty.jinja2 import Environment
from betty.json.schema import Ref, AllOf
from betty.project import Project, ProjectSchema
from betty.project.extension import Extension

if TYPE_CHECKING:
    from jinja2 import Template
    from collections.abc import MutableMapping, Callable, AsyncIterator
    from betty.locale import Localey


@asynccontextmanager
async def _assert_template(
    template_factory: Callable[[Environment, str], Template],
    template: str,
    *,
    data: MutableMapping[str, Any] | None = None,
    locale: Localey | None = None,
    autoescape: bool | None = None,
    extensions: set[type[Extension]] | None = None,
) -> AsyncIterator[tuple[str, Project]]:
    async with (
        App.new_temporary() as app,
        app,
        Project.new_temporary(app) as project,
    ):
        project.configuration.debug = True
        if data is None:
            data = {}
        if locale is not None:
            data["localizer"] = await app.localizers.get(locale)
        if extensions is not None:
            project.configuration.extensions.enable(*extensions)
        async with project:
            jinja2_environment = await project.jinja2_environment
            if autoescape is not None:
                jinja2_environment.autoescape = autoescape
            rendered = await template_factory(
                jinja2_environment, template
            ).render_async(**data)
            yield rendered, project


def assert_template_string(
    template: str,
    *,
    data: MutableMapping[str, Any] | None = None,
    locale: Localey | None = None,
    autoescape: bool | None = None,
    extensions: set[type[Extension]] | None = None,
) -> AsyncContextManager[tuple[str, Project]]:
    """
    Assert that a template string can be rendered.
    """
    return _assert_template(
        Environment.from_string,
        template,
        data=data,
        locale=locale,
        autoescape=autoescape,
        extensions=extensions,
    )


def assert_template_file(
    template: str,
    *,
    data: MutableMapping[str, Any] | None = None,
    locale: Localey | None = None,
    autoescape: bool | None = None,
    extensions: set[type[Extension]] | None = None,
) -> AsyncContextManager[tuple[str, Project]]:
    """
    Assert that a template file can be rendered.
    """
    return _assert_template(
        Environment.get_template,
        template,
        data=data,
        locale=locale,
        autoescape=autoescape,
        extensions=extensions,
    )


class _TemplateTestBase:
    extensions = set[type[Extension]]()
    """
    The extensions to enable before rendering the template.
    """


class TemplateStringTestBase(_TemplateTestBase):
    """
    A base class for testing Jinja2 template strings.
    """

    def assert_template_string(
        self,
        template: str,
        *,
        data: MutableMapping[str, Any] | None = None,
        locale: Localey | None = None,
        autoescape: bool | None = None,
    ) -> AsyncContextManager[tuple[str, Project]]:
        """
        Assert that a template string can be rendered.
        """
        return assert_template_string(
            template,
            data=data,
            locale=locale,
            autoescape=autoescape,
            extensions=self.extensions,
        )


class TemplateFileTestBase(_TemplateTestBase):
    """
    A base class for testing Jinja2 template files.
    """

    template: str

    def assert_template_file(
        self,
        *,
        data: MutableMapping[str, Any] | None = None,
        locale: Localey | None = None,
        autoescape: bool | None = None,
    ) -> AsyncContextManager[tuple[str, Project]]:
        """
        Assert that a template file can be rendered.
        """
        return assert_template_file(
            self.template,
            data=data,
            locale=locale,
            autoescape=autoescape,
            extensions=self.extensions,
        )


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


async def assert_betty_json(project: Project, url_path: str, def_name: str) -> Path:
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

    project_schema = await ProjectSchema.new_for_project(project)
    # Somehow $ref cannot be top-level in our case, so wrap it.
    schema = AllOf(Ref(def_name))
    project_schema.embed(schema)

    schema.validate(betty_json_data)

    return betty_json_file_path
