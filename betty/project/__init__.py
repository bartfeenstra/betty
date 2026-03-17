"""
Provide the project API.

Projects are how people use Betty. A project is a workspace, starting out with the user's configuration,
and combining it with the resulting ancestry, allowing the user to perform tasks, such as generating a
site from the entire project.
"""

from __future__ import annotations

from asyncio import gather
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Self, final, override

from aiofiles.tempfile import TemporaryDirectory

import betty
import betty.dirs
from betty.ancestry import Ancestry
from betty.app import App
from betty.asset import (
    AssetDefinition,
    AssetManufacturer,
    AssetRepository,
    ProxyAssetRepository,
    StaticAssetRepository,
)
from betty.document import Document, DocumentProvider
from betty.extension import Extension, ExtensionDefinition
from betty.hashid import hashid
from betty.html.css import CssResourceDefinition
from betty.html.js import JsResourceDefinition
from betty.importlib import fully_qualified_name
from betty.jinja.filter import JinjaFilterDefinition
from betty.jinja.test import JinjaTestDefinition
from betty.link import LinkDefinition
from betty.locale import DEFAULT_LOCALE
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    ProxyTranslationRepository,
    TranslationRepository,
)
from betty.machine_name import MachineName
from betty.privacy.privatizer import Privatizer
from betty.project.data import ProjectConfiguration
from betty.render import RenderDispatcher, RendererDefinition
from betty.serde import SerializerDefinition, serializer_for
from betty.service.factory import DataManufacturable
from betty.service.level import ChainedServiceLevel, ServiceLevel
from betty.service.level.universe import UNIVERSE
from betty.service.plugin import ServicePluginManager, ServicePluginProvider
from betty.service.provider import service
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Collection, Iterable, Mapping

    from babel import Locale

    from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
    from betty.event_type import EventTypeDefinition
    from betty.gender import GenderDefinition
    from betty.jinja import Environment
    from betty.license import License, LicenseDefinition
    from betty.place_type import PlaceTypeDefinition
    from betty.plugin import PluginDefinition
    from betty.plugin.data import PluginDefinitionConfiguration
    from betty.plugin.discovery import ResolvableDiscovery
    from betty.role import RoleDefinition
    from betty.service.plugin import PluginCollection
    from betty.url import UrlGenerator


@final
class Project(
    DataManufacturable[ProjectConfiguration],
    ChainedServiceLevel[App],
    ServicePluginProvider,
):
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
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
    ):
        super().__init__(plugins=plugins, upstream=app)
        self.life_cycle.on_bootstrap(self._ensure_locale)
        self.life_cycle.on_bootstrap(self._validate)
        self._app = app
        self._configuration = configuration
        self._configuration_file = configuration_file
        self._ancestry = Ancestry() if ancestry is None else ancestry

    def _ensure_locale(self) -> None:
        if not self._configuration.locales:
            self._configuration.locales.add(DEFAULT_LOCALE)

    async def _validate(self) -> None:
        for entity_type in self._configuration.entity_types:
            await entity_type.validate(self)

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
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
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
                plugins=plugins,
            )

    @override
    @service
    async def service_plugins(self) -> ServicePluginManager:
        service_plugins = ServicePluginManager(
            {
                AssetDefinition: [AssetManufacturer("project")],
                CssResourceDefinition: [],
                ExtensionDefinition: self.configuration.extensions,
                JinjaFilterDefinition: [],
                JinjaTestDefinition: [],
                JsResourceDefinition: [],
                LinkDefinition: [],
            },
            services=self,
        )
        await service_plugins.bootstrap()
        self.life_cycle.attach(service_plugins)
        return service_plugins

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
            [plugin async for plugin in UNIVERSE.plugins[SerializerDefinition]],
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
    def name(self) -> MachineName:
        """
        The project name.

        If no project name was configured, this defaults to the hash of the configuration file path.
        """
        if self._configuration.name is None:
            return MachineName(hashid(str(self.configuration_file)))
        return self._configuration.name

    @property
    def ancestry(self) -> Ancestry:
        """
        The project's ancestry.
        """
        return self._ancestry

    @service
    async def _project_assets(self) -> AssetRepository:
        return StaticAssetRepository(
            *(
                asset.plugin().assets
                for asset in (await self.service_plugins)[AssetDefinition]
            )
        )

    @service
    async def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        return ProxyAssetRepository(
            *await gather(self._project_assets, self.upstream.assets)
        )

    @service
    async def translations(self) -> TranslationRepository:
        """
        The available translations.
        """
        return ProxyTranslationRepository(
            AssetTranslationRepository(
                await self._project_assets, self.upstream.binary_file_cache
            ),
            await self.upstream.translations,
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
        from betty.jinja import new_environment

        return await new_environment(self)

    @service
    async def renderer(self) -> RenderDispatcher:
        """
        The  content renderer.
        """
        return RenderDispatcher(
            *[
                await self.factory.new(plugin.cls)
                async for plugin in self.plugins[RendererDefinition]
            ]
        )

    @property
    async def extensions(self) -> PluginCollection[ExtensionDefinition, Extension]:
        """
        The enabled extensions.
        """
        return (await self.service_plugins)[ExtensionDefinition]

    @property
    def logo(self) -> Path:
        """
        The path to the logo file.
        """
        return (
            self._configuration.logo
            or betty.dirs.ASSETS_DIRECTORY_PATH
            / "universe"
            / "public"
            / "static"
            / "betty-512x512.png"
        )

    @service
    async def copyright_notice(self) -> CopyrightNotice:
        """
        The overall project copyright.
        """
        return await self.factory.new(self.configuration.copyright_notice)

    @service
    async def license(self) -> License:
        """
        The overall project license.
        """
        return await self.factory.new(self.configuration.license)

    @service
    def privatizer(self) -> Privatizer:
        """
        The privatizer.
        """
        return Privatizer(
            self.configuration.lifetime_threshold, user=self.upstream.user
        )

    async def new_document(
        self,
        resource: object = None,
        resource_url: object = None,
        **kwargs: object,
    ) -> Document:
        """
        Create a new document.
        """
        return Document(
            resource,
            resource_url,
            **{
                key: value
                for extension in await self.extensions
                if isinstance(extension, DocumentProvider)
                for (key, value) in extension.new_document_vars().items()
            },
            **kwargs,
        )


def _discover[PluginDefinitionT: PluginDefinition](
    plugins: Iterable[PluginDefinitionConfiguration[PluginDefinitionT]],
) -> Iterable[PluginDefinitionT]:
    for plugin in plugins:
        yield plugin.new_plugin()


@require_project
def _discover_copyright_notices(
    project: Project,
) -> Iterable[CopyrightNoticeDefinition]:
    return _discover(project.configuration.copyright_notices)


@require_project
def _discover_event_types(project: Project) -> Iterable[EventTypeDefinition]:
    return _discover(project.configuration.event_types)


@require_project
def _discover_genders(project: Project) -> Iterable[GenderDefinition]:
    return _discover(project.configuration.genders)


@require_project
def _discover_licenses(project: Project) -> Iterable[LicenseDefinition]:
    return _discover(project.configuration.licenses)


@require_project
def _discover_place_types(project: Project) -> Iterable[PlaceTypeDefinition]:
    return _discover(project.configuration.place_types)


@require_project
def _discover_roles(project: Project) -> Iterable[RoleDefinition]:
    return _discover(project.configuration.roles)
