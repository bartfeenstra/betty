from __future__ import annotations
from collections import defaultdict
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager
from gettext import NullTranslations

try:
    from graphlib import TopologicalSorter
except ImportError:
    from graphlib_backport import TopologicalSorter
from pathlib import Path

import aiohttp
from jinja2 import Environment
from reactives import reactive, scope

from betty.concurrent import ExceptionRaisingExecutor
from betty.dispatch import Dispatcher
from betty.extension import _build_extension_type_graph, ConfigurableExtension, Extension, Extensions
from betty.lock import Locks
from betty.render import Renderer, SequentialRenderer

from typing import Type, Dict, Sequence, List

from betty.model.ancestry import Ancestry
from betty.config import Configuration
from betty.fs import FileSystem
from betty.locale import open_translations, Translations, negotiate_locale
from betty.url import AppUrlGenerator, StaticPathUrlGenerator, LocalizedUrlGenerator, StaticUrlGenerator


@reactive
class _AppExtensions(Extensions):
    def __init__(self):
        self._extensions = []

    @scope.register_self
    def __getitem__(self, extension_type: Type[Extension]) -> Extension:
        for extension in self.flatten():
            if type(extension) == extension_type:
                return extension
        raise KeyError(f'Unknown extension of type "{extension_type}"')

    @scope.register_self
    def __iter__(self) -> Sequence[Sequence[Extension]]:
        # Use a generator so we discourage calling code from storing the result.
        for batch in self._extensions:
            yield (extension for extension in batch)

    @scope.register_self
    def __contains__(self, extension_type: Type[Extension]) -> bool:
        for extension in self.flatten():
            if type(extension) == extension_type:
                return True
        return False

    def _update(self, extensions: List[List[Extension]]) -> None:
        self._extensions = extensions
        self.react.trigger()


