"""
Provide the project API.

Projects are how people use Betty. A project is a workspace, starting out with the user's configuration,
and combining it with the resulting ancestry, allowing the user to perform tasks, such as generating a
site from the entire project.
"""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Self, final, overload

from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import TypeVar, override

import betty
import betty.dirs
from betty.ancestry import Ancestry
from betty.asset import AssetRepository, ProxyAssetRepository, StaticAssetRepository
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.document import Document, DocumentProvider
from betty.extension import Extension, ExtensionDefinition
from betty.hashid import hashid
from betty.importlib import fully_qualified_name
from betty.license import LicenseDefinition
from betty.locale.localizable.gettext import _
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    ProxyTranslationRepository,
    TranslationRepository,
)
from betty.plugin import PluginDefinition, ResolvableId, resolve_id
from betty.plugin.dependent import sort_dependent_plugin_graph
from betty.privacy.privatizer import Privatizer
from betty.project.data import ProjectConfiguration
from betty.render import RenderDispatcher, RendererDefinition
from betty.serde import SerializerDefinition, serializer_for
from betty.service.container import service
from betty.service.factory import DataManufacturable
from betty.service.level import UNIVERSE, ServiceLevel
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Collection,
        Iterator,
        MutableSequence,
        Sequence,
    )

    from babel import Locale

    from betty.app import App
    from betty.jinja2 import Environment
    from betty.license import License
    from betty.machine_name import MachineName
    from betty.url import UrlGenerator

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class Project(DataManufacturable[ProjectConfiguration], ServiceLevel):
    """
    Define a Betty project.

    A project combines project configuration and the resulting ancestry.

    .. list-table::
       :widths: 10 20
       :header-rows: 0

       * - Configuration
         - :py:class:`betty.project.data.ProjectConfiguration`
    """

    def __init__(
        self,
        app: App,
        configuration_file: Path,
        /,
        *,
        configuration: ProjectConfiguration,
        ancestry: Ancestry | None = None,
    ):
        super().__init__()
        self.life_cycle.on_bootstrap(
            lambda: self._configuration.data().hydrate(self, self._configuration)
        )
        self._app = app
        self._configuration = configuration
        self._configuration_file = configuration_file
        self._ancestry = Ancestry() if ancestry is None else ancestry

    @override
    @classmethod
    def new_data_cls(cls) -> type[ProjectConfiguration]:
        return ProjectConfiguration

    @override
    @classmethod
    async def new(cls, services: ServiceLevel, data: ProjectConfiguration, /) -> Self:
        raise NotImplementedError(
            f"Creating a new {fully_qualified_name(cls)} from its configuration is not yet supported."
        )

    @property
    def configuration(self) -> ProjectConfiguration:
        """
        The project configuration.
        """
        return self._configuration

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        app: App,
        *,
        ancestry: Ancestry | None = None,
        configuration: ProjectConfiguration | None = None,
        configuration_file: Path | None = None,
    ) -> AsyncIterator[Self]:
        """
        Creat a new, isolated, temporary project.

        The project will not leave any traces on the system, except when it uses
        global Betty functionality such as caches.
        """
        async with AsyncExitStack() as stack:
            if configuration_file is None:
                configuration_file = (
                    Path(await stack.enter_async_context(TemporaryDirectory()))
                    / "betty.json"
                )
            yield cls(
                app,
                configuration_file,
                configuration=ProjectConfiguration(
                    title="Betty", url="https://example.com"
                )
                if configuration is None
                else configuration,
                ancestry=ancestry,
            )

    @property
    def configuration_file(self) -> Path:
        """
        The path to the configuration's file.
        """
        return self._configuration_file

    async def set_configuration_file(self, configuration_file: Path, /) -> None:
        """
        Set the path to the configuration's file.
        """
        if configuration_file == self._configuration_file:
            return
        serializer_for(
            list(await UNIVERSE.plugins.plugins(SerializerDefinition)),
            configuration_file.suffix,
        )
        self._configuration_file = configuration_file

    @property
    def directory(self) -> Path:
        """
        The project directory path.

        Betty will look for resources in this directory, and place generated artifacts there. It is expected
        that no other applications or projects share this same directory.
        """
        return self.configuration_file.parent

    @property
    def output_directory(self) -> Path:
        """
        The output directory path.
        """
        return self.directory / "output"

    @property
    def assets_directory(self) -> Path:
        """
        The :doc:`assets directory path </usage/assets>`.
        """
        return self.directory / "assets"

    @property
    def www_directory(self) -> Path:
        """
        The WWW directory path.
        """
        return self.output_directory / "www"

    def localize_www_directory(self, locale: Locale) -> Path:
        """
        Get the WWW directory path for a locale.
        """
        if self.configuration.multilingual:
            return self.www_directory / self.configuration.locales[locale].slug
        return self.www_directory

    @property
    def app(self) -> App:
        """
        The application this project is run within.
        """
        return self._app

    @property
    def name(self) -> MachineName:
        """
        The project name.

        If no project name was configured, this defaults to the hash of the configuration file path.
        """
        if self._configuration.name is None:
            return hashid(str(self.configuration_file))
        return self._configuration.name

    @property
    def ancestry(self) -> Ancestry:
        """
        The project's ancestry.
        """
        return self._ancestry

    @service
    async def _project_assets(self) -> AssetRepository:
        asset_paths = [self.assets_directory]
        extensions = await self.extensions
        for project_extension in extensions.flatten():
            extension_assets_directory_path = (
                project_extension.plugin().assets_directory
            )
            if extension_assets_directory_path is not None:
                asset_paths.append(extension_assets_directory_path)
        return StaticAssetRepository(*asset_paths)

    @service
    async def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        return ProxyAssetRepository(await self._project_assets, self.app.assets)

    @service
    async def translations(self) -> TranslationRepository:
        """
        The available translations.
        """
        return ProxyTranslationRepository(
            AssetTranslationRepository(
                await self._project_assets, self.app.binary_file_cache
            ),
            await self.app.translations,
        )

    @service
    async def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        return LocalizerRepository(await self.translations)

    @service
    async def public_localizers(self) -> Collection[Localizer]:
        """
        The public localizers.
        """
        localizers = await self.localizers
        return [localizers.get(locale) for locale in self.configuration.locales.keys()]  # noqa: SIM118

    @service
    async def url_generator(self) -> UrlGenerator:
        """
        The URL generator.
        """
        from betty.project.url import new_project_url_generator

        return await new_project_url_generator(self)

    @service
    async def jinja(self) -> Environment:
        """
        The Jinja2 environment.
        """
        from betty.jinja2 import Environment

        return await Environment.new(self)

    @service
    async def renderer(self) -> RenderDispatcher:
        """
        The  content renderer.
        """
        return RenderDispatcher(
            *[
                await self.factory.new(plugin.cls)
                for plugin in await self.plugins.plugins(RendererDefinition)
            ]
        )

    @service
    async def extensions(self) -> ProjectExtensions:
        """
        The enabled extensions.
        """
        extensions = await self.plugins.plugins(ExtensionDefinition)
        configured_extension_definitions = []
        configured_extension_configurations = {}
        for extension_configuration in self.configuration.extensions:
            configured_extension_definitions.append(
                extensions[extension_configuration.id]
            )
            configured_extension_configurations[extension_configuration.id] = (
                extension_configuration
            )

        extensions_sorter = await sort_dependent_plugin_graph(
            extensions, configured_extension_definitions
        )
        extensions_sorter.prepare()

        theme_count = 0
        enabled_extensions = []
        while extensions_sorter.is_active():
            enabled_extension_ids_batch = extensions_sorter.get_ready()
            enabled_extension_batch: MutableSequence[Extension] = []
            for enabled_extension_id in enabled_extension_ids_batch:
                enabled_extension_definition = extensions[enabled_extension_id]
                if enabled_extension_definition.theme:
                    theme_count += 1
                if enabled_extension_id in configured_extension_configurations:
                    extension = await configured_extension_configurations[
                        enabled_extension_id
                    ].new_plugin(self, ExtensionDefinition)
                else:
                    extension = await self.factory.new(enabled_extension_definition.cls)
                await extension.bootstrap()
                enabled_extension_batch.append(extension)
                extensions_sorter.done(enabled_extension_id)
            self.life_cycle.attach(*enabled_extension_batch)
            enabled_extensions.append(
                sorted(
                    enabled_extension_batch,
                    key=lambda extension: extension.plugin().id,
                )
            )
        initialized_extensions = ProjectExtensions(enabled_extensions)

        # Users may not realize no theme is enabled, and be confused by their site looking bare.
        # Warn them out of courtesy.
        if theme_count == 0:
            await self.app.user.message_warning(
                _(
                    'Your project has no theme enabled. This means your site\'s pages may look bare. Try the "raspberry-mint" extension.'
                )
            )

        return initialized_extensions

    @property
    def logo(self) -> Path:
        """
        The path to the logo file.
        """
        return (
            self._configuration.logo
            or betty.dirs.ASSETS_DIRECTORY_PATH
            / "public"
            / "static"
            / "betty-512x512.png"
        )

    @service
    async def copyright_notice(self) -> CopyrightNotice:
        """
        The overall project copyright.
        """
        return await self.configuration.copyright_notice.new_plugin(
            self, CopyrightNoticeDefinition
        )

    @service
    async def license(self) -> License:
        """
        The overall project license.
        """
        return await self.configuration.license.new_plugin(self, LicenseDefinition)

    @service
    def privatizer(self) -> Privatizer:
        """
        The privatizer.
        """
        return Privatizer(self.configuration.lifetime_threshold, user=self.app.user)

    async def new_document(
        self,
        resource: object = None,
        resource_url: object = None,
        **kwargs: object,
    ) -> Document:
        """
        Create a new document.
        """
        extensions = await self.extensions
        return Document(
            resource,
            resource_url,
            **{
                key: value
                for extension in extensions.flatten()
                if isinstance(extension, DocumentProvider)
                for (key, value) in extension.new_document_vars().items()
            },
            **kwargs,
        )


