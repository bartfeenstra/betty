"""
Provide rendering utilities using `Jinja2 <https://jinja.palletsprojects.com>`_.
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from threading import Lock
from typing import Callable, Any, cast, TYPE_CHECKING, TypeAlias, final, Awaitable

import aiofiles
from aiofiles import os as aiofiles_os
from jinja2 import (
    Environment as Jinja2Environment,
    select_autoescape,
    FileSystemLoader,
    pass_context,
)
from jinja2.runtime import StrictUndefined, Context, DebugUndefined
from typing_extensions import override

from betty import model
from betty.asyncio import wait_to_thread
from betty.html import CssProvider, JsProvider
from betty.jinja2.filter import FILTERS
from betty.jinja2.test import TESTS
from betty.job import Context as JobContext
from betty.locale.localizer import Localizer
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.locale.date import Date
from betty.render import Renderer
from betty.serde.dump import Dumpable, DumpMapping, VoidableDump, Dump
from betty.typing import Void

if TYPE_CHECKING:
    from betty.model import Entity
    from betty.project.extension import Extension
    from betty.project import ProjectConfiguration, Project
    from betty.model.ancestry import Citation
    from pathlib import Path
    from collections.abc import MutableMapping, Iterator, Sequence


def context_project(context: Context) -> Project:
    """
    Get the current project from the Jinja2 context.
    """
    return cast(Environment, context.environment).project


def context_job_context(context: Context) -> JobContext | None:
    """
    Get the current job context from the Jinja2 context.
    """
    job_context = context.resolve_or_missing("job_context")
    return job_context if isinstance(job_context, JobContext) else None


def context_localizer(context: Context) -> Localizer:
    """
    Get the current localizer from the Jinja2 context.
    """
    localizer = context.resolve_or_missing("localizer")
    if isinstance(localizer, Localizer):
        return localizer
    raise RuntimeError(
        "No `localizer` context variable exists in this Jinja2 template."
    )


class _Citer:
    __slots__ = "_lock", "_cited"

    def __init__(self):
        self._lock = Lock()
        self._cited: list[Citation] = []

    def __iter__(self) -> enumerate[Citation]:
        return enumerate(self._cited, 1)

    def __len__(self) -> int:
        return len(self._cited)

    def cite(self, citation: Citation) -> int:
        with self._lock:
            if citation not in self._cited:
                self._cited.append(citation)
            return self._cited.index(citation) + 1


class _Breadcrumb(Dumpable):
    def __init__(self, label: str, url: str):
        self._label = label
        self._url = url

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "@type": "ListItem",
            "name": self._label,
            "item": self._url,
        }


class _Breadcrumbs(Dumpable):
    def __init__(self):
        self._breadcrumbs: list[_Breadcrumb] = []

    def append(self, label: str, url: str) -> None:
        self._breadcrumbs.append(_Breadcrumb(label, url))

    @override
    def dump(self) -> VoidableDump:
        if not self._breadcrumbs:
            return Void
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "position": position,
                    **breadcrumb.dump(),
                }
                for position, breadcrumb in enumerate(self._breadcrumbs, 1)
            ],
        }


class EntityContexts:
    """
    Track the current entity contexts.

    To allow templates to respond to their environment, this class allows
    our templates to set and get one entity per entity type for the current context.

    Use cases include rendering an entity label as plain text if the template is in
    that entity's context, but as a hyperlink if the template is not in the entity's
    context.
    """

    def __init__(self, *entities: Entity) -> None:
        self._contexts: dict[type[Entity], Entity | None] = defaultdict(lambda: None)
        for entity in entities:
            self._contexts[entity.type] = entity

    def __getitem__(
        self, entity_type_or_type_name: type[Entity] | str
    ) -> Entity | None:
        if isinstance(entity_type_or_type_name, str):
            entity_type = wait_to_thread(
                model.ENTITY_TYPE_REPOSITORY.get(entity_type_or_type_name)
            )
        else:
            entity_type = entity_type_or_type_name
        return self._contexts[entity_type]

    def __call__(self, *entities: Entity) -> EntityContexts:
        """
        Create a new context with the given entities.
        """
        updated_contexts = EntityContexts()
        for entity in entities:
            updated_contexts._contexts[entity.type] = entity
        return updated_contexts


Globals: TypeAlias = dict[str, Any]
Filters: TypeAlias = dict[str, Callable[..., Any]]
Tests: TypeAlias = dict[str, Callable[..., bool]]
ContextVars: TypeAlias = dict[str, Any]


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

    def new_context_vars(self) -> ContextVars:
        """
        Create new variables for a new :py:class:`jinja2.runtime.Context`.

        Keys are the variable names, and values are variable values.
        """
        return {}


class Environment(Jinja2Environment):
    """
    Betty's Jinja2 environment.
    """

    globals: dict[str, Any]
    filters: dict[str, Callable[..., Any]]
    tests: dict[str, Callable[..., bool | Awaitable[bool]]]  # type: ignore[assignment]

    def __init__(self, project: Project):
        template_directory_paths = [
            str(path / "templates") for path in project.assets.assets_directory_paths
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
            ],
        )

        self._context_class: type[Context] | None = None
        self._project = project

        if project.configuration.debug:
            self.add_extension("jinja2.ext.debug")

        self._init_i18n()
        self._init_globals()
        self.filters.update(FILTERS)
        self.tests.update(TESTS)
        self._init_extensions()

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
        )
        self.policies["ext.i18n.trimmed"] = True

    @override
    @property
    def context_class(self) -> type[Context]:  # type: ignore[override]
        if self._context_class is None:
            jinja2_providers: Sequence[Jinja2Provider & Extension] = [
                extension
                for extension in self.project.extensions.flatten()
                if isinstance(extension, Jinja2Provider)
            ]

            class _Context(Context):
                def __init__(
                    self,
                    environment: Environment,
                    parent: dict[str, Any],
                    name: str | None,
                    blocks: dict[str, Callable[[Context], Iterator[str]]],
                    globals: MutableMapping[str, Any] | None = None,  # noqa A002
                ):
                    if "citer" not in parent:
                        parent["citer"] = _Citer()
                    if "breadcrumbs" not in parent:
                        parent["breadcrumbs"] = _Breadcrumbs()
                    for jinja2_provider in jinja2_providers:
                        for key, value in jinja2_provider.new_context_vars().items():
                            if key not in parent:
                                parent[key] = value
                    super().__init__(
                        environment,
                        parent,
                        name,
                        blocks,
                        globals,
                    )

            self._context_class = _Context

        return self._context_class

    @pass_context
    def _gettext(self, context: Context, message: str) -> str:
        return context_localizer(context).gettext(message)

    @pass_context
    def _ngettext(
        self, context: Context, message_singular: str, message_plural: str, n: int
    ) -> str:
        return context_localizer(context).ngettext(message_singular, message_plural, n)

    @pass_context
    def _pgettext(self, context: Context, gettext_context: str, message: str) -> str:
        return context_localizer(context).pgettext(gettext_context, message)

    @pass_context
    def _npgettext(
        self,
        context: Context,
        gettext_context: str,
        message_singular: str,
        message_plural: str,
        n: int,
    ) -> str:
        return context_localizer(context).npgettext(
            gettext_context, message_singular, message_plural, n
        )

    def _init_globals(self) -> None:
        self.globals["app"] = self.project.app
        self.globals["project"] = self.project
        today = datetime.date.today()
        self.globals["today"] = Date(today.year, today.month, today.day)
        # Ideally we would use the Dispatcher for this. However, it is asynchronous only.
        self.globals["public_css_paths"] = [
            path
            for extension in self.project.extensions.flatten()
            if isinstance(extension, CssProvider)
            for path in extension.public_css_paths
        ]
        self.globals["public_js_paths"] = [
            path
            for extension in self.project.extensions.flatten()
            if isinstance(extension, JsProvider)
            for path in extension.public_js_paths
        ]
        self.globals["entity_contexts"] = EntityContexts()
        self.globals["localizer"] = DEFAULT_LOCALIZER

    def _init_extensions(self) -> None:
        for extension in self.project.extensions.flatten():
            if isinstance(extension, Jinja2Provider):
                self.globals.update(extension.globals)
                self.filters.update(extension.filters)
                self.tests.update(extension.tests)


@final
class Jinja2Renderer(Renderer):
    """
    Render content as Jinja2 templates.
    """

    def __init__(self, environment: Environment, configuration: ProjectConfiguration):
        self._environment = environment
        self._configuration = configuration

    @override
    @property
    def file_extensions(self) -> set[str]:
        return {".j2"}

    @override
    async def render_file(
        self,
        file_path: Path,
        *,
        job_context: JobContext | None = None,
        localizer: Localizer | None = None,
    ) -> Path:
        destination_file_path = file_path.parent / file_path.stem
        data: dict[str, Any] = {}
        if job_context is not None:
            data["job_context"] = job_context
        if localizer is not None:
            data["localizer"] = localizer
        try:
            relative_file_destination_path = destination_file_path.relative_to(
                self._configuration.www_directory_path
            )
        except ValueError:
            pass
        else:
            resource = "/".join(relative_file_destination_path.parts)
            if self._configuration.locales.multilingual:
                resource_parts = resource.lstrip("/").split("/")
                if resource_parts[0] in (
                    x.alias for x in self._configuration.locales.values()
                ):
                    resource = "/".join(resource_parts[1:])
            data["page_resource"] = resource
        async with aiofiles.open(file_path) as f:
            template_source = await f.read()
        rendered = await self._environment.from_string(
            template_source, self._environment.globals
        ).render_async(data)
        async with aiofiles.open(destination_file_path, "w", encoding="utf-8") as f:
            await f.write(rendered)
        await aiofiles_os.remove(file_path)
        return destination_file_path
