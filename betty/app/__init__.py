from __future__ import annotations

import locale
import weakref
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import contextmanager, ExitStack, suppress
from gettext import NullTranslations
from pathlib import Path
from typing import List, Type, TYPE_CHECKING, Set, Iterator, Optional

from babel.core import parse_locale
from babel.localedata import locale_identifiers

from betty.resource import Releaser, Acquirer

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self

from reactives.factory.type import ReactiveInstance

from betty.app.extension import ListExtensions, Extension, Extensions, build_extension_type_graph, \
    CyclicDependencyError, ExtensionDispatcher, ConfigurableExtension
from betty.asyncio import sync
from betty.model import Entity, EntityTypeProvider
from betty.model.event_type import EventTypeProvider, Birth, Baptism, Adoption, Death, Funeral, Cremation, Burial, Will, \
    Engagement, Marriage, MarriageAnnouncement, Divorce, DivorceAnnouncement, Residence, Immigration, Emigration, \
    Occupation, Retirement, Correspondence, Confirmation
from betty.project import Project

try:
    from graphlib import TopologicalSorter, CycleError
except ImportError:
    from graphlib_backport import TopologicalSorter  # type: ignore

import aiohttp
from jinja2 import Environment as Jinja2Environment
from reactives import reactive

from betty.concurrent import ExceptionRaisingAwaitableExecutor
from betty.config import ConfigurationError, FileBasedConfiguration, DumpedConfiguration
from betty.dispatch import Dispatcher
from betty.lock import Locks
from betty.render import Renderer, SequentialRenderer

from betty.model.ancestry import Citation, Event, File, Person, PersonName, Presence, Place, Enclosure, \
    Source, Note, EventType
from betty.config import Configurable
from betty.fs import FileSystem, ASSETS_DIRECTORY_PATH, HOME_DIRECTORY_PATH
from betty.locale import negotiate_locale, TranslationsRepository, Translations, rfc_1766_to_bcp_47, bcp_47_to_rfc_1766, \
    getdefaultlocale


if TYPE_CHECKING:
    from betty.builtins import _
    from betty.url import StaticUrlGenerator, ContentNegotiationUrlGenerator

CONFIGURATION_DIRECTORY_PATH = HOME_DIRECTORY_PATH / 'configuration'


@reactive
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

    @reactive  # type: ignore
    @property
    def locale(self) -> Optional[str]:
        if self._locale is None:
            return getdefaultlocale()
        return self._locale

    @locale.setter
    def locale(self, locale: str) -> None:
        self._locale = locale

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('Betty application configuration must be a mapping (dictionary).'))

        if 'locale' in dumped_configuration:
            if not isinstance(dumped_configuration['locale'], str):
                raise ConfigurationError(_('The locale must be a string.'), contexts=['`title`'])
            try:
                parse_locale(bcp_47_to_rfc_1766(dumped_configuration['locale']))
            except ValueError:
                raise ConfigurationError(_('{locale} is not a valid IETF BCP 47 language tag.').format(locale=locale))
            self.locale = dumped_configuration['locale']

    def dump(self) -> DumpedConfiguration:
        dumped_configuration = {}
        if self._locale is not None:
            dumped_configuration['locale'] = self.locale

        return dumped_configuration


@reactive
class App(Acquirer, Releaser, Configurable[AppConfiguration], ReactiveInstance):
    def __init__(self, *args, **kwargs):
        from betty.url import AppUrlGenerator, StaticPathUrlGenerator

        super().__init__(*args, **kwargs)
        self._configuration = AppConfiguration()
        with suppress(FileNotFoundError):
            self.configuration.read()

        self._acquired = False
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
        self._translations = TranslationsRepository(self.assets)
        self._default_translations = None
        self._acquire_contexts = ExitStack()
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

    def acquire(self) -> None:
        if self._acquired:
            raise RuntimeError('This application is acquired already.')
        self._acquired = True
        try:
            # Enable the gettext API by entering a dummy translations context.
            self._acquire_contexts.enter_context(Translations(NullTranslations()))
            # Then acquire the actual locale.
            self._acquire_contexts.enter_context(self.acquire_locale())

            for extension in self.extensions.flatten():
                if isinstance(extension, Acquirer):
                    extension.acquire()
                if isinstance(extension, Releaser):
                    self._acquire_contexts.callback(extension.release)
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
    def acquire_locale(self, requested_locale: Optional[str] = None) -> Iterator[Self]:  # type: ignore
        """
        Temporarily change this application's locale and the global gettext translations.
        """
        if requested_locale is None:
            requested_locale = self.configuration.locale

        negotiated_locale = negotiate_locale(
            requested_locale,
            {
                rfc_1766_to_bcp_47(locale)
                for locale
                in locale_identifiers()
            },
        )

        if negotiated_locale is None:
            raise ValueError(f'Locale "{requested_locale}" is not enabled.')

        previous_locale = self._locale
        self._locale = negotiated_locale

        negotiated_translations_locale = negotiate_locale(
            requested_locale,
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
                if issubclass(extension_type, ConfigurableExtension) and extension_type in self.project.configuration.extensions:
                    extension: Extension = extension_type(self, configuration=self.project.configuration.extensions[extension_type].extension_configuration)
                else:
                    extension = extension_type(self)
                extensions_batch.append(extension)
                extension_types_sorter.done(extension_type)
            extensions.append(extensions_batch)
        self._extensions._update(extensions)

    @reactive  # type: ignore
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
    def translations(self) -> TranslationsRepository:
        return self._translations

    @reactive  # type: ignore
    @property
    def jinja2_environment(self) -> Jinja2Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import Environment
            self._jinja2_environment = Environment(self)

        return self._jinja2_environment

    @jinja2_environment.deleter
    def jinja2_environment(self) -> None:
        self._jinja2_environment = None

    @reactive  # type: ignore
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

    @reactive  # type: ignore
    @property
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

    @reactive  # type: ignore
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

    @entity_types.deleter
    def entity_types(self) -> None:
        self._entity_types = None

    @reactive  # type: ignore
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
