from __future__ import annotations

import weakref
import asyncio
from concurrent.futures import Executor, ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import suppress
from pathlib import Path
import os as stdos
from typing import List, Optional, Type, TYPE_CHECKING, Set, Callable, Awaitable, Mapping

import aiohttp
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property

from betty.app.extension import ListExtensions, Extension, Extensions, build_extension_type_graph, \
    CyclicDependencyError, ExtensionDispatcher, ConfigurableExtension, discover_extension_types
from betty.asyncio import sync
from betty.cache import Cache
from betty.concurrent import ExceptionRaisingAwaitableExecutor
from betty.config import DumpedConfiguration, VoidableDumpedConfiguration, Configurable, FileBasedConfiguration
from betty.config.dump import void_none, minimize
from betty.config.load import ConfigurationValidationError, Fields, Assertions, OptionalField, Asserter
from betty.dispatch import Dispatcher
from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH, HOME_DIRECTORY_PATH
from betty.locale import LocalizerRepository, get_data, Localey, DEFAULT_LOCALE, to_locale, \
    Localizer, DEFAULT_LOCALIZER
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
    from betty.jinja2 import Environment
    from betty.json import JSONEncoder
    from betty.serve import Server
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
        self._locale: str | None = None

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
            get_data(locale)
        except ValueError:
            raise ConfigurationValidationError(self.localizer._('"{locale}" is not a valid IETF BCP 47 language tag.').format(locale=locale))
        self._locale = locale

    def update(self, other: Self) -> None:
        self._locale = other._locale
        self.react.trigger()

    @classmethod
    def load(
            cls,
            dumped_configuration: DumpedConfiguration,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter(localizer=localizer)
        asserter.assert_record(Fields(
            OptionalField(
                'locale',
                Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'locale')),
        ),
        )(dumped_configuration)
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
        return minimize({
            'locale': void_none(self.locale)
        }, True)


class App(Configurable[AppConfiguration], ReactiveInstance):
    def __init__(
        self,
        configuration: AppConfiguration | None = None,
        project: Project | None = None,
        locale: Localey | None = DEFAULT_LOCALE,
    ):
        super().__init__()
        self._configuration = configuration or AppConfiguration()
        self._assets: FileSystem | None = None
        self._extensions = _AppExtensions()
        self._extensions_initialized = False
        self._locale = to_locale(locale) if locale else None
        self._localization_initialized = False
        self._localizer: Localizer | None = None
        self._localizers: LocalizerRepository | None = None
        with suppress(FileNotFoundError):
            self.configuration.read()
        self._project = project or Project()
        self._init_localization()

        self._dispatcher: ExtensionDispatcher | None = None
        self._entity_types: Set[Type[Entity]] | None = None
        self._event_types: Set[Type[EventType]] | None = None
        self._url_generator: ContentNegotiationUrlGenerator | None = None
        self._static_url_generator: StaticUrlGenerator | None = None
        self._jinja2_environment: Environment | None = None
        self._renderer: Renderer | None = None
        self.__thread_pool_executor: ExceptionRaisingAwaitableExecutor | None = None
        self.__process_pool_executor: ExceptionRaisingAwaitableExecutor | None = None
        self._locks = Locks()
        self._http_client: aiohttp.ClientSession | None = None
        self._cache: Cache | None = None

    def __getstate__(self) -> None:
        raise RuntimeError(f'{self.__class__} MUST NOT be pickled. Pickle {self.__class__}.project instead.')

    def __copy__(self) -> Self:
        raise RuntimeError(f'{self.__class__} MUST NOT be copied. Copy {self.__class__}.project instead.')

    def __deepcopy__(self, _) -> None:
        raise RuntimeError(f'{self.__class__} MUST NOT be copied. Copy {self.__class__}.project instead.')

    def wait(self) -> None:
        del self._thread_pool_executor
        del self._process_pool_executor
        del self.http_client

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wait()

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
        for app_extension_configuration in self.project.configuration.extensions.values():
            if app_extension_configuration.enabled:
                app_extension_configuration.extension_type.enable_requirement(localizer=self._localizer).assert_met()
                extension_types_enabled_in_configuration.add(app_extension_configuration.extension_type)

        extension_types_sorter = TopologicalSorter(
            build_extension_type_graph(extension_types_enabled_in_configuration)
        )
        try:
            extension_types_sorter.prepare()
        except CycleError:
            raise CyclicDependencyError([
                app_extension_configuration.extension_type
                for app_extension_configuration
                in self.project.configuration.extensions.values()
            ])

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
        from betty.url import AppUrlGenerator

        if self._url_generator is None:
            self._url_generator = AppUrlGenerator(self)
        return self._url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        from betty.url import StaticPathUrlGenerator

        if self._static_url_generator is None:
            self._static_url_generator = StaticPathUrlGenerator(self.project.configuration)
        return self._static_url_generator

    @property
    def locale(self) -> str:
        return self._locale or self.configuration.locale or DEFAULT_LOCALE

    @property
    def localizer(self) -> Localizer:
        if self._localizer is None:
            if not self._localization_initialized:
                return DEFAULT_LOCALIZER
            self._localizer = self.localizers.get_negotiated(self.locale)
        return self._localizer

    @property
    def localizers(self) -> LocalizerRepository:
        if self._localizers is None:
            self._localizers = LocalizerRepository(self.assets)
        return self._localizers

    def _init_localization(self) -> None:
        self._localization_initialized = True
        self.configuration.localizer = self.localizer
        self.project.localizer = self.localizer

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
        with suppress(KeyError):
            return int(stdos.environ['BETTY_CONCURRENCY'])
        # Assume that any machine that runs Betty has at least two CPU cores.
        return stdos.cpu_count() or 2

    @property
    def async_concurrency(self) -> int:
        return self.concurrency ** 2

    @property
    def _thread_pool_executor(self) -> Executor:
        if self.__thread_pool_executor is None:
            self.__thread_pool_executor = ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor(self.async_concurrency))
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
    def json_encoder(self) -> Type[JSONEncoder]:
        from betty.json import JSONEncoder
        return lambda *args, **kwargs: JSONEncoder(self)  # type: ignore[return-value]

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

    @property
    def servers(self) -> Mapping[str, Server]:
        from betty import serve
        from betty.demo import DemoServer

        return {
            server.name(): server
            for server
            in [
                *(
                    server
                    for extension in self.extensions.flatten()
                    if isinstance(extension, serve.ServerProvider)
                    for server in extension.servers
                ),
                serve.BuiltinServer(self.project),
                DemoServer(localizer=self._localizer),
            ]
        }

    @property
    def cache(self) -> Cache:
        if self._cache is None:
            self._cache = Cache(localizer=self.localizer)
        return self._cache
