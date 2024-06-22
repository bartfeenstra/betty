"""Provide test utilities and define all tests for Betty itself."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import (
    Callable,
    Any,
    AsyncIterator,
    TYPE_CHECKING,
)

import aiofiles
import html5lib
from html5lib.html5parser import ParseError

from betty.app import App
from betty.app.extension import Extension
from betty.jinja2 import Environment
from betty.json.schema import Schema

if TYPE_CHECKING:
    from betty.locale import Localey
    from jinja2.environment import Template


class TemplateTestCase:
    template_string: str | None = None
    template_file: str | None = None
    extensions = set[type[Extension]]()

    @asynccontextmanager
    async def _render(
        self,
        *,
        data: dict[str, Any] | None = None,
        template_file: str | None = None,
        template_string: str | None = None,
        locale: Localey | None = None,
    ) -> AsyncIterator[tuple[str, App]]:
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
        async with App.new_temporary() as app:
            app.project.configuration.debug = True
            app.project.configuration.extensions.enable(*self.extensions)
            async with app:
                if data is None:
                    data = {}
                if locale is not None:
                    data["localizer"] = await app.localizers.get(locale)
                rendered = await template_factory(
                    app.jinja2_environment, template
                ).render_async(**data)
                yield rendered, app


async def assert_betty_html(
    app: App,
    url_path: str,
    *,
    check_links: bool = False,
) -> Path:
    """
    Assert that an entity's HTML resource exists and is valid.
    """
    betty_html_file_path = app.project.configuration.www_directory_path / Path(
        url_path.lstrip("/")
    )
    async with aiofiles.open(betty_html_file_path) as f:
        betty_html = await f.read()
    try:
        html5lib.HTMLParser(strict=True).parse(betty_html)
    except ParseError as e:
        raise ValueError(f'HTML parse error "{e}" in:\n{betty_html}') from None

    return betty_html_file_path


async def assert_betty_json(
    app: App,
    url_path: str,
    schema_definition: str | None = None,
) -> Path:
    """
    Assert that an entity's JSON resource exists and is valid.
    """
    import json

    betty_json_file_path = app.project.configuration.www_directory_path / Path(
        url_path.lstrip("/")
    )
    async with aiofiles.open(betty_json_file_path) as f:
        betty_json = await f.read()
    betty_json_data = json.loads(betty_json)
    if schema_definition:
        schema = Schema(app)
        await schema.validate(betty_json_data)

    return betty_json_file_path
