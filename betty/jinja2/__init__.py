"""
Provide rendering utilities using `Jinja2 <https://jinja.palletsprojects.com>`_.
"""
from __future__ import annotations

import datetime
from collections import defaultdict
from pathlib import Path
from typing import Callable, Any, cast, \
    Mapping, TypeVar

import aiofiles
from aiofiles import os as aiofiles_os
from jinja2 import Environment as Jinja2Environment, select_autoescape, FileSystemLoader, pass_context, \
    Template as Jinja2Template
from jinja2.runtime import StrictUndefined, Context, DebugUndefined, new_context

from betty import task
from betty.app import App
from betty.html import CssProvider, JsProvider
from betty.jinja2.filter import FILTERS
from betty.jinja2.test import TESTS
from betty.locale import Date, Localizer, \
    DEFAULT_LOCALIZER
from betty.model import Entity, get_entity_type, \
    AncestryEntityId
from betty.model.ancestry import Citation, AnonymousCitation, AnonymousSource
from betty.project import ProjectConfiguration
from betty.render import Renderer
from betty.serde.dump import Dumpable, DictDump, VoidableDump, Void, Dump

T = TypeVar('T')


def context_app(context: Context) -> App:
    """
    Get the current app from the Jinja2 context.
    """
    return cast(Environment, context.environment).app


def context_task_context(context: Context) -> task.Context | None:
    """
    Get the current task context from the Jinja2 context.
    """
    task_context = context.resolve_or_missing('task_context')
    return task_context if isinstance(task_context, task.Context) else None


def context_localizer(context: Context) -> Localizer:
    """
    Get the current localizer from the Jinja2 context.
    """
    localizer = context.resolve_or_missing('localizer')
    if isinstance(localizer, Localizer):
        return localizer
    raise RuntimeError('No `localizer` context variable exists in this Jinja2 template.')


class _Citer:
    def __init__(self):
        self._citations: list[Citation] = []
        self._anonymous_source = AnonymousSource()
        self._anonymous_citations: dict[AncestryEntityId | None, Citation] = {}

    def __iter__(self) -> enumerate[Citation]:
        return enumerate(self._citations, 1)

    def __len__(self) -> int:
        return len(self._citations)

    def cite(self, citation: Citation) -> int:
        if citation.private:
            source_key = None if citation.source is None else citation.source.ancestry_id
            try:
                citation = self._anonymous_citations[source_key]
            except KeyError:
                citation = AnonymousCitation(
                    source=citation.source or self._anonymous_source,
                )
                self._anonymous_citations[source_key] = citation
        if citation not in self._citations:
            self._citations.append(citation)
        return self._citations.index(citation) + 1


class _Breadcrumb(Dumpable):
    def __init__(self, label: str, url: str):
        self._label = label
        self._url = url

    def dump(self) -> DictDump[Dump]:
        return {
            '@type': 'ListItem',
            'name': self._label,
            'item': self._url,
        }


class _Breadcrumbs(Dumpable):
    def __init__(self):
        self._breadcrumbs: list[_Breadcrumb] = []

    def append(self, label: str, url: str) -> None:
        self._breadcrumbs.append(_Breadcrumb(label, url))

    def dump(self) -> VoidableDump:
        if not self._breadcrumbs:
            return Void
        return {
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': [
                {
                    'position': position,
                    **breadcrumb.dump(),
                }
                for position, breadcrumb
                in enumerate(self._breadcrumbs, 1)
            ],
        }


class EntityContexts:
    def __init__(self, *entities: Entity) -> None:
        self._contexts: dict[type[Entity], Entity | None] = defaultdict(lambda: None)
        for entity in entities:
            self._contexts[entity.type] = entity

    def __getitem__(self, entity_type_or_type_name: type[Entity] | str) -> Entity | None:
        if isinstance(entity_type_or_type_name, str):
            entity_type = get_entity_type(entity_type_or_type_name)
        else:
            entity_type = entity_type_or_type_name
        return self._contexts[entity_type]

    def __call__(self, *entities: Entity) -> EntityContexts:
        updated_contexts = EntityContexts()
        for entity in entities:
            updated_contexts._contexts[entity.type] = entity
        return updated_contexts


class Jinja2Provider:
    @property
    def globals(self) -> dict[str, Any]:
        return {}

    @property
    def filters(self) -> dict[str, Callable[..., Any]]:
        return {}

    @property
    def tests(self) -> dict[str, Callable[..., bool]]:
        return {}


