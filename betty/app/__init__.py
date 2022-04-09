from __future__ import annotations

import weakref
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import AsyncExitStack, contextmanager
from gettext import NullTranslations
from typing import List, Type, TYPE_CHECKING, Set

from reactives.factory.type import ReactiveInstance

from betty.app.extension import ListExtensions, Extension, Extensions, build_extension_type_graph, \
    CyclicDependencyError, ExtensionDispatcher
from betty.asyncio import sync
from betty.environment import Environment
from betty.model import Entity, EntityTypeProvider
from betty.model.event_type import EventTypeProvider, Birth, Baptism, Adoption, Death, Funeral, Cremation, Burial, Will, \
    Engagement, Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, Emigration, \
    Occupation, Retirement, Correspondence, Confirmation
from betty.project import Project

if TYPE_CHECKING:
    from betty.url import StaticUrlGenerator, ContentNegotiationUrlGenerator

try:
    from graphlib import TopologicalSorter, CycleError
except ImportError:
    from graphlib_backport import TopologicalSorter

import aiohttp
from jinja2 import Environment as Jinja2Environment
from reactives import reactive

from betty.concurrent import ExceptionRaisingAwaitableExecutor
from betty.dispatch import Dispatcher
from betty.lock import Locks
from betty.render import Renderer, SequentialRenderer

from betty.model.ancestry import Citation, Event, File, Person, PersonName, Presence, Place, Enclosure, \
    Source, Note, EventType
from betty.config import Configurable
from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH
from betty.locale import Translations, negotiate_locale, TranslationsRepository


@reactive
class _AppExtensions(ListExtensions):
    def __init__(self):
        super().__init__([])

    def _update(self, extensions: List[List[Extension]]) -> None:
        self._extensions = extensions
        self.react.trigger()


