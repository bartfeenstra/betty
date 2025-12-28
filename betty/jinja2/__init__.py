"""
Provide rendering utilities using `Jinja2 <https://jinja.palletsprojects.com>`_.
"""

from __future__ import annotations

import datetime
from collections.abc import Awaitable, Callable, Mapping, MutableMapping
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, Any, Self, TypeAlias, cast

import aiofiles
from aiofiles.os import makedirs
from jinja2 import Environment as Jinja2Environment
from jinja2 import FileSystemLoader, pass_context, select_autoescape
from jinja2.async_utils import auto_await
from jinja2.ext import Extension as Jinja2Extension
from jinja2.nodes import CallBlock, ContextReference, Node
from jinja2.runtime import Context as Jinja2Context
from jinja2.runtime import DebugUndefined, StrictUndefined
from jinja2.utils import missing
from typing_extensions import override

from betty import about
from betty.cache import CacheItem
from betty.date import Date
from betty.html import CssProvider, JsProvider, NavigationLinkProvider, generate_html_id
from betty.html.attributes import Attributes
from betty.jinja2.filter import filters
from betty.jinja2.test import tests
from betty.media_type import UnsupportedMediaType, match_extension
from betty.media_type.media_types import JINJA2
from betty.project.factory import ProjectDependentSelfFactory
from betty.typing import private
from betty.warnings import deprecate

if TYPE_CHECKING:
    from collections.abc import Sequence

    from jinja2.parser import Parser

    from betty.asset import AssetRepository
    from betty.job import Context as JobContext
    from betty.locale.localize import Localizer
    from betty.project import Project
    from betty.project.extension import Extension
    from betty.resource import Context
    from betty.resource import Context as ResourceContext


CopyFunction: TypeAlias = Callable[[Path, Path], Awaitable[None]]


def context_project(context: Jinja2Context) -> Project:
    """
    Get the current project from the Jinja2 context.
    """
    return cast(Environment, context.environment).project


def context_resource_context(context: Jinja2Context) -> ResourceContext:
    """
    Get the current resource context from the Jinja2 context.
    """
    resource: ResourceContext = context.resolve_or_missing("resource")
    if resource is missing:
        raise RuntimeError(
            "No `resource` context variable exists in this Jinja2 template."
        ) from None
    return resource


def context_job_context(context: Jinja2Context) -> JobContext | None:
    """
    Get the current job context from the Jinja2 context.
    """
    try:
        return context_resource_context(context).job_context
    except (KeyError, RuntimeError):
        return None


def context_localizer(context: Jinja2Context) -> Localizer:
    """
    Get the current localizer from the Jinja2 context.
    """
    try:
        return context_resource_context(context).localizer
    except KeyError:
        raise RuntimeError(
            "No `resource.localizer` context variable exists in this Jinja2 template."
        ) from None


Globals: TypeAlias = Mapping[str, Any]
Filters: TypeAlias = Mapping[str, Callable[..., Any]]
Tests: TypeAlias = Mapping[str, Callable[..., bool]]


class Jinja2Provider:
    """
    Integrate an :py:class:`betty.project.extension.Extension` with the Jinja2 API.
    """

    @property
    def globals(self) -> Globals:
        """
        Jinja2 globals provided by this extension.

        Keys are the globals' names, and values are the globals' values.
        """
        return {}

    @property
    def filters(self) -> Filters:
        """
        Jinja2 filters provided by this extension.

        Keys are filter names, and values are the filters themselves.
        """
        return {}

    @property
    def tests(self) -> Tests:
        """
        Jinja2 tests provided by this extension.

        Keys are test names, and values are the tests themselves.
        """
        return {}


