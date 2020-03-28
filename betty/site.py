import gettext
from collections import defaultdict, OrderedDict
from contextlib import AsyncExitStack
from copy import copy
from os.path import abspath, dirname, join
from typing import Type, Dict

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.event import EventDispatcher
from betty.fs import FileSystem
from betty.graph import tsort, Graph
from betty.locale import open_translations, Translations, negotiate_locale
from betty.url import SiteUrlGenerator, StaticPathUrlGenerator, LocalizedUrlGenerator, StaticUrlGenerator


class Site:
    def __init__(self, configuration: Configuration):
        self._site_stack = []
        self._ancestry = Ancestry()
        self._configuration = configuration
        self._resources = FileSystem(
            join(dirname(abspath(__file__)), 'resources'))
        self._event_dispatcher = EventDispatcher()
        self._localized_url_generator = SiteUrlGenerator(configuration)
        self._static_url_generator = StaticPathUrlGenerator(configuration)
        self._locale = None
        self._translations = defaultdict(gettext.NullTranslations)
        self._default_translations = None
        self._plugins = OrderedDict()
        self._plugin_exit_stack = AsyncExitStack()
        self._init_plugins()
        self._init_event_listeners()
        self._init_resources()
        self._init_translations()

    async def __aenter__(self):
        if not self._site_stack:
            for plugin in self._plugins.values():
                await self._plugin_exit_stack.enter_async_context(plugin)

        self._default_translations = Translations(self.translations[self.locale])
        self._default_translations.install()

        self._site_stack.append(self)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._site_stack.pop()

        self._default_translations.uninstall()

        if not self._site_stack:
            await self._plugin_exit_stack.aclose()

    @property
    def locale(self) -> str:
        if self._locale is not None:
            return self._locale
        return self._configuration.default_locale

    def _init_plugins(self) -> None:
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
        for plugin_type in self._configuration.plugins.keys():
            _extend_plugin_type_graph(plugin_types_graph, plugin_type)
        # Now all dependencies have been collected, extend the graph with optional plugin orders.
        for plugin_type in self._configuration.plugins.keys():
            for before in plugin_type.comes_before():
                if before in plugin_types_graph:
                    plugin_types_graph[plugin_type].add(before)
            for after in plugin_type.comes_after():
                if after in plugin_types_graph:
                    plugin_types_graph[after].add(plugin_type)

        for plugin_type in tsort(plugin_types_graph):
            plugin_configuration = self.configuration.plugins[
                plugin_type] if plugin_type in self.configuration.plugins else {}
            plugin = plugin_type.from_configuration_dict(
                self, plugin_configuration)
            self._plugins[plugin_type] = plugin

    def _init_event_listeners(self) -> None:
        for plugin in self._plugins.values():
            for event_name, listener in plugin.subscribes_to():
                self._event_dispatcher.add_listener(event_name, listener)

    def _init_resources(self) -> None:
        for plugin in self._plugins.values():
            if plugin.resource_directory_path is not None:
                self._resources.paths.appendleft(
                    plugin.resource_directory_path)
        if self._configuration.resources_directory_path:
            self._resources.paths.appendleft(
                self._configuration.resources_directory_path)

    def _init_translations(self) -> None:
        self._translations['en-US'] = gettext.NullTranslations()
        for locale in self._configuration.locales:
            for resources_path in reversed(self._resources.paths):
                translations = open_translations(locale, resources_path)
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
    def plugins(self) -> Dict:
        return self._plugins

    @property
    def resources(self) -> FileSystem:
        return self._resources

    @property
    def event_dispatcher(self) -> EventDispatcher:
        return self._event_dispatcher

    @property
    def localized_url_generator(self) -> LocalizedUrlGenerator:
        return self._localized_url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        return self._static_url_generator

    @property
    def translations(self) -> Dict[str, gettext.NullTranslations]:
        return self._translations

    def with_locale(self, locale: str) -> 'Site':
        locale = negotiate_locale(locale, list(self.configuration.locales.keys()))
        if locale is None:
            raise ValueError('Locale "%s" is not enabled.' % locale)
        if locale == self.locale:
            return self

        site = copy(self)
        site._locale = locale
        return site
