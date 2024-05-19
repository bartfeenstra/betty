"""Provide test utilities and define all tests for Betty itself."""

from __future__ import annotations

import functools
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, TypeVar, Any, AsyncIterator, Awaitable, ParamSpec

import aiofiles
import html5lib
import pytest
from aiofiles.tempfile import TemporaryDirectory
from html5lib.html5parser import ParseError
from jinja2.environment import Template

from betty import fs
from betty.app import App
from betty.app.extension import Extension
from betty.jinja2 import Environment
from betty.json.schema import Schema
from betty.locale import Localey
from betty.warnings import deprecated

T = TypeVar("T")
P = ParamSpec("P")


@deprecated(
    "The `@patch_cache` decorator is deprecated as of Betty 0.3.3, and will be removed in Bety 0.4.x. Use the `binary_file_cache` fixture instead."
)
def patch_cache(f: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """
    Patch Betty's default global file cache with a temporary directory.
    """

    @functools.wraps(f)
    async def _patch_cache(*args: P.args, **kwargs: P.kwargs) -> T:
        original_cache_directory_path = fs.CACHE_DIRECTORY_PATH
        async with TemporaryDirectory() as cache_directory:
            fs.CACHE_DIRECTORY_PATH = Path(cache_directory)
            try:
                return await f(*args, **kwargs)

            finally:
                fs.CACHE_DIRECTORY_PATH = original_cache_directory_path

    return _patch_cache


class TemplateTester:
    def __init__(
        self,
        app: App,
        template_string: str | None = None,
        template_file: str | None = None,
        extensions: set[type[Extension]] | None = None,
    ):
        self.app = app
        self._template_string = template_string
        self._template_file = template_file
        self._extensions = extensions

    @asynccontextmanager
    async def render(
        self,
        *,
        data: dict[str, Any] | None = None,
        template_file: str | None = None,
        template_string: str | None = None,
        locale: Localey | None = None,
    ) -> AsyncIterator[str]:
        if self._template_string is not None and self._template_file is not None:
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
        elif self._template_string is not None:
            template = self._template_string
            template_factory = Environment.from_string
        elif self._template_file is not None:
            template = self._template_file
            template_factory = Environment.get_template
        else:
            class_name = self.__class__.__name__
            raise RuntimeError(
                f"You must define one of `template_string`, `template_file`, `{class_name}.template_string`, or `{class_name}.template_file`."
            )
        self.app.project.configuration.debug = True
        if data is None:
            data = {}
        if locale is not None:
            data["localizer"] = await self.app.localizers.get(locale)
        rendered = await template_factory(
            self.app.jinja2_environment, template
        ).render_async(**data)
        yield rendered


@pytest.fixture
def template_tester(new_temporary_app: App) -> TemplateTester:
    return TemplateTester(new_temporary_app)


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
        raise ValueError(f'HTML parse error "{e}" in:\n{betty_html}')

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
