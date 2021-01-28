import gettext
from collections import defaultdict, OrderedDict
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path

import aiohttp
from jinja2 import Environment
from reactives import reactive, Scope

from betty.concurrent import ExceptionRaisingExecutor
from betty.dispatch import Dispatcher
from betty.extension import build_extension_type_graph, ConfigurableExtension, Extension
from betty.lock import Locks
from betty.render import Renderer, SequentialRenderer

try:
    from contextlib import AsyncExitStack
except ImportError:
    from async_exit_stack import AsyncExitStack
from copy import copy
from typing import Type, Dict, Optional, Iterable, Sequence

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.fs import FileSystem
from betty.graph import tsort
from betty.locale import open_translations, Translations, negotiate_locale
from betty.url import AppUrlGenerator, StaticPathUrlGenerator, LocalizedUrlGenerator, StaticUrlGenerator


@reactive
class Extensions:
    def __init__(self, extensions: Optional[Sequence[Extension]] = None):
        self._extensions = OrderedDict()
        if extensions is not None:
            for extension in extensions:
                self._extensions[extension.extension_type] = extension

    @Scope.register_self
    def __getitem__(self, extension_type: Type[Extension]) -> Extension:
        return self._extensions[extension_type]

    @Scope.register_self
    def __iter__(self) -> Iterable[Extension]:
        return (extension for extension in self._extensions.values())

    @Scope.register_self
    def __eq__(self, other):
        if not isinstance(other, Extensions):
            return NotImplemented
        return self._extensions == other._extensions

    def _add(self, extension: Extension) -> None:
        self._extensions[type(extension)] = extension

    def _remove(self, extension_type: Type[Extension]) -> None:
        del self._extensions[extension_type]


@reactive
class App:
    def __init__(self, configuration: Configuration):
        self._app_stack = []
        self._ancestry = Ancestry()
        self._configuration = configuration
        self._assets = FileSystem()
        self._dispatcher = None
        self._localized_url_generator = AppUrlGenerator(configuration)
        self._static_url_generator = StaticPathUrlGenerator(configuration)
        self._locale = None
        self._translations = defaultdict(gettext.NullTranslations)
        self._default_translations = None
        self._extensions = Extensions()
        self._extension_exit_stack = AsyncExitStack()
        self._jinja2_environment = None
        self._renderer = None
        self._executor = None
        self._locks = Locks()
        self._http_client = None

    @property
    def configuration(self) -> Configuration:
        return self._configuration

    async def enter(self):
        if not self._app_stack:
            for extension in self.extensions:
                await self._extension_exit_stack.enter_async_context(extension)

        self._default_translations = Translations(self.translations[self.locale])
        self._default_translations.install()

        if self._executor is None:
            self._executor = ExceptionRaisingExecutor(ThreadPoolExecutor())

        self._app_stack.append(self)

        return self

    async def exit(self):
        self._app_stack.pop()

        self._default_translations.uninstall()

        if not self._app_stack:
            self._executor.shutdown()
            self._executor = None

            if self._http_client is not None:
                await self._http_client.close()
                self._http_client = None

            await self._extension_exit_stack.aclose()

    async def __aenter__(self) -> 'App':
        return await self.enter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exit()

    @property
    def locale(self) -> str:
        if self._locale is not None:
            return self._locale
        return self._configuration.locales.default.locale

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry

    @property
    def extensions(self) -> Extensions:
        extensions_enabled_in_configuration = {
            extension_configuration.extension_type
            for extension_configuration in self._configuration.extensions
            if extension_configuration.enabled
        }
        extension_types = tsort(build_extension_type_graph(extensions_enabled_in_configuration))

        # Remove disabled extensions.
        for extension in list(self._extensions):
            extension_type = type(extension)
            if extension_type not in extension_types:
                self._extensions._remove(extension_type)

        # Add enabled extensions.
        for extension_type in extension_types:
            if extension_type not in self._extensions:
                if issubclass(extension_type, ConfigurableExtension):
                    if extension_type not in extensions_enabled_in_configuration or self._configuration.extensions[extension_type].extension_type_configuration is None:
                        configuration = extension_type.default_configuration()
                    else:
                        configuration = self._configuration.extensions[extension_type].extension_type_configuration
                    extension = extension_type(self, configuration)
                else:
                    extension = extension_type(self)

                self._extensions._add(extension)

        return self._extensions

    @reactive(on_trigger=(lambda app: app._assets.paths.clear(),))
    @property
    def assets(self) -> FileSystem:
        if len(self._assets.paths) == 0:
            self._assets.paths.appendleft((Path(__file__).resolve().parent / 'assets', 'utf-8'))
            for extension in self.extensions:
                if extension.assets_directory_path is not None:
                    self._assets.paths.appendleft((extension.assets_directory_path, 'utf-8'))
            if self._configuration.assets_directory_path:
                self._assets.paths.appendleft((self._configuration.assets_directory_path, None))

        return self._assets

    @property
    def dispatcher(self) -> Dispatcher:
        if self._dispatcher is None:
            from betty.extension import ExtensionDispatcher

            self._dispatcher = ExtensionDispatcher(list(self.extensions))

        return self._dispatcher

    @property
    def localized_url_generator(self) -> LocalizedUrlGenerator:
        return self._localized_url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        return self._static_url_generator

    @reactive(on_trigger=(lambda app: app._translations.clear(),))
    @property
    def translations(self) -> Dict[str, gettext.NullTranslations]:
        if len(self._translations) == 0:
            self._translations['en-US'] = gettext.NullTranslations()
            for locale_configuration in self._configuration.locales:
                for assets_path, _ in reversed(self._assets.paths):
                    translations = open_translations(locale_configuration.locale, assets_path)
                    if translations:
                        translations.add_fallback(self._translations[locale_configuration])
                        self._translations[locale_configuration] = translations

        return self._translations

    @reactive(on_trigger=(lambda app: setattr(app, '_jinja2_environment', None),))
    @property
    def jinja2_environment(self) -> Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import BettyEnvironment
            self._jinja2_environment = BettyEnvironment(self)

        return self._jinja2_environment

    @reactive(on_trigger=(lambda app: setattr(app, '_renderer', None),))
    @property
    def renderer(self) -> Renderer:
        if not self._renderer:
            from betty.jinja2 import Jinja2Renderer

            self._renderer = SequentialRenderer([
                Jinja2Renderer(self.jinja2_environment, self._configuration),
            ])

        return self._renderer

    @property
    def executor(self) -> Executor:
        if self._executor is None:
            raise RuntimeError("Cannot get the executor before this app's context is entered.")
        return self._executor

    @property
    def locks(self) -> Locks:
        return self._locks

    @property
    def http_client(self) -> aiohttp.ClientSession:
        if self._http_client is None:
            self._http_client = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))
        return self._http_client

    def with_locale(self, locale: str) -> 'App':
        locale = negotiate_locale(locale, [locale_configuration.locale for locale_configuration in self.configuration.locales])
        if locale is None:
            raise ValueError('Locale "%s" is not enabled.' % locale)
        if locale == self.locale:
            return self

        app = copy(self)
        app._locale = locale

        # Clear all locale-dependent lazy-loaded attributes.
        app._jinja2_environment = None
        app._renderer = None

        return app