class Environment(ProjectDependentSelfFactory, Jinja2Environment):
    """
    Betty's Jinja2 environment.
    """

    globals: dict[str, Any]
    filters: dict[str, Callable[..., Any]]
    tests: dict[str, Callable[..., bool]]  # type: ignore[assignment]

    @private
    def __init__(
        self,
        project: Project,
        extensions: Sequence[Extension],
        assets: AssetRepository,
        globals: Mapping[str, Any],  # noqa A002
        filters: Mapping[str, Callable[..., Any]],
        tests: Mapping[str, Callable[..., bool]],
    ):
        template_directory_paths = [
            str(path / "templates") for path in assets.assets_directory_paths
        ]
        super().__init__(
            loader=FileSystemLoader(template_directory_paths),
            auto_reload=project.configuration.debug,
            enable_async=True,
            undefined=(
                DebugUndefined if project.configuration.debug else StrictUndefined
            ),
            autoescape=select_autoescape(["html.j2"]),
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=[
                "jinja2.ext.do",
                "jinja2.ext.i18n",
                _CacheTagExtension,
            ],
        )

        self._project = project
        self._extensions = extensions

        if project.configuration.debug:
            self.add_extension("jinja2.ext.debug")

        self._init_i18n()
        self._init_globals()
        self.globals.update(globals)
        self.filters.update(filters)
        self.tests.update(tests)
        self._init_extensions()

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        extensions = list((await project.extensions).flatten())
        return cls(
            project,
            extensions,
            await project.assets,
            {
                # Ideally we would use the Dispatcher for this. However, it is asynchronous only.
                "public_css_paths": [
                    path
                    for extension in extensions
                    if isinstance(extension, CssProvider)
                    for path in await extension.get_public_css_paths()
                ],
                "public_js_paths": [
                    path
                    for extension in extensions
                    if isinstance(extension, JsProvider)
                    for path in await extension.get_public_js_paths()
                ],
            },
            await filters(),
            await tests(),
        )

    @property
    def project(self) -> Project:
        """
        The current project.
        """
        return self._project

    def _init_i18n(self) -> None:
        self.install_gettext_callables(  # type: ignore[attr-defined]
            gettext=self._gettext,
            ngettext=self._ngettext,
            pgettext=self._pgettext,
            npgettext=self._npgettext,
            newstyle=True,
        )
        self.policies["ext.i18n.trimmed"] = True

    @pass_context
    def _gettext(self, context: Jinja2Context, message: str) -> str:
        return context_localizer(context).gettext(message)

    @pass_context
    def _ngettext(
        self, context: Jinja2Context, message_singular: str, message_plural: str, n: int
    ) -> str:
        return context_localizer(context).ngettext(message_singular, message_plural, n)

    @pass_context
    def _pgettext(
        self, context: Jinja2Context, gettext_context: str, message: str
    ) -> str:
        return context_localizer(context).pgettext(gettext_context, message)

    @pass_context
    def _npgettext(
        self,
        context: Jinja2Context,
        gettext_context: str,
        message_singular: str,
        message_plural: str,
        n: int,
    ) -> str:
        return context_localizer(context).npgettext(
            gettext_context, message_singular, message_plural, n
        )

    def _init_globals(self) -> None:
        self.globals["about_version_major"] = about.VERSION_MAJOR_LABEL
        self.globals["app"] = self.project.app
        self.globals["project"] = self.project
        today = datetime.date.today()
        self.globals["today"] = Date(today.year, today.month, today.day)
        self.globals["primary_navigation_links"] = [
            link
            for extension in self._extensions
            if isinstance(extension, NavigationLinkProvider)
            for link in extension.primary_navigation_links()
        ]
        self.globals["secondary_navigation_links"] = [
            link
            for extension in self._extensions
            if isinstance(extension, NavigationLinkProvider)
            for link in extension.secondary_navigation_links()
        ]
        self.globals["generate_html_id"] = generate_html_id
        self.globals["deprecate"] = deprecate
        self.globals["new_attributes"] = Attributes
        self.globals["copy_resource_context"] = self._copy_resource_context

    def _init_extensions(self) -> None:
        for extension in self._extensions:
            if isinstance(extension, Jinja2Provider):
                self.globals.update(extension.globals)
                self.filters.update(extension.filters)
                self.tests.update(extension.tests)

    @pass_context
    def _copy_resource_context(
        self,
        context: Jinja2Context,
        **vars: Any,  # noqa A002
    ) -> ResourceContext:
        return context_resource_context(context).copy(**vars)

    def make_copy_function(
        self,
        *,
        resource: Context,
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

            copy_resource_url = resource.resource_url

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
                        resource_part.startswith(".")
                        for resource_part in resource_parts
                    ):
                        if is_localized_and_multilingual:
                            resource_parts = resource_parts[1:]
                        copy_resource_url = f"betty:///{'/'.join(resource_parts)}"
            async with aiofiles.open(source_path) as f:
                content = await f.read()

            template = self.from_string(content)
            copy_resource = resource.copy(
                resource=destination_path, resource_url=copy_resource_url
            )
            rendered_content = await template.render_async(resource=copy_resource)
            async with aiofiles.open(destination_path, "w") as f:
                await f.write(rendered_content)

        return _copy_function


_CacheExtensionMap: TypeAlias = MutableMapping[str, str]


class _CacheTagExtension(Jinja2Extension):
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
        self, cache_key: str, context: Jinja2Context, caller: Callable[[], str]
    ) -> str:
        job_context = context_job_context(context)
        if job_context is None:
            return await auto_await(caller())
        async with job_context.cache.getset(f"jinja2_cache_tag:{cache_key}") as result:
            if isinstance(result, CacheItem):
                return cast(str, await result.value())
            rendered = await auto_await(caller())
            await result(rendered)
            return rendered
