import gettext
from collections import defaultdict, OrderedDict
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor

from jinja2 import Environment

from betty.concurrent import ExceptionRaisingExecutor
from betty.dispatch import Dispatcher
from betty.extension import Extension, build_extension_type_graph, ConfigurableExtension
from betty.lock import Locks
from betty.render import Renderer, SequentialRenderer

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
from betty.graph import tsort_grouped
from betty.locale import open_translations, Translations, negotiate_locale
from betty.url import AppUrlGenerator, StaticPathUrlGenerator, LocalizedUrlGenerator, StaticUrlGenerator


class App:
    def __init__(self, configuration: Configuration):
        self._app_stack = []
        self._ancestry = Ancestry()
        self._configuration = configuration
        self._assets = FileSystem(
            join(dirname(abspath(__file__)), 'assets'))
        self._dispatcher = None
        self._localized_url_generator = AppUrlGenerator(configuration)
        self._static_url_generator = StaticPathUrlGenerator(configuration)
        self._locale = None
        self._translations = defaultdict(gettext.NullTranslations)
        self._default_translations = None
        self._extensions = OrderedDict()
        self._extension_exit_stack = AsyncExitStack()
        self._init_extensions()
        self._init_dispatcher()
        self._init_assets()
        self._init_translations()
        self._jinja2_environment = None
        self._renderer = None
        self._executor = None
        self._locks = Locks()

    async def enter(self):
        if not self._app_stack:
            for extension in self._extensions.values():
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
            await self._extension_exit_stack.aclose()

    async def __aenter__(self) -> 'App':
        return await self.enter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exit()

    @property
    def locale(self) -> str:
        if self._locale is not None:
            return self._locale
        return self._configuration.default_locale

    def _init_extensions(self) -> None:
        for grouped_extension_types in tsort_grouped(build_extension_type_graph(set(self._configuration.extensions.keys()))):
            for extension_type in grouped_extension_types:
                extension_args = []
                if issubclass(extension_type, ConfigurableExtension) and extension_type in self.configuration.extensions:
                    extension_kwargs = self.configuration.extensions[extension_type]
                else:
                    extension_kwargs = {}

                if issubclass(extension_type, AppAwareFactory):
                    extension = extension_type.new_for_app(self, *extension_args, **extension_kwargs)
                else:
                    extension = extension_type(*extension_args, **extension_kwargs)

                self._extensions[extension_type] = extension

    def _init_dispatcher(self) -> None:
        from betty.extension import ExtensionDispatcher

        self._dispatcher = ExtensionDispatcher(self._extensions.values())

    def _init_assets(self) -> None:
        for extension in self._extensions.values():
            if extension.assets_directory_path is not None:
                self._assets.paths.appendleft(
                    extension.assets_directory_path)
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
    def extensions(self) -> Dict[Type[Extension], Extension]:
        return self._extensions

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

    def with_locale(self, locale: str) -> 'App':
        locale = negotiate_locale(locale, list(self.configuration.locales.keys()))
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


class AppAwareFactory:
    @classmethod
    def new_for_app(cls, app: App, *args, **kwargs):
        """
        Create a new instance of cls based on a Betty app.

        Parameters
        ----------
        betty.app.App
            The Betty app.
        *args
            Any additional arguments passed on to cls.__init__().
        *kwargs
            Any additional keyword arguments passed on to cls.__init__().

        Returns
        -------
        cls
        """

        raise NotImplementedError
