"""Define Betty's core application functionality."""

from __future__ import annotations

import operator
import os as stdos
import weakref
from collections.abc import Callable
from contextlib import suppress
from functools import reduce
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Mapping, Self, final

import aiohttp

from betty.app.extension import ListExtensions, Extension, Extensions, build_extension_type_graph, \
    CyclicDependencyError, ExtensionDispatcher, ConfigurableExtension, discover_extension_types
from betty.asyncio import sync, wait
from betty.cache import Cache
from betty.config import Configurable, FileBasedConfiguration
from betty.dispatch import Dispatcher
from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH, HOME_DIRECTORY_PATH
from betty.locale import LocalizerRepository, get_data, DEFAULT_LOCALE, Localizer, Str
from betty.model import Entity, EntityTypeProvider
from betty.model.event_type import EventType, EventTypeProvider, Birth, Baptism, Adoption, Death, Funeral, Cremation, \
    Burial, Will, Engagement, Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, \
    Emigration, Occupation, Retirement, Correspondence, Confirmation
from betty.project import Project
from betty.render import Renderer, SequentialRenderer
from betty.serde.dump import minimize, void_none, Dump, VoidableDump, Void
from betty.serde.load import AssertionFailed, Fields, Assertions, OptionalField, Asserter

if TYPE_CHECKING:
    from betty.jinja2 import Environment
    from betty.serve import Server
    from betty.url import StaticUrlGenerator, LocalizedUrlGenerator

CONFIGURATION_DIRECTORY_PATH = HOME_DIRECTORY_PATH / 'configuration'


class _AppExtensions(ListExtensions):
    def __init__(self):
        super().__init__([])

    def _update(self, extensions: list[list[Extension]]) -> None:
        self._extensions = extensions


class AppConfiguration(FileBasedConfiguration):
    def __init__(
        self,
        *,
        locale: str | None = None,
    ):
        super().__init__()
        self._locale: str | None = locale

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
    def locale(self) -> str | None:
        return self._locale

    @locale.setter
    def locale(self, locale: str) -> None:
        try:
            get_data(locale)
        except ValueError:
            raise AssertionFailed(Str._(
                '"{locale}" is not a valid IETF BCP 47 language tag.',
                locale=locale,
            ))
        self._locale = locale
        self._dispatch_change()

    def update(self, other: Self) -> None:
        self._locale = other._locale
        self._dispatch_change()

    @classmethod
    def load(
            cls,
            dump: Dump,
            configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        asserter.assert_record(Fields(
            OptionalField(
                'locale',
                Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'locale')),
        ),
        )(dump)
        return configuration

    def dump(self) -> VoidableDump:
        return minimize({
            'locale': void_none(self.locale)
        }, True)


