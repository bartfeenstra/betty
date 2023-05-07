from __future__ import annotations

import weakref
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import suppress
from pathlib import Path
from typing import List, Type, TYPE_CHECKING, Set, Optional, Callable

import aiohttp
from reactives.instance import ReactiveInstance
from reactives.instance.method import reactive_method
from reactives.instance.property import reactive_property

from betty.app.extension import ListExtensions, Extension, Extensions, build_extension_type_graph, \
    CyclicDependencyError, ExtensionDispatcher, ConfigurableExtension, discover_extension_types
from betty.asyncio import sync
from betty.concurrent import ExceptionRaisingAwaitableExecutor
from betty.config import FileBasedConfiguration, DumpedConfigurationImport, Configurable, DumpedConfigurationExport
from betty.config.load import ConfigurationValidationError, Loader, Field
from betty.dispatch import Dispatcher
from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH, HOME_DIRECTORY_PATH
from betty.locale import TranslationRepository, get_data, PassthroughTranslation, Localey
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
    from betty.json import JSONEncoder
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
            get_data(locale)
        except ValueError:
            raise ConfigurationValidationError(_('{locale} is not a valid IETF BCP 47 language tag.').format(locale=locale))
        self._locale = locale

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'locale': Field(
                True,
                loader.assert_str,  # type: ignore
                lambda x: loader.assert_setattr(self, 'locale', x),
            ),
        })

    def dump(self) -> DumpedConfigurationExport:
        dumped_configuration = {}
        if self._locale is not None:
            dumped_configuration['locale'] = self.locale

        return dumped_configuration


class App(Configurable[AppConfiguration], ReactiveInstance):
    def __init__(self, locale: Localey | None = None, *args, **kwargs):
        from betty.url import AppUrlGenerator, StaticPathUrlGenerator

        super().__init__(*args, **kwargs)
        self._configuration = AppConfiguration()
        self._locale = locale
        self._translation = None
        with PassthroughTranslation():
            with suppress(FileNotFoundError):
                self.configuration.read()

        self._extensions = _AppExtensions()
        self._extensions_initialized = False
        self._project = Project()
        self._assets = FileSystem()
        self._dispatcher = None
        self._entity_types = None
        self._event_types = None
        self._url_generator = AppUrlGenerator(self)
        self._static_url_generator = StaticPathUrlGenerator(self.project.configuration)
        self._debug = None
        self._locale: Optional[str] = None
        self._translations: Optional[TranslationRepository] = None
        self._default_translations = None
        self._jinja2_environment = None
        self._renderer = None
        self._executor = None
        self._locks = Locks()
        self._http_client = None

    def __copy__(self) -> Self:  # type: ignore
        copied = type(self)()
        copied._project = self._project
        return copied

    def wait(self) -> None:
        self._wait_for_threads()

    def _wait_for_threads(self) -> None:
        if self._executor:
            self._executor.wait()

    @property
    @reactive_property
    def locale(self) -> str:
        # @todo Finish this
        # @todo
        # @todo
        # @todo IDEA
        # @todo One app, one locale. Although the app's locale must remain configurable
        # @todo Now, we want the app to be able to enter localized contexts (eg install gettext)
        # @todo How do we want to be able to spin up a copy of the app in a subprocess, with a different locale?
        # @todo Remember that old async PR that's still pending? We introduced methods on App to run a task in a thread or a subprocess
        # @todo Can introduce that here, with another wrapper specifically for doing to with a different locale
        # @todo However,we've got to make sure apps can be initialized with a locale override, so as not to read that particular app config setting
        # @todo Also, when the app locale config setting changes, and the app has no locale override, uninstall the current translation and install a new one for the newly configured locale
        # @todo Fuuuck this may also mean we need to make the ENTIRE ancestry pickleable. Let's hope that other PR is in a decent shape still...
        # @todo
        return self._locale or self.configuration.locale

    @reactive_method(on_trigger_call=True)
    def _install_translation(self) -> None:
        if self._translation:
            self._uninstall_translation()
        self._translation = self.translations.get_negotiated(self.locale)
        self._translation.install()

    def _uninstall_translation(self) -> None:
        self._wait_for_threads()
        self._translation.uninstall()
        self._translation = None

    def __enter__(self) -> Self:
        self._install_translation()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wait()
        del self.http_client
        self._uninstall_translation()

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
        if len(self._assets) == 0:
            self._build_assets()

        return self._assets

    @assets.deleter
    def assets(self) -> None:
        # Proactively rebuild the assets, so the assets file system can be reused.
        self._build_assets()

    def _build_assets(self) -> None:
        self._assets.clear()
        self._assets.prepend(ASSETS_DIRECTORY_PATH, 'utf-8')
        for extension in self.extensions.flatten():
            extension_assets_directory_path = extension.assets_directory_path()
            if extension_assets_directory_path is not None:
                self._assets.prepend(extension_assets_directory_path, 'utf-8')
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
    def translations(self) -> TranslationRepository:
        if self._translations is None:
            self._translations = TranslationRepository(self.assets)
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
    def executor(self) -> Executor:
        if self._executor is None:
            self._executor = ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor())
        return self._executor

    @property
    def json_encoder(self) -> Callable[[], JSONEncoder]:
        from betty.json import JSONEncoder
        return lambda *args, **kwargs: JSONEncoder(
            self.project.configuration.locales,
            self.url_generator,
            self.static_url_generator,
            *args,
            **kwargs,
        )

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
