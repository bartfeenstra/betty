from __future__ import annotations

import weakref
import asyncio
from concurrent.futures import Executor, ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import contextmanager, ExitStack, suppress
from gettext import NullTranslations
from pathlib import Path
import os as stdos
from typing import Iterator, List, Optional, Type, TYPE_CHECKING, Set, Callable, Awaitable

import aiohttp
from babel.core import parse_locale
from babel.localedata import locale_identifiers
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property

from betty.app.extension import ListExtensions, Extension, Extensions, build_extension_type_graph, \
    CyclicDependencyError, ExtensionDispatcher, ConfigurableExtension, discover_extension_types
from betty.asyncio import sync
from betty.concurrent import ExceptionRaisingAwaitableExecutor
from betty.config import FileBasedConfiguration, DumpedConfiguration, Configurable, VoidableDumpedConfiguration
from betty.config.load import ConfigurationValidationError, Loader, Field
from betty.dispatch import Dispatcher
from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH, HOME_DIRECTORY_PATH
from betty.locale import negotiate_locale, TranslationsRepository, Translations, rfc_1766_to_bcp_47, bcp_47_to_rfc_1766
from betty.lock import Locks
from betty.model import Entity, EntityTypeProvider
from betty.model.ancestry import Citation, Event, File, Person, PersonName, Presence, Place, Enclosure, \
    Source, Note, EventType
from betty.model.event_type import EventTypeProvider, Birth, Baptism, Adoption, Death, Funeral, Cremation, Burial, Will, \
    Engagement, Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, Emigration, \
    Occupation, Retirement, Correspondence, Confirmation
from betty.project import Project
from betty.render import Renderer, SequentialRenderer

try:
    from graphlib_backport import TopologicalSorter, CycleError
except ModuleNotFoundError:
    from graphlib import TopologicalSorter, CycleError

try:
    from typing_extensions import Self
except ModuleNotFoundError:  # pragma: no cover
    from typing import Self  # type: ignore  # pragma: no cover

if TYPE_CHECKING:
    from betty.builtins import _
    from betty.jinja2 import Environment
    from betty.url import StaticUrlGenerator, ContentNegotiationUrlGenerator

CONFIGURATION_DIRECTORY_PATH = HOME_DIRECTORY_PATH / 'configuration'


class _AppExtensions(ListExtensions):
    def __init__(self):
        super().__init__([])

    def _update(self, extensions: List[List[Extension]]) -> None:
        self._extensions = extensions
        self.react.trigger()


class AppConfiguration(FileBasedConfiguration):
    def __init__(self):
        super().__init__()
        self._locale = None

    @property
    def configuration_file_path(self) -> Path:
        return CONFIGURATION_DIRECTORY_PATH / 'app.json'

    @configuration_file_path.setter
    def configuration_file_path(self, __) -> None:
        pass

    @configuration_file_path.deleter
    def configuration_file_path(self) -> None:
        pass

    @property
    @reactive_property
    def locale(self) -> Optional[str]:
        return self._locale

    @locale.setter
    def locale(self, locale: str) -> None:
        try:
            parse_locale(bcp_47_to_rfc_1766(locale))
        except ValueError:
            raise ConfigurationValidationError(_('{locale} is not a valid IETF BCP 47 language tag.').format(locale=locale))
        self._locale = locale

    def load(self, dumped_configuration: DumpedConfiguration, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'locale': Field(
                False,
                loader.assert_str,  # type: ignore
                lambda x: loader.assert_setattr(self, 'locale', x),
            ),
        })

    def dump(self) -> VoidableDumpedConfiguration:
        dumped_configuration = {}
        if self._locale is not None:
            dumped_configuration['locale'] = self.locale

        return dumped_configuration


