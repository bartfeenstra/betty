"""
Provide rendering utilities using `Jinja2 <https://jinja.palletsprojects.com>`_.
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, Self, TypeAlias, cast, final

import aiofiles
from aiofiles import os as aiofiles_os
from jinja2 import (
    Environment as Jinja2Environment,
)
from jinja2 import (
    FileSystemLoader,
    Template,
    pass_context,
    select_autoescape,
)
from jinja2.runtime import Context, DebugUndefined, StrictUndefined
from typing_extensions import override

from betty.date import Date
from betty.html import (
    Breadcrumbs,
    Citer,
    CssProvider,
    JsProvider,
    NavigationLinkProvider,
)
from betty.html.attributes import Attributes
from betty.jinja2.filter import filters
from betty.jinja2.globals import HtmlId, generate_html_id
from betty.jinja2.test import tests
from betty.job import Context as JobContext
from betty.locale.localizable import Localizable, plain
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.model import ENTITY_TYPE_REPOSITORY
from betty.plugin import Plugin, PluginIdToTypeMapping
from betty.project.factory import ProjectDependentFactory
from betty.render import Renderer
from betty.typing import private
from betty.warnings import deprecate

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableMapping, Sequence
    from pathlib import Path

    from betty.assets import AssetRepository
    from betty.machine_name import MachineName
    from betty.model import Entity
    from betty.project import Project
    from betty.project.config import ProjectConfiguration
    from betty.project.extension import Extension


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


class EntityContexts:
    """
    Track the current entity contexts.

    To allow templates to respond to their environment, this class allows
    our templates to set and get one entity per entity type for the current context.

    Use cases include rendering an entity label as plain text if the template is in
    that entity's context, but as a hyperlink if the template is not in the entity's
    context.
    """

    def __init__(
        self,
        *entities: Entity,
        entity_type_id_to_type_mapping: PluginIdToTypeMapping[Entity],
    ) -> None:
        self._entity_type_id_to_type_mapping = entity_type_id_to_type_mapping
        self._contexts: MutableMapping[type[Entity], Entity | None] = defaultdict(
            lambda: None
        )
        for entity in entities:
            self._contexts[entity.type] = entity

    @classmethod
    async def new(cls, *entities: Entity) -> Self:
        """
        Create a new instance.
        """
        return cls(
            *entities,
            entity_type_id_to_type_mapping=await ENTITY_TYPE_REPOSITORY.mapping(),
        )

    def __getitem__(
        self, entity_type_or_type_name: type[Entity] | str
    ) -> Entity | None:
        return self._contexts[
            self._entity_type_id_to_type_mapping[entity_type_or_type_name]
        ]

    def __call__(self, *entities: Entity) -> EntityContexts:
        """
        Create a new context with the given entities.
        """
        updated_contexts = EntityContexts(
            *(entity for entity in self._contexts.values() if entity is not None),
            entity_type_id_to_type_mapping=self._entity_type_id_to_type_mapping,
        )
        for entity in entities:
            updated_contexts._contexts[entity.type] = entity
        return updated_contexts


Globals: TypeAlias = Mapping[str, Any]
Filters: TypeAlias = Mapping[str, Callable[..., Any]]
Tests: TypeAlias = Mapping[str, Callable[..., bool]]
ContextVars: TypeAlias = Mapping[str, Any]


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


class Environment(ProjectDependentFactory, Jinja2Environment):
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
        entity_contexts: EntityContexts,
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
            ],
        )

        self._context_class: type[Context] | None = None
        self._project = project
        self._extensions = extensions
        self._entity_contexts = entity_contexts

        if project.configuration.debug:
            self.add_extension("jinja2.ext.debug")

        self._init_i18n()
        self._init_globals()
        self.filters.update(filters)
        self.tests.update(tests)
        self._init_extensions()

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        extensions = await project.extensions
        return cls(
            project,
            list(extensions.flatten()),
            await project.assets,
            await EntityContexts.new(),
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
        )
        self.policies["ext.i18n.trimmed"] = True

    @override
    @property
    def context_class(self) -> type[Context]:  # type: ignore[override]
        if self._context_class is None:
            jinja2_providers: Sequence[Jinja2Provider & Extension] = [
                extension
                for extension in self._extensions
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
                        parent["citer"] = Citer()
                    if "breadcrumbs" not in parent:
                        parent["breadcrumbs"] = Breadcrumbs()
                    if "_html_id_generator" not in parent:
                        parent["_html_id_generator"] = HtmlId()
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

    async def from_file(self, file_path: Path) -> Template:
        """
        Create a :py:class:`jinja2.Template` out of the given Jinja2 file path.

        This method is intended for rendering individual files once. It **MUST NOT**
        be used for reusable templates.
        """
        async with aiofiles.open(file_path) as f:
            template_source = await f.read()
        template_code = self.compile(
            template_source, filename=str(file_path.expanduser().resolve())
        )
        return self.template_class.from_code(self, template_code, self.globals)

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
            for extension in self._extensions
            if isinstance(extension, CssProvider)
            for path in extension.public_css_paths
        ]
        self.globals["public_js_paths"] = [
            path
            for extension in self._extensions
            if isinstance(extension, JsProvider)
            for path in extension.public_js_paths
        ]
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
        self.globals["entity_contexts"] = self._entity_contexts
        self.globals["localizer"] = DEFAULT_LOCALIZER
        self.globals["generate_html_id"] = generate_html_id
        self.globals["deprecate"] = deprecate
        self.globals["new_attributes"] = Attributes

    def _init_extensions(self) -> None:
        for extension in self._extensions:
            if isinstance(extension, Jinja2Provider):
                self.globals.update(extension.globals)
                self.filters.update(extension.filters)
                self.tests.update(extension.tests)


@final
class Jinja2Renderer(Renderer, ProjectDependentFactory, Plugin):
    """
    Render content as Jinja2 templates.
    """

    def __init__(self, environment: Environment, configuration: ProjectConfiguration):
        self._environment = environment
        self._configuration = configuration

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return "jinja2"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain("Jinja2")

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(await project.jinja2_environment, project.configuration)

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
        data: MutableMapping[str, Any] = {}
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
            data["page_resource"] = f"betty:///{resource}"
        template = await self._environment.from_file(file_path)
        rendered = await template.render_async(data)
        async with aiofiles.open(destination_file_path, "w", encoding="utf-8") as f:
            await f.write(rendered)
        await aiofiles_os.remove(file_path)
        return destination_file_path