@reactive
class App(Environment, ReactiveInstance):
    def __init__(self, *args, **kwargs):
        from betty.url import AppUrlGenerator, StaticPathUrlGenerator

        super().__init__(*args, **kwargs)

        self._active = False
        self._extensions = None
        self._project = Project()
        self._assets = FileSystem()
        self._dispatcher = None
        self._entity_types = None
        self._event_types = None
        self._url_generator = AppUrlGenerator(self)
        self._static_url_generator = StaticPathUrlGenerator(self.project.configuration)
        self._debug = None
        self._locale = None
        self._translations = TranslationsRepository(self.assets)
        self._default_translations = None
        self._activation_exit_stack = AsyncExitStack()
        self._jinja2_environment = None
        self._renderer = None
        self._executor = None
        self._locks = Locks()
        self._http_client = None

    def wait(self) -> None:
        self._wait_for_threads()

    def _wait_for_threads(self) -> None:
        if self._executor:
            self._executor.wait()

    def _assert_active(self) -> None:
        if not self._active:
            raise RuntimeError('This application is not yet active.')

    def _assert_deactive(self) -> None:
        if self._active:
            raise RuntimeError('This application is still active.')

    @contextmanager
    def activate_locale(self, requested_locale: str) -> None:
        """
        Temporarily change this application's locale and the global gettext translations.
        """
        self._assert_active()

        negotiated_locale = negotiate_locale(
            requested_locale,
            [
                locale_configuration.locale
                for locale_configuration
                in self.project.configuration.locales
            ],
        )

        if negotiated_locale is None:
            raise ValueError(f'Locale "{requested_locale}" is not enabled.')

        previous_locale = self._locale
        if negotiated_locale == previous_locale:
            yield
            return
        self._wait_for_threads()

        self._locale = negotiated_locale
        with self.translations[negotiated_locale]:
            self.react['locale'].react.trigger()
            yield
            self._wait_for_threads()

        self._locale = previous_locale
        self.react['locale'].react.trigger()

    async def activate(self) -> None:
        self._assert_deactive()
        self._active = True

        self._wait_for_threads()

        try:
            # Enable the gettext API by entering a dummy translations context.
            self._activation_exit_stack.enter_context(Translations(NullTranslations()))
            # Then enter the final locale context (doing so may recursively require the gettext API).
            self._activation_exit_stack.enter_context(self.activate_locale(self.locale))
            for extension in self.extensions.flatten():
                await extension.activate()
                self._activation_exit_stack.push_async_callback(extension.deactivate)
        except BaseException:
            await self.deactivate()
            raise

    async def deactivate(self) -> None:
        self._assert_active()
        self._active = False

        self._wait_for_threads()

        await self._activation_exit_stack.aclose()

    async def __aenter__(self) -> App:
        await self.activate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.deactivate()

    @property
    def project(self) -> Project:
        return self._project

    @reactive
    @property
    def debug(self) -> bool:
        if self._debug is not None:
            return self._debug
        return self.project.configuration.debug

    @reactive
    @property
    def locale(self) -> str:
        if self._locale is not None:
            return self._locale
        return self.project.configuration.locales.default_locale.locale

    @property
    def extensions(self) -> Extensions:
        if self._extensions is None:
            self._extensions = _AppExtensions()
            self._update_extensions()
            self.project.configuration.extensions.react(self._update_extensions)

        return self._extensions

    def _update_extensions(self) -> None:
        extension_types_enabled_in_configuration = set()
        for app_extension_configuration in self.project.configuration.extensions:
            if app_extension_configuration.enabled:
                app_extension_configuration.extension_type.requires().assert_met()
                extension_types_enabled_in_configuration.add(app_extension_configuration.extension_type)

        extension_types_sorter = TopologicalSorter(
            build_extension_type_graph(extension_types_enabled_in_configuration)
        )
        try:
            extension_types_sorter.prepare()
        except CycleError:
            raise CyclicDependencyError([app_extension_configuration.extension_type for app_extension_configuration in self.project.configuration.extensions])

        extensions = []
        while extension_types_sorter.is_active():
            extension_types_batch = extension_types_sorter.get_ready()
            extensions_batch = []
            for extension_type in extension_types_batch:
                if issubclass(extension_type, Configurable):
                    if extension_type not in extension_types_enabled_in_configuration or self.project.configuration.extensions[extension_type].extension_configuration is None:
                        configuration = extension_type.default()
                    else:
                        configuration = self.project.configuration.extensions[extension_type].extension_configuration
                    extension = extension_type(self, configuration)
                else:
                    extension = extension_type(self)
                extensions_batch.append(extension)
                extension_types_sorter.done(extension_type)
            extensions.append(extensions_batch)
        self._extensions._update(extensions)

    @reactive
    @property
    def assets(self) -> FileSystem:
        if len(self._assets) == 0:
            self._build_assets()

        return self._assets

    @assets.deleter
    def assets(self) -> None:
        self._assets.clear()
        # Proactively rebuild the assets, so the assets file system can be reused.
        self._build_assets()

    def _build_assets(self) -> None:
        self._assets.prepend(ASSETS_DIRECTORY_PATH, 'utf-8')
        for extension in self.extensions.flatten():
            if extension.assets_directory_path() is not None:
                self._assets.prepend(extension.assets_directory_path(), 'utf-8')
        if self.project.configuration.assets_directory_path:
            self._assets.prepend(self.project.configuration.assets_directory_path)

    @property
    def dispatcher(self) -> Dispatcher:
        if self._dispatcher is None:
            self._dispatcher = ExtensionDispatcher(self.extensions)

        return self._dispatcher

    @property
    def url_generator(self) -> ContentNegotiationUrlGenerator:
        return self._url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        return self._static_url_generator

    @property
    def translations(self) -> TranslationsRepository:
        return self._translations

    @reactive
    @property
    def jinja2_environment(self) -> Jinja2Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import Environment
            self._jinja2_environment = Environment(self)

        return self._jinja2_environment

    @jinja2_environment.deleter
    def jinja2_environment(self) -> None:
        self._jinja2_environment = None

    @reactive
    @property
    def renderer(self) -> Renderer:
        if not self._renderer:
            from betty.jinja2 import Jinja2Renderer

            self._renderer = SequentialRenderer([
                Jinja2Renderer(self.jinja2_environment, self.project.configuration),
            ])

        return self._renderer

    @renderer.deleter
    def renderer(self) -> None:
        self._renderer = None

    @property
    def executor(self) -> Executor:
        if self._executor is None:
            self._executor = ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor())
        return self._executor

    @property
    def locks(self) -> Locks:
        return self._locks

    @property
    def http_client(self) -> aiohttp.ClientSession:
        if not self._http_client:
            self._http_client = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))
            weakref.finalize(self, sync(self._http_client.close))
        return self._http_client

    @reactive
    @property
    @sync
    async def entity_types(self) -> Set[Type[Entity]]:
        if self._entity_types is None:
            self._entity_types = set(await self.dispatcher.dispatch(EntityTypeProvider)()) | {
                Citation,
                Enclosure,
                Event,
                File,
                Note,
                Person,
                PersonName,
                Presence,
                Place,
                Source,
            }
        return self._entity_types

    @reactive
    @property
    @sync
    async def event_types(self) -> Set[Type[EventType]]:
        if self._event_types is None:
            self._event_types = set(await self.dispatcher.dispatch(EventTypeProvider)()) | {
                Birth,
                Baptism,
                Adoption,
                Death,
                Funeral,
                Cremation,
                Burial,
                Will,
                Engagement,
                Marriage,
                MarriageAnnouncement,
                Divorce,
                DivorceAnnouncement,
                Residence,
                Immigration,
                Emigration,
                Occupation,
                Retirement,
                Correspondence,
                Confirmation,
            }
        return self._event_types

    @entity_types.deleter
    def entity_types(self) -> None:
        self._entity_types = None