class App(Configurable[AppConfiguration], ReactiveInstance):
    def __init__(self, configuration: AppConfiguration | None = None, project: Project | None = None, *args, **kwargs):
        from betty.url import AppUrlGenerator, StaticPathUrlGenerator

        super().__init__(*args, **kwargs)
        self._configuration = configuration or AppConfiguration()
        with suppress(FileNotFoundError):
            with Translations():
                self.configuration.read()

        self._acquired = False
        self._extensions = _AppExtensions()
        self._extensions_initialized = False
        self._project = project or Project()
        self._assets: FileSystem | None = None
        self._dispatcher: ExtensionDispatcher | None = None
        self._entity_types: Set[Type[Entity]] | None = None
        self._event_types: Set[Type[EventType]] | None = None
        self._url_generator = AppUrlGenerator(self)
        self._static_url_generator = StaticPathUrlGenerator(self.project.configuration)
        self._locale: Optional[str] = None
        self._translations: Optional[TranslationsRepository] = None
        self._locale = None
        self._default_translations = None
        self._acquire_contexts = ExitStack()
        self._jinja2_environment: Environment | None = None
        self._renderer: Renderer | None = None
        self.__thread_pool_executor: ExceptionRaisingAwaitableExecutor | None = None
        self.__process_pool_executor: ExceptionRaisingAwaitableExecutor | None = None
        self._locks = Locks()
        self._http_client: aiohttp.ClientSession | None = None

    def __getstate__(self) -> None:
        raise RuntimeError(f'{self.__class__} MUST NOT be pickled. Pickle {self.__class__}.project instead.')

    def __copy__(self) -> Self:
        raise RuntimeError(f'{self.__class__} MUST NOT be copied. Copy {self.__class__}.project instead.')

    def __deepcopy__(self, _) -> None:
        raise RuntimeError(f'{self.__class__} MUST NOT be copied. Copy {self.__class__}.project instead.')

    def wait(self) -> None:
        self._wait_for_threads()
        self._wait_for_processes()

    def _wait_for_threads(self) -> None:
        del self._thread_pool_executor

    def _wait_for_processes(self) -> None:
        del self._process_pool_executor

    def acquire(self) -> None:
        if self._acquired:
            raise RuntimeError('This application is acquired already.')
        self._acquired = True
        try:
            # Enable the gettext API by entering a dummy translations context.
            self._acquire_contexts.enter_context(Translations(NullTranslations()))
            # Then acquire the actual locale.
            self._acquire_contexts.enter_context(self.acquire_locale())
        except BaseException:
            self.release()
            raise

    def release(self) -> None:
        if not self._acquired:
            raise RuntimeError('This application is not yet acquired.')
        self._wait_for_threads()
        self._acquire_contexts.close()
        del self.http_client
        self._acquired = False

    @contextmanager
    def acquire_locale(self, *requested_locales: str | None) -> Iterator[Self]:  # type: ignore
        """
        Temporarily change this application's locale and the global gettext translations.
        """
        if not requested_locales:
            requested_locales = (self.configuration.locale,)
        requested_locales = (*requested_locales, 'en-US')
        preferred_locales = [locale for locale in requested_locales if locale is not None]

        negotiated_locale = negotiate_locale(
            preferred_locales,
            {
                rfc_1766_to_bcp_47(locale)
                for locale
                in locale_identifiers()
            },
        )

        if negotiated_locale is None:
            raise ValueError('None of the requested locales are available.')

        previous_locale = self._locale
        self._locale = negotiated_locale

        negotiated_translations_locale = negotiate_locale(
            preferred_locales,
            set(self.translations.locales),
        )
        if negotiated_translations_locale is None:
            negotiated_translations_locale = 'en-US'
        with self.translations[negotiated_translations_locale]:
            yield self

        self._locale = previous_locale

    @property
    def locale(self) -> str:
        if self._locale is None:
            raise RuntimeError(f'No locale has been acquired yet. Use {type(self)}.acquire_locale() to activate a locale.')
        return self._locale

    def __enter__(self) -> App:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    @property
    def project(self) -> Project:
        return self._project

    def discover_extension_types(self) -> Set[Type[Extension]]:
        return {*discover_extension_types(), *map(type, self._extensions.flatten())}

    @property
    def extensions(self) -> Extensions:
        if not self._extensions_initialized:
            self._extensions_initialized = True
            self._update_extensions()
            self.project.configuration.extensions.react(self._update_extensions)

        return self._extensions

    def _update_extensions(self) -> None:
        extension_types_enabled_in_configuration = set()
        for app_extension_configuration in self.project.configuration.extensions:
            if app_extension_configuration.enabled:
                app_extension_configuration.extension_type.enable_requirement().assert_met()
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
                if issubclass(extension_type, ConfigurableExtension) and extension_type in self.project.configuration.extensions:
                    extension: Extension = extension_type(self, configuration=self.project.configuration.extensions[extension_type].extension_configuration)
                else:
                    extension = extension_type(self)
                extensions_batch.append(extension)
                extension_types_sorter.done(extension_type)
            extensions.append(extensions_batch)
        self._extensions._update(extensions)

    @property
    @reactive_property(on_trigger_delete=True)
    def assets(self) -> FileSystem:
        if self._assets is None:
            self._assets = FileSystem()
            self._assets.prepend(ASSETS_DIRECTORY_PATH, 'utf-8')
            for extension in self.extensions.flatten():
                extension_assets_directory_path = extension.assets_directory_path()
                if extension_assets_directory_path is not None:
                    self._assets.prepend(extension_assets_directory_path, 'utf-8')
            if self.project.configuration.assets_directory_path:
                self._assets.prepend(self.project.configuration.assets_directory_path)
        return self._assets

    @assets.deleter
    def assets(self) -> None:
        self._assets = None

    @property
    def dispatcher(self) -> Dispatcher:
        if self._dispatcher is None:
            self._dispatcher = ExtensionDispatcher(self.extensions)

        return self._dispatcher

    @property
    def www_directory_path(self) -> Path:
        if self.project.configuration.multilingual:
            return self.static_www_directory_path / self.project.configuration.locales[self.locale].alias
        return self.static_www_directory_path

    @property
    def static_www_directory_path(self) -> Path:
        return self.project.configuration.www_directory_path

    @property
    def url_generator(self) -> ContentNegotiationUrlGenerator:
        return self._url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        return self._static_url_generator

    @property
    def translations(self) -> TranslationsRepository:
        if self._translations is None:
            self._translations = TranslationsRepository(self.assets)
        return self._translations

    @property
    @reactive_property(on_trigger_delete=True)
    def jinja2_environment(self) -> Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import Environment
            self._jinja2_environment = Environment(self)

        return self._jinja2_environment

    @jinja2_environment.deleter
    def jinja2_environment(self) -> None:
        self._jinja2_environment = None

    @property
    @reactive_property(on_trigger_delete=True)
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
    def concurrency(self) -> int:
        # Assume that any machine that runs Betty has at least two CPU cores.
        return stdos.cpu_count() or 2

    @property
    def _thread_pool_executor(self) -> Executor:
        if self.__thread_pool_executor is None:
            self.__thread_pool_executor = ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor(self.concurrency))
        return self.__thread_pool_executor

    @_thread_pool_executor.deleter
    def _thread_pool_executor(self) -> None:
        if self.__thread_pool_executor is not None:
            self.__thread_pool_executor.wait()

    def do_in_thread(self, task: Callable[[], None]) -> Awaitable[None]:
        return asyncio.get_event_loop().run_in_executor(self._thread_pool_executor, task)

    @property
    def _process_pool_executor(self) -> Executor:
        if self.__process_pool_executor is None:
            self.__process_pool_executor = ExceptionRaisingAwaitableExecutor(ProcessPoolExecutor(self.concurrency))
        return self.__process_pool_executor

    @_process_pool_executor.deleter
    def _process_pool_executor(self) -> None:
        if self.__process_pool_executor is not None:
            self.__process_pool_executor.wait()

    def do_in_process(self, task: Callable[[], None]) -> Awaitable[None]:
        return asyncio.get_event_loop().run_in_executor(self._process_pool_executor, task)

    @property
    def locks(self) -> Locks:
        return self._locks

    @property
    @reactive_property(on_trigger_delete=True)
    def http_client(self) -> aiohttp.ClientSession:
        if not self._http_client:
            self._http_client = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))
            weakref.finalize(self, sync(self._http_client.close))
        return self._http_client

    @http_client.deleter  # type: ignore
    @sync
    async def http_client(self) -> None:
        if self._http_client is not None:
            await self._http_client.close()
            self._http_client = None

    @property
    @reactive_property(on_trigger_delete=True)
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

    @entity_types.deleter
    def entity_types(self) -> None:
        self._entity_types = None

    @property
    @reactive_property(on_trigger_delete=True)
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
