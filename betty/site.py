import gettext
from collections import defaultdict, OrderedDict
from concurrent.futures._base import Executor
from concurrent.futures.process import ProcessPoolExecutor

from jinja2 import Environment

from betty.concurrent import ExceptionRaisingExecutor
from betty.dispatch import Dispatcher
from betty.lock import Locks
from betty.render import Renderer, SequentialRenderer
from betty.sass import SassRenderer

try:
    from contextlib import AsyncExitStack
except ImportError:
    from async_exit_stack import AsyncExitStack
from copy import copy
from os.path import abspath, dirname, join
from typing import Type, Dict

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.fs import FileSystem
from betty.graph import tsort, Graph
from betty.locale import open_translations, Translations, negotiate_locale
from betty.url import SiteUrlGenerator, StaticPathUrlGenerator, LocalizedUrlGenerator, StaticUrlGenerator


class Site:
    def __init__(self, configuration: Configuration):
        self._site_stack = []
        self._ancestry = Ancestry()
        self._configuration = configuration
        self._assets = FileSystem(
            join(dirname(abspath(__file__)), 'assets'))
        self._dispatcher = Dispatcher()
        self._localized_url_generator = SiteUrlGenerator(configuration)
        self._static_url_generator = StaticPathUrlGenerator(configuration)
        self._locale = None
        self._translations = defaultdict(gettext.NullTranslations)
        self._default_translations = None
        self._plugins = OrderedDict()
        self._plugin_exit_stack = AsyncExitStack()
        self._init_plugins()
        self._init_dispatch_handlers()
        self._init_assets()
        self._init_translations()
        self._jinja2_environment = None
        self._renderer = None
        self._executor = None
        self._locks = Locks()

    async def enter(self):
        if not self._site_stack:
            for plugin in self._plugins.values():
                await self._plugin_exit_stack.enter_async_context(plugin)

        self._default_translations = Translations(self.translations[self.locale])
        self._default_translations.install()

        if self._executor is None:
            self._executor = ExceptionRaisingExecutor(ProcessPoolExecutor())

        self._site_stack.append(self)

        return self

    async def exit(self):
        self._site_stack.pop()

        self._default_translations.uninstall()

        if not self._site_stack:
            self._executor.shutdown()
            self._executor = None
            await self._plugin_exit_stack.aclose()

    async def __aenter__(self) -> 'Site':
        return await self.enter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exit()

    @property
    def locale(self) -> str:
        if self._locale is not None:
            return self._locale
        return self._configuration.default_locale

    def _init_plugins(self) -> None:
        from betty.plugin import NO_CONFIGURATION

        def _extend_plugin_type_graph(graph: Graph, plugin_type: Type['Plugin']):
            dependencies = plugin_type.depends_on()
            # Ensure each plugin type appears in the graph, even if they're isolated.
            graph.setdefault(plugin_type, set())
            for dependency in dependencies:
                seen_dependency = dependency in graph
                graph[dependency].add(plugin_type)
                if not seen_dependency:
                    _extend_plugin_type_graph(graph, dependency)

        plugin_types_graph = defaultdict(set)
        # Add dependencies to the plugin graph.
        for plugin_type, _ in self._configuration.plugins:
            _extend_plugin_type_graph(plugin_types_graph, plugin_type)
        # Now all dependencies have been collected, extend the graph with optional plugin orders.
        for plugin_type, _ in self._configuration.plugins:
            for before in plugin_type.comes_before():
                if before in plugin_types_graph:
                    plugin_types_graph[plugin_type].add(before)
            for after in plugin_type.comes_after():
                if after in plugin_types_graph:
                    plugin_types_graph[after].add(plugin_type)

        for plugin_type in tsort(plugin_types_graph):
            plugin_configuration = self.configuration.plugins[
                plugin_type] if plugin_type in self.configuration.plugins else NO_CONFIGURATION
            plugin = plugin_type.for_site(
                self, plugin_configuration)
            self._plugins[plugin_type] = plugin

    def _init_dispatch_handlers(self) -> None:
        for plugin in self._plugins.values():
            self._dispatcher.append_handler(plugin)

    def _init_assets(self) -> None:
        for plugin in self._plugins.values():
            if plugin.assets_directory_path is not None:
                self._assets.paths.appendleft(
                    plugin.assets_directory_path)
        if self._configuration.assets_directory_path:
            self._assets.paths.appendleft(
                self._configuration.assets_directory_path)

    def _init_translations(self) -> None:
        self._translations['en-US'] = gettext.NullTranslations()
        for locale in self._configuration.locales:
            for assets_path in reversed(self._assets.paths):
                translations = open_translations(locale, assets_path)
                if translations:
                    translations.add_fallback(self._translations[locale])
                    self._translations[locale] = translations

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry

    @property
    def configuration(self) -> Configuration:
        return self._configuration

    @property
    def plugins(self) -> Dict[Type['Plugin'], 'Plugin']:
        return self._plugins

    @property
    def assets(self) -> FileSystem:
        return self._assets

    @property
    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @property
    def localized_url_generator(self) -> LocalizedUrlGenerator:
        return self._localized_url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        return self._static_url_generator

    @property
    def translations(self) -> Dict[str, gettext.NullTranslations]:
        return self._translations

    @property
    def jinja2_environment(self) -> Environment:
        if not self._jinja2_environment:
            from betty.jinja2 import BettyEnvironment
            self._jinja2_environment = BettyEnvironment(self)

        return self._jinja2_environment

    @property
    def renderer(self) -> Renderer:
        if not self._renderer:
            from betty.jinja2 import Jinja2Renderer
            self._renderer = SequentialRenderer([
                Jinja2Renderer(self.jinja2_environment, self._configuration),
                SassRenderer(),
            ])

        return self._renderer

    @property
    def executor(self) -> Executor:
        if self._executor is None:
            raise RuntimeError("Cannot get the executor before this site's context is entered.")
        return self._executor

    @property
    def locks(self) -> Locks:
        return self._locks

    def with_locale(self, locale: str) -> 'Site':
        locale = negotiate_locale(locale, list(self.configuration.locales.keys()))
        if locale is None:
            raise ValueError('Locale "%s" is not enabled.' % locale)
        if locale == self.locale:
            return self

        site = copy(self)
        site._locale = locale

        # Clear all locale-dependent lazy-loaded attributes.
        site._jinja2_environment = None
        site._renderer = None

        return site
