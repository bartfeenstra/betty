"""
Provide the project API.

Projects are how people use Betty. A project is a workspace, starting out with the user's configuration,
and combining it with the resulting ancestry, allowing the user to perform tasks, such as generating a
site from the entire project.
"""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, cast, final, overload

from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import TypeVar, override

import betty
import betty.dirs
from betty.ancestry import Ancestry
from betty.app.factory import AppTarget
from betty.asset import AssetRepository, ProxyAssetRepository, StaticAssetRepository
from betty.config import Configurable
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.hashid import hashid
from betty.job import Context as JobContext
from betty.license import LicenseDefinition
from betty.locale.localizable.gettext import _
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    ProxyTranslationRepository,
    TranslationRepository,
)
from betty.model import Entity
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.dependent import sort_dependent_plugin_graph
from betty.plugin.repository.provider import PluginRepositoryProvider
from betty.plugin.repository.provider.service import (
    ServiceLevelPluginRepositoryProvider,
    plugins,
)
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.privacy.privatizer import Privatizer
from betty.project.config import ProjectConfiguration
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.factory import ProjectDependentFactory, ProjectDependentSelfFactory
from betty.project.url import new_project_url_generator
from betty.render import RenderDispatcher, RendererDefinition
from betty.requirement import Requirement, StaticRequirement
from betty.resource import Context, ContextProvider
from betty.resource import Context as ResourceContext
from betty.serde.format import FormatDefinition, format_for
from betty.service.container import ServiceContainer, service
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
    from betty.cache import Cache
    from betty.jinja2 import Environment
    from betty.license import License
    from betty.locale.localizable import LocalizableLike
    from betty.machine_name import MachineName
    from betty.plugin.repository import PluginRepository
    from betty.progress import Progress
    from betty.service.level import ServiceLevel
    from betty.service.level.factory import AnyFactoryTarget
    from betty.url import UrlGenerator

_T = TypeVar("_T")
_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)
_EntityT = TypeVar("_EntityT", bound=Entity)

_ProjectDependentT = TypeVar("_ProjectDependentT")


