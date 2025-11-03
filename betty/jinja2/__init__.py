"""
Provide rendering utilities using `Jinja2 <https://jinja.palletsprojects.com>`_.
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeAlias, cast, final

from jinja2 import Environment as Jinja2Environment
from jinja2 import FileSystemLoader, pass_context, select_autoescape
from jinja2.runtime import Context, DebugUndefined, StrictUndefined
from typing_extensions import override

from betty import about
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
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.media_type.media_types import JINJA2
from betty.plugin import PluginIdentifier, resolve_id
from betty.project.factory import ProjectDependentFactory
from betty.render import Renderer, RendererDefinition
from betty.typing import private
from betty.warnings import deprecate

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableMapping, Sequence

    from betty.asset import AssetRepository
    from betty.machine_name import MachineName
    from betty.media_type import MediaType
    from betty.model import Entity
    from betty.project import Project
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

    def __init__(self, *entities: Entity) -> None:
        self._contexts: MutableMapping[MachineName, Entity | None] = defaultdict(
            lambda: None
        )
        for entity in entities:
            self._contexts[entity.plugin.id] = entity

    def __getitem__(self, entity_type: PluginIdentifier) -> Entity | None:
        return self._contexts[resolve_id(entity_type)]

    def __call__(self, *entities: Entity) -> EntityContexts:
        """
        Create a new context with the given entities.
        """
        updated_contexts = EntityContexts(
            *(entity for entity in self._contexts.values() if entity is not None)
        )
        for entity in entities:
            updated_contexts._contexts[entity.plugin.id] = entity
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
        self.globals.update(globals)
        self.filters.update(filters)
        self.tests.update(tests)
        self._init_extensions()

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        extensions = list((await project.extensions).flatten())
        return cls(
            project,
            extensions,
            await project.assets,
            EntityContexts(),
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
@RendererDefinition(
    id="jinja2",
)
class Jinja2Renderer(Renderer, ProjectDependentFactory):
    """
    Render content as Jinja2 templates.
    """

    plugin: ClassVar[RendererDefinition]

    def __init__(self, environment: Jinja2Environment):
        self._environment = environment

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(await project.jinja2_environment)

    @override
    @property
    def media_types(self) -> Sequence[MediaType]:
        return [JINJA2]

    @override
    async def render(
        self,
        content: str,
        media_type: MediaType,
        *,
        data: Mapping[str, Any] | None = None,
        job_context: JobContext | None = None,
        localizer: Localizer | None = None,
    ) -> str:
        data = {} if data is None else dict(data)
        if job_context is not None:
            data["job_context"] = job_context
        if localizer is not None:
            data["localizer"] = localizer
        template = self._environment.template_class.from_code(
            self._environment,
            self._environment.compile(content),
            self._environment.globals,
        )
        return await template.render_async(data)
