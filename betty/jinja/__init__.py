"""
Provide rendering utilities using `Jinja2 <https://jinja.palletsprojects.com>`_.
"""

from __future__ import annotations

import datetime
from asyncio import gather
from collections.abc import Awaitable, Callable
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, cast, override

import aiofiles
from aiofiles.os import makedirs
from jinja2 import Environment, FileSystemLoader, pass_context, select_autoescape
from jinja2.async_utils import auto_await
from jinja2.ext import Extension
from jinja2.nodes import CallBlock, ContextReference, Node
from jinja2.runtime import Context as JinjaContext
from jinja2.runtime import DebugUndefined, StrictUndefined
from jinja2.utils import missing

from betty import about
from betty.cache import CacheItem
from betty.date import Date
from betty.html import generate_html_id
from betty.html.attributes import Attributes
from betty.html.css import CssResourceDefinition
from betty.html.js import JsResourceDefinition
from betty.jinja.filter import JinjaFilterDefinition
from betty.jinja.test import JinjaTestDefinition
from betty.link import LinkDefinition
from betty.media_type import UnsupportedMediaType, match_extension
from betty.media_type.media_types import JINJA2
from betty.string import kebab_case_to_snake_case
from betty.warnings import deprecate

if TYPE_CHECKING:
    from jinja2.parser import Parser

    from betty.document import Document
    from betty.project import Project


type CopyFunction = Callable[[Path, Path], Awaitable[None]]


def context_document(context: JinjaContext) -> Document:
    """
    Get the current document from the Jinja2 context.
    """
    document: Document = context.resolve_or_missing("document")
    if document is missing:
        raise RuntimeError(
            "No `document` context variable exists in this Jinja2 template."
        ) from None
    return document


async def new_environment(project: Project, /) -> Environment:
    """
    Create a new environment.
    """
    assets, extensions, service_plugins = await gather(
        project.assets, project.extensions, project.service_plugins
    )
    template_directory_paths = [str(path / "templates") for path in assets.directories]
    links = [link.plugin() for link in service_plugins[LinkDefinition]]
    today = datetime.date.today()
    environment = Environment(
        loader=FileSystemLoader(template_directory_paths),
        auto_reload=project.debug,
        enable_async=True,
        undefined=(DebugUndefined if project.debug else StrictUndefined),
        autoescape=select_autoescape(["html.j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=[
            "jinja2.ext.do",
            "jinja2.ext.i18n",
            _CacheTagExtension,
        ],
    )
    if project.debug:
        environment.add_extension("jinja2.ext.debug")
    environment.install_gettext_callables(  # ty:ignore[unresolved-attribute]
        gettext=_gettext,
        ngettext=_ngettext,
        pgettext=_pgettext,
        npgettext=_npgettext,
        newstyle=True,
    )
    environment.policies["ext.i18n.trimmed"] = True

    environment.globals.update(
        {
            "about_version_major": about.VERSION_MAJOR_LABEL,
            "app": project.upstream,
            "deprecate": deprecate,
            "generate_html_id": generate_html_id,
            "new_attributes": Attributes,
            "project": project,
            "primary_navigation_links": [link.link for link in links if link.primary],
            "public_css_paths": [
                resource.plugin().resource
                for resource in service_plugins[CssResourceDefinition]
            ],
            "public_js_paths": [
                resource.plugin().resource
                for resource in service_plugins[JsResourceDefinition]
            ],
            "secondary_navigation_links": [
                link.link for link in links if not link.primary
            ],
            "today": Date(today.year, today.month, today.day),
        }
    )  # ty:ignore[no-matching-overload]
    environment.filters.update(
        {
            kebab_case_to_snake_case(filter.plugin().id): filter.__call__
            for filter in (await project.service_plugins)[JinjaFilterDefinition]  # noqa: A001
        }
    )
    environment.tests.update(
        {
            kebab_case_to_snake_case(test.plugin().id): test.__call__
            for test in service_plugins[JinjaTestDefinition]
        }
    )
    return environment


@pass_context
def _gettext(context: JinjaContext, message: str) -> str:
    return context_document(context).localizer.gettext(message)


@pass_context
def _ngettext(
    context: JinjaContext, message_singular: str, message_plural: str, n: int
) -> str:
    return context_document(context).localizer.ngettext(
        message_singular, message_plural, n
    )


@pass_context
def _pgettext(context: JinjaContext, gettext_context: str, message: str) -> str:
    return context_document(context).localizer.pgettext(gettext_context, message)


@pass_context
def _npgettext(
    context: JinjaContext,
    gettext_context: str,
    message_singular: str,
    message_plural: str,
    n: int,
) -> str:
    return context_document(context).localizer.npgettext(
        gettext_context, message_singular, message_plural, n
    )


def make_copy_function(
    environment: Environment,
    *,
    document: Document,
    www_directory_path: Path | None = None,
    is_localized_and_multilingual: bool | None = None,
) -> CopyFunction:
    """
    Make a copy function for this renderer that renders supported files.
    """

    async def _copy_function(source_path: Path, destination_path: Path) -> None:
        await makedirs(destination_path.parent, exist_ok=True)
        try:
            media_type, extension = match_extension(source_path, [JINJA2])
        except UnsupportedMediaType:
            copy2(source_path, destination_path)
            return

        destination_path = destination_path.with_name(
            destination_path.name[: -len(extension)]
        )

        copy_resource_url = document.resource_url

        if www_directory_path:
            try:
                relative_file_destination_path = destination_path.relative_to(
                    www_directory_path
                )
            except ValueError:
                pass
            else:
                resource_parts = relative_file_destination_path.parts
                if not any(
                    resource_part.startswith(".") for resource_part in resource_parts
                ):
                    if is_localized_and_multilingual:
                        resource_parts = resource_parts[1:]
                    copy_resource_url = f"betty:///{'/'.join(resource_parts)}"
        async with aiofiles.open(source_path) as f:
            content = await f.read()

        template = environment.from_string(content)
        copy_document = document.copy(
            resource=destination_path, resource_url=copy_resource_url
        )
        rendered_content = await template.render_async(document=copy_document)
        async with aiofiles.open(destination_path, "w") as f:
            await f.write(rendered_content)

    return _copy_function


class _CacheTagExtension(Extension):
    tags = {"cache"}

    @override
    def parse(self, parser: Parser) -> Node | list[Node]:
        lineno = next(parser.stream).lineno
        cache_key = parser.parse_expression()
        body = parser.parse_statements(("name:endcache",), drop_needle=True)
        return CallBlock(
            self.call_method("_cache", [cache_key, ContextReference()]),
            [],
            [],
            body,
        ).set_lineno(lineno)

    async def _cache(
        self, cache_key: str, context: JinjaContext, caller: Callable[[], str]
    ) -> str:
        try:
            job_context = context_document(context).context
        except RuntimeError:
            job_context = None
        if job_context is None:
            return await auto_await(caller())
        async with job_context.cache.getset(f"jinja2_cache_tag:{cache_key}") as result:
            if isinstance(result, CacheItem):
                return cast(str, await result.value())
            rendered = await auto_await(caller())
            await result(rendered)
            return rendered