@final
class Project(
    Configurable[ProjectConfiguration], ServiceContainer, PluginRepositoryProvider
):
    """
    Define a Betty project.

    A project combines project configuration and the resulting ancestry.
    """

    def __init__(
        self,
        app: App,
        configuration_file_path: Path,
        /,
        *,
        ancestry: Ancestry | None = None,
        configuration: ProjectConfiguration | None = None,
    ):
        super().__init__(
            configuration=ProjectConfiguration()
            if configuration is None
            else configuration
        )
        self._app = app
        self._configuration_file_path = configuration_file_path
        self._ancestry = Ancestry() if ancestry is None else ancestry
        self._plugin_repository_provider = ServiceLevelPluginRepositoryProvider(self)

    @override
    @classmethod
    def configuration_cls(cls) -> type[ProjectConfiguration]:
        return ProjectConfiguration

    @override
    @classmethod
    async def requires(
        cls, services: ServiceLevel, subject: LocalizableLike, /
    ) -> Requirement | Self:
        if not isinstance(services, cls):
            return StaticRequirement(
                _("{subject} requires a project.").format(subject=subject)
            )
        return services

    @override
    async def plugins(
        self,
        plugin_type: type[_PluginDefinitionT] | MachineName,
        *,
        check_requirements: bool = True,
    ) -> PluginRepository[_PluginDefinitionT]:
        return await self._plugin_repository_provider.plugins(
            plugin_type, check_requirements=check_requirements
        )

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        app: App,
        *,
        ancestry: Ancestry | None = None,
        configuration: ProjectConfiguration | None = None,
        configuration_file_path: Path | None = None,
    ) -> AsyncIterator[Self]:
        """
        Creat a new, isolated, temporary project.

        The project will not leave any traces on the system, except when it uses
        global Betty functionality such as caches.
        """
        async with AsyncExitStack() as stack:
            if configuration_file_path is None:
                configuration_file_path = (
                    Path(await stack.enter_async_context(TemporaryDirectory()))
                    / "betty.json"
                )
            yield cls(
                app,
                configuration_file_path,
                configuration=configuration,
                ancestry=ancestry,
            )

    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        try:
            for project_extension_batch in await self.extensions:
                for project_extension in project_extension_batch:
                    await project_extension.bootstrap()
                    self._shutdown_stack.append(project_extension)
        except BaseException:
            await self.shutdown()
            raise

    @property
    def configuration_file_path(self) -> Path:
        """
        The path to the configuration's file.
        """
        return self._configuration_file_path

    async def set_configuration_file_path(
        self, configuration_file_path: Path, /
    ) -> None:
        """
        Set the path to the configuration's file.
        """
        if configuration_file_path == self._configuration_file_path:
            return
        format_for(
            list(await plugins(FormatDefinition)), configuration_file_path.suffix
        )
        self._configuration_file_path = configuration_file_path

    @property
    def project_directory_path(self) -> Path:
        """
        The project directory path.

        Betty will look for resources in this directory, and place generated artifacts there. It is expected
        that no other applications or projects share this same directory.
        """
        return self.configuration_file_path.parent

    @property
    def output_directory_path(self) -> Path:
        """
        The output directory path.
        """
        return self.project_directory_path / "output"

    @property
    def assets_directory_path(self) -> Path:
        """
        The :doc:`assets directory path </usage/assets>`.
        """
        return self.project_directory_path / "assets"

    @property
    def www_directory_path(self) -> Path:
        """
        The WWW directory path.
        """
        return self.output_directory_path / "www"

    def localize_www_directory_path(self, locale: Locale) -> Path:
        """
        Get the WWW directory path for a locale.
        """
        if self.configuration.locales.multilingual:
            return self.www_directory_path / self.configuration.locales[locale].alias
        return self.www_directory_path

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
            return hashid(str(self.configuration_file_path))
        return self._configuration.name

    @property
    def ancestry(self) -> Ancestry:
        """
        The project's ancestry.
        """
        return self._ancestry

    @service
    async def _project_assets(self) -> AssetRepository:
        asset_paths = [self.assets_directory_path]
        extensions = await self.extensions
        for project_extension in extensions.flatten():
            extension_assets_directory_path = (
                project_extension.plugin().assets_directory_path
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
        return [localizers.get(locale) for locale in self.configuration.locales]

    @service
    async def url_generator(self) -> UrlGenerator:
        """
        The URL generator.
        """
        return await new_project_url_generator(self)

    @service
    async def jinja2_environment(self) -> Environment:
        """
        The Jinja2 environment.
        """
        from betty.jinja2 import Environment

        return await Environment.new_for_project(self)

    @service
    async def renderer(self) -> RenderDispatcher:
        """
        The  content renderer.
        """
        return RenderDispatcher(
            *[
                await self.new_target(plugin.cls)
                for plugin in await self.plugins(RendererDefinition)
            ]
        )

    @service
    async def extensions(self) -> ProjectExtensions:
        """
        The enabled extensions.
        """
        from betty.config.factory import new_target

        extensions = await self.plugins(ExtensionDefinition)
        configured_extension_definitions = []
        configured_extension_configurations = {}
        for extension_configuration in self.configuration.extensions.values():
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
                    extension_target = new_target(
                        enabled_extension_definition.cls,
                        configured_extension_configurations[
                            enabled_extension_id
                        ].configuration,
                    )
                else:
                    extension_target = enabled_extension_definition.cls
                extension = await self.new_target(extension_target)
                enabled_extension_batch.append(extension)
                extensions_sorter.done(enabled_extension_id)
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

    @override
    async def new_target(self, target: AnyFactoryTarget[_T]) -> _T:
        if (
            isinstance(target, ProjectDependentFactory)
            or isinstance(target, type)
            and issubclass(target, ProjectDependentSelfFactory)
        ):
            return cast(_T, await target.new_for_project(self))
        return await self.app.new_target(cast(AppTarget[_T], target))

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
        from betty.config.factory import new_target

        copyright_notices = await self.plugins(CopyrightNoticeDefinition)
        return await self.new_target(
            new_target(
                copyright_notices[self.configuration.copyright_notice.id].cls,
                self.configuration.copyright_notice.configuration,
            )
        )

    @service
    async def license(self) -> License:
        """
        The overall project license.
        """
        from betty.config.factory import new_target

        licenses = await self.plugins(LicenseDefinition)
        return await self.new_target(
            new_target(
                licenses[self.configuration.license.id].cls,
                self.configuration.license.configuration,
            )
        )

    @service
    def privatizer(self) -> Privatizer:
        """
        The privatizer.
        """
        return Privatizer(self.configuration.lifetime_threshold, user=self.app.user)

    async def new_resource_context(
        self,
        resource: object = None,
        resource_url: object = None,
        **kwargs: object,
    ) -> ResourceContext:
        """
        Create new resource context variables.
        """
        extensions = await self.extensions
        return Context(
            resource,
            resource_url,
            **{
                key: value
                for extension in extensions.flatten()
                if isinstance(extension, ContextProvider)
                for (key, value) in extension.new_resource_context().items()
            },
            **kwargs,  # type: ignore[arg-type]
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


class ProjectContext(JobContext):
    """
    A job context for a project.
    """

    def __init__(
        self,
        project: Project,
        *,
        cache: Cache[Any] | None = None,
        progress: Progress | None = None,
    ):
        super().__init__(cache=cache, progress=progress)
        self._project = project

    @property
    def project(self) -> Project:
        """
        The Betty project this job context is run within.
        """
        return self._project