class Template(Jinja2Template):
    environment: Environment

    def new_context(
        self,
        vars: dict[str, Any] | None = None,
        shared: bool = False,
        locals: Mapping[str, Any] | None = None,
    ) -> Context:
        return new_context(
            self.environment,
            self.name,
            self.blocks,
            vars,
            shared,
            {
                'citer': _Citer(),
                'breadcrumbs': _Breadcrumbs(),
                **self.globals,
            },
            locals,
        )


class Environment(Jinja2Environment):
    template_class = Template
    globals: dict[str, Any]
    filters: dict[str, Callable[..., Any]]
    tests: dict[str, Callable[..., bool]]

    def __init__(self, app: App):
        template_directory_paths = [str(path / 'templates') for path, _ in app.assets.paths]
        super().__init__(
            loader=FileSystemLoader(template_directory_paths),
            auto_reload=app.project.configuration.debug,
            enable_async=True,
            undefined=DebugUndefined if app.project.configuration.debug else StrictUndefined,
            autoescape=select_autoescape(['html.j2']),
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=[
                'jinja2.ext.do',
                'jinja2.ext.i18n',
            ],
        )

        self.app = app

        if app.project.configuration.debug:
            self.add_extension('jinja2.ext.debug')

        self._init_i18n()
        self._init_globals()
        self.filters.update(FILTERS)
        self.tests.update(TESTS)
        self._init_extensions()

    def _init_i18n(self) -> None:
        self.install_gettext_callables(  # type: ignore[attr-defined]
            gettext=self._gettext,
            ngettext=self._ngettext,
            pgettext=self._pgettext,
            npgettext=self._npgettext,
        )
        self.policies['ext.i18n.trimmed'] = True

    @pass_context
    def _gettext(self, context: Context, message: str) -> str:
        return context_localizer(context).gettext(message)

    @pass_context
    def _ngettext(self, context: Context, message_singular: str, message_plural: str, n: int) -> str:
        return context_localizer(context).ngettext(message_singular, message_plural, n)

    @pass_context
    def _pgettext(self, context: Context, gettext_context: str, message: str) -> str:
        return context_localizer(context).pgettext(gettext_context, message)

    @pass_context
    def _npgettext(self, context: Context, gettext_context: str, message_singular: str, message_plural: str, n: int) -> str:
        return context_localizer(context).npgettext(gettext_context, message_singular, message_plural, n)

    def _init_globals(self) -> None:
        self.globals['app'] = self.app
        today = datetime.date.today()
        self.globals['today'] = Date(today.year, today.month, today.day)
        # Ideally we would use the Dispatcher for this. However, it is asynchronous only.
        self.globals['public_css_paths'] = [
            path
            for extension in self.app.extensions.flatten()
            if isinstance(extension, CssProvider)
            for path in extension.public_css_paths
        ]
        self.globals['public_js_paths'] = [
            path
            for extension in self.app.extensions.flatten()
            if isinstance(extension, JsProvider)
            for path in extension.public_js_paths
        ]
        self.globals['entity_contexts'] = EntityContexts()
        self.globals['localizer'] = DEFAULT_LOCALIZER

    def _init_extensions(self) -> None:
        for extension in self.app.extensions.flatten():
            if isinstance(extension, Jinja2Provider):
                self.globals.update(extension.globals)
                self.filters.update(extension.filters)
                self.tests.update(extension.tests)


Template.environment_class = Environment


class Jinja2Renderer(Renderer):
    def __init__(self, environment: Environment, configuration: ProjectConfiguration):
        self._environment = environment
        self._configuration = configuration

    @property
    def file_extensions(self) -> set[str]:
        return {'.j2'}

    async def render_file(
        self,
        file_path: Path,
        *,
        task_context: task.Context | None = None,
        localizer: Localizer | None = None,
    ) -> Path:
        destination_file_path = file_path.parent / file_path.stem
        data: dict[str, Any] = {}
        if task_context is not None:
            data['task_context'] = task_context
        if localizer is not None:
            data['localizer'] = localizer
        try:
            relative_file_destination_path = destination_file_path.relative_to(self._configuration.www_directory_path)
        except ValueError:
            pass
        else:
            resource = '/'.join(relative_file_destination_path.parts)
            if self._configuration.locales.multilingual:
                resource_parts = resource.lstrip('/').split('/')
                if resource_parts[0] in map(lambda x: x.alias, self._configuration.locales.values()):
                    resource = '/'.join(resource_parts[1:])
            data['page_resource'] = resource
        async with aiofiles.open(file_path) as f:
            template_source = await f.read()
        rendered = await self._environment.from_string(template_source, self._environment.globals).render_async(data)
        async with aiofiles.open(destination_file_path, 'w', encoding='utf-8') as f:
            await f.write(rendered)
        await aiofiles_os.remove(file_path)
        return destination_file_path