@reactive
class App:
    def __init__(self, configuration: Configuration):
        self._active = False
        self._ancestry = Ancestry()
        self._configuration = configuration
        self._assets = FileSystem()
        self._dispatcher = None
        self._localized_url_generator = AppUrlGenerator(configuration)
        self._static_url_generator = StaticPathUrlGenerator(configuration)
        self._debug = None
        self._locale = None
        self._translations = defaultdict(NullTranslations)
        self._default_translations = None
        self._extensions = None
        self._activation_exit_stack = AsyncExitStack()
        self._jinja2_environment = None
        self._renderer = None
        self._executor = None
        self._locks = Locks()
        self._http_client = None

    @property
    def configuration(self) -> Configuration:
        return self._configuration

    async def wait(self) -> None:
        await self._wait_for_threads()

    async def _wait_for_threads(self) -> None:
        del self.executor

    async def activate(self) -> App:
        if self._active:
            raise RuntimeError('This application is active already.')
        self._active = True

        await self._wait_for_threads()

        try:
            await self._activation_exit_stack.enter_async_context(self.with_locale(self.locale))
            for extension in self.extensions.flatten():
                await self._activation_exit_stack.enter_async_context(extension)
        except BaseException:
            await self.deactivate()
            raise

        return self

    async def deactivate(self):
        if not self._active:
            raise RuntimeError('This application is not yet active.')
        self._active = False

        await self._wait_for_threads()

        await self._activation_exit_stack.aclose()

    async def __aenter__(self) -> App:
        return await self.activate()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.deactivate()

    @reactive
    @property
    def debug(self) -> bool:
        if self._debug is not None:
            return self._debug
        return self._configuration.debug

    @reactive
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
        if self._extensions is None:
            self._extensions = _AppExtensions()
            self._update_extensions()
            self._configuration.extensions.react(self._update_extensions)

        return self._extensions

    def _update_extensions(self) -> None:
        extension_types_enabled_in_configuration = {
            extension_configuration.extension_type
            for extension_configuration in self._configuration.extensions
            if extension_configuration.enabled
        }

        extension_types_sorter = TopologicalSorter(
            _build_extension_type_graph(extension_types_enabled_in_configuration)
        )
        extension_types_sorter.prepare()

        extensions = []
        while extension_types_sorter.is_active():
            extension_types_batch = extension_types_sorter.get_ready()
            extensions_batch = []
            for extension_type in extension_types_batch:
                if issubclass(extension_type, ConfigurableExtension):
                    if extension_type not in extension_types_enabled_in_configuration or self._configuration.extensions[extension_type].extension_type_configuration is None:
                        configuration = extension_type.default_configuration()
                    else:
                        configuration = self._configuration.extensions[extension_type].extension_type_configuration
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
        if len(self._assets.paths) == 0:
            self._assets.paths.appendleft((Path(__file__).resolve().parent / 'assets', 'utf-8'))
            for extension in self.extensions.flatten():
                if extension.assets_directory_path is not None:
                    self._assets.paths.appendleft((extension.assets_directory_path, 'utf-8'))
            if self._configuration.assets_directory_path:
                self._assets.paths.appendleft((self._configuration.assets_directory_path, None))

        return self._assets

    @assets.deleter
    def assets(self) -> None:
        self._assets.paths.clear()

    @property
    def dispatcher(self) -> Dispatcher:
        if self._dispatcher is None:
            from betty.extension import ExtensionDispatcher

            self._dispatcher = ExtensionDispatcher(self.extensions)

        return self._dispatcher

    @property
    def localized_url_generator(self) -> LocalizedUrlGenerator:
        return self._localized_url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        return self._static_url_generator

    @reactive
    @property
    def translations(self) -> Dict[str, NullTranslations]:
        if len(self._translations) == 0:
            self._translations['en-US'] = NullTranslations()
            for locale_configuration in self._configuration.locales:
                for assets_path, _ in reversed(self._assets.paths):
                    translations = open_translations(locale_configuration.locale, assets_path)
                    if translations:
                        translations.add_fallback(self._translations[locale_configuration])
                        self._translations[locale_configuration] = translations

        return self._translations

    @translations.deleter
    def translations(self) -> None:
        self._translations.clear()

    @reactive
    @property
    def jinja2_environment(self) -> Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import BettyEnvironment
            self._jinja2_environment = BettyEnvironment(self)

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
                Jinja2Renderer(self.jinja2_environment, self._configuration),
            ])

        return self._renderer

    @renderer.deleter
    def renderer(self) -> None:
        self._renderer = None

    @property
    def executor(self) -> Executor:
        if self._executor is None:
            self._executor = ExceptionRaisingExecutor(ThreadPoolExecutor())
        return self._executor

    @executor.deleter
    def executor(self) -> None:
        if self._executor is not None:
            self._executor.shutdown()
            self._executor = None

    @property
    def locks(self) -> Locks:
        return self._locks

    @reactive
    @property
    def http_client(self) -> aiohttp.ClientSession:
        if self._http_client is None:
            self._http_client = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=5))
        return self._http_client

    @http_client.deleter
    def http_client(self) -> None:
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    @asynccontextmanager
    async def with_locale(self, locale: str) -> App:
        """
        Temporarily change this application's locale and the global gettext translations.
        """
        locale = negotiate_locale(locale, [locale_configuration.locale for locale_configuration in self.configuration.locales])

        if locale is None:
            raise ValueError('Locale "%s" is not enabled.' % locale)

        previous_locale = self._locale
        if locale == previous_locale:
            yield self
            return
        await self._wait_for_threads()

        self._locale = locale
        with Translations(self.translations[locale]):
            self.react.getattr('locale').react.trigger()
            yield self
            await self._wait_for_threads()

        self._locale = previous_locale
        self.react.getattr('locale').react.trigger()

    @asynccontextmanager
    async def with_debug(self, debug: bool) -> App:
        previous_debug = self.debug
        if debug == previous_debug:
            yield self
            return
        await self._wait_for_threads()

        self._debug = debug
        self.react.getattr('debug').react.trigger()
        yield self
        await self._wait_for_threads()

        self._debug = previous_debug
        self.react.getattr('debug').react.trigger()