@final
class App(Configurable[AppConfiguration]):
    def __init__(
        self,
        configuration: AppConfiguration | None = None,
        project: Project | None = None,
    ):
        super().__init__()
        self._started = False
        self._configuration = configuration or AppConfiguration()
        self._configuration.on_change(self._on_locale_change)
        self._assets: FileSystem | None = None
        self._extensions = _AppExtensions()
        self._extensions_initialized = False
        self._localization_initialized = False
        self._localizer: Localizer | None = None
        self._localizers: LocalizerRepository | None = None
        with suppress(FileNotFoundError):
            wait(self.configuration.read())
        self._project = project or Project()
        self.project.configuration.extensions.on_change(self._update_extensions)

        self._dispatcher: ExtensionDispatcher | None = None
        self._entity_types: set[type[Entity]] | None = None
        self._event_types: set[type[EventType]] | None = None
        self._url_generator: LocalizedUrlGenerator | None = None
        self._static_url_generator: StaticUrlGenerator | None = None
        self._jinja2_environment: Environment | None = None
        self._renderer: Renderer | None = None
        self._http_client: aiohttp.ClientSession | None = None
        self._cache: Cache | None = None

    @classmethod
    def _unreduce(cls, dumped_app_configuration: VoidableDump, project: Project) -> Self:
        if dumped_app_configuration is Void:
            app_configuration = None
        else:
            app_configuration = AppConfiguration.load(
                dumped_app_configuration,  # type: ignore[arg-type]
            )
        return App(
            app_configuration,
            project,
        )

    def __reduce__(self) -> tuple[
        Callable[[VoidableDump, Project], Self],
        tuple[
            VoidableDump,
            Project,
        ],
    ]:
        return (
            App._unreduce,
            (
                self._configuration.dump(),
                self._project,
            ),
        )

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        await self.stop()

    async def start(self) -> None:
        if self._started:
            raise RuntimeError('This app has started already.')
        self._started = True

    async def stop(self) -> None:
        self._started = False
        del self.http_client

    def __del__(self) -> None:
        if self._started:
            raise RuntimeError(f'{self} was started, but never stopped.')

    def _on_locale_change(self) -> None:
        del self.localizer
        del self.localizers

    @property
    def project(self) -> Project:
        return self._project

    def discover_extension_types(self) -> set[type[Extension]]:
        return {*discover_extension_types(), *map(type, self._extensions.flatten())}

    @property
    def extensions(self) -> Extensions:
        if not self._extensions_initialized:
            self._extensions_initialized = True
            self._update_extensions()

        return self._extensions

    def _update_extensions(self) -> None:
        extension_types_enabled_in_configuration = set()
        for app_extension_configuration in self.project.configuration.extensions.values():
            if app_extension_configuration.enabled:
                app_extension_configuration.extension_type.enable_requirement().assert_met()
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
        del self.assets
        del self.localizers
        del self.localizer
        del self.jinja2_environment
        del self.renderer
        del self.entity_types
        del self.event_types

    @property
    def assets(self) -> FileSystem:
        if self._assets is None:
            assets = FileSystem()
            assets.prepend(ASSETS_DIRECTORY_PATH, 'utf-8')
            for extension in self.extensions.flatten():
                extension_assets_directory_path = extension.assets_directory_path()
                if extension_assets_directory_path is not None:
                    assets.prepend(extension_assets_directory_path, 'utf-8')
            assets.prepend(self.project.configuration.assets_directory_path)
            self._assets = assets
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
    def url_generator(self) -> LocalizedUrlGenerator:
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
    @sync
    async def localizer(self) -> Localizer:
        """
        Get the application's localizer.
        """
        if self._localizer is None:
            self._localizer = await self.localizers.get_negotiated(self.configuration.locale or DEFAULT_LOCALE)
        return self._localizer

    @localizer.deleter
    def localizer(self) -> None:
        self._localizer = None

    @property
    def localizers(self) -> LocalizerRepository:
        if self._localizers is None:
            self._localizers = LocalizerRepository(self.assets)
        return self._localizers

    @localizers.deleter
    def localizers(self) -> None:
        self._localizers = None

    @property
    def jinja2_environment(self) -> Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import Environment
            self._jinja2_environment = Environment(self)

        return self._jinja2_environment

    @jinja2_environment.deleter
    def jinja2_environment(self) -> None:
        self._jinja2_environment = None

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
    def concurrency(self) -> int:
        with suppress(KeyError):
            return int(stdos.environ['BETTY_CONCURRENCY'])
        # Assume that any machine that runs Betty has at least two CPU cores.
        return stdos.cpu_count() or 2

    @property
    def async_concurrency(self) -> int:
        return self.concurrency ** 2

    @property
    def http_client(self) -> aiohttp.ClientSession:
        if not self._http_client:
            self._http_client = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit_per_host=5),
                headers={
                    'User-Agent': f'Betty (https://github.com/bartfeenstra/betty) on behalf of {self._project.configuration.base_url}{self._project.configuration.root_path}',
                },
            )
            weakref.finalize(self, sync(self._http_client.close))
        return self._http_client

    @http_client.deleter
    @sync
    async def http_client(self) -> None:
        if self._http_client is not None:
            await self._http_client.close()
            self._http_client = None

    @property
    @sync
    async def entity_types(self) -> set[type[Entity]]:
        if self._entity_types is None:
            from betty.model.ancestry import Citation, Enclosure, Event, File, Note, Person, PersonName, Presence, Place, Source

            self._entity_types = reduce(operator.or_, await self.dispatcher.dispatch(EntityTypeProvider)(), set()) | {
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
    @sync
    async def event_types(self) -> set[type[EventType]]:
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

    @event_types.deleter
    def event_types(self) -> None:
        self._event_types = None

    @property
    def servers(self) -> Mapping[str, Server]:
        from betty import serve
        from betty.extension.demo import DemoServer

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
                serve.BuiltinAppServer(self),
                DemoServer(),
            ]
        }

    @property
    def cache(self) -> Cache:
        if self._cache is None:
            self._cache = Cache(self.localizer)
        return self._cache