_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


@internal
@final
class ProjectExtensions:
    """
    Manage the extensions running within the :py:class:`betty.project.Project`.
    """

    def __init__(self, project_extensions: Sequence[Sequence[Extension]]):
        super().__init__()
        self._project_extensions = project_extensions

    @overload
    def __getitem__(self, extension: type[_ExtensionT]) -> _ExtensionT:
        pass

    @overload
    def __getitem__(self, extension: ResolvableId[ExtensionDefinition]) -> Extension:
        pass

    def __getitem__(self, extension: ResolvableId[ExtensionDefinition]) -> Extension:
        extension_id = resolve_id(extension)
        for project_extension in self.flatten():
            if project_extension.plugin().id == extension_id:
                return project_extension
        raise KeyError(f'Unknown extension of type "{extension_id}"')

    def __iter__(self) -> Iterator[Iterator[Extension]]:
        """
        Iterate over all extensions, in topologically sorted batches.

        Each item is a batch of extensions. Items are ordered because later items depend
        on earlier items. The extensions in each item do not depend on each other and their
        order has no meaning. However, implementations SHOULD sort the extensions in each
        item in a stable fashion for reproducability.
        """
        # Use a generator so we discourage calling code from storing the result.
        for batch in self._project_extensions:
            yield (project_extension for project_extension in batch)

    def flatten(self) -> Iterator[Extension]:
        """
        Get a sequence of topologically sorted extensions.
        """
        for batch in self:
            yield from batch

    def __contains__(self, extension: ResolvableId[ExtensionDefinition]) -> bool:
        if isinstance(extension, type) and issubclass(extension, Extension):
            extension = extension.plugin()
        try:
            self[resolve_id(extension)]
        except KeyError:
            return False
        else:
            return True
