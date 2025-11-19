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
from betty.asset import AssetRepository, ProxyAssetRepository, StaticAssetRepository
from betty.config import Configurable
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.data import Key
from betty.exception import HumanFacingExceptionGroup
from betty.factory import TargetFactory
from betty.hashid import hashid
from betty.job import Context as JobContext
from betty.json.schema import JsonSchemaReference, Schema
from betty.license import LicenseDefinition
from betty.locale.localizable import _
from betty.locale.localizer import LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    ProxyTranslationRepository,
    TranslationRepository,
)
from betty.model import Entity, EntityDefinition, ToManySchema
from betty.plugin import (
    PluginRepositoryProvider,
    resolve_id,
)
from betty.plugin.dependent import sort_dependent_plugin_graph
from betty.privacy.privatizer import Privatizer
from betty.project.config import ProjectConfiguration
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.factory import ProjectDependentFactory
from betty.project.url import new_project_url_generator
from betty.render import ProxyRenderer, Renderer, RendererDefinition
from betty.resource import Context as ResourceContext
from betty.resource import ContextProvider, new_context
from betty.service import ServiceProvider, service
from betty.string import kebab_case_to_lower_camel_case
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator, MutableSequence, Sequence

    from betty.app import App
    from betty.cache import Cache
    from betty.jinja2 import Environment
    from betty.license import License
    from betty.machine_name import MachineName
    from betty.plugin import PluginIdentifier
    from betty.progress import Progress
    from betty.url import UrlGenerator

_T = TypeVar("_T")
_EntityT = TypeVar("_EntityT", bound=Entity)

_ProjectDependentT = TypeVar("_ProjectDependentT")


@final
class Project(
    Configurable[ProjectConfiguration],
    TargetFactory,
    ServiceProvider,
    PluginRepositoryProvider,
):
    """
    Define a Betty project.

    A project combines project configuration and the resulting ancestry.
    """

    def __init__(
        self,
        app: App,
        configuration: ProjectConfiguration,
        *,
        ancestry: Ancestry | None = None,
    ):
        super().__init__(configuration=configuration, service_level=self)
        self._app = app
        self._ancestry = Ancestry() if ancestry is None else ancestry

    @classmethod
    @asynccontextmanager
    async def new_temporary(
        cls,
        app: App,
        *,
        configuration: ProjectConfiguration | None = None,
        ancestry: Ancestry | None = None,
    ) -> AsyncIterator[Self]:
        """
        Creat a new, temporary, isolated project.

        The project will not leave any traces on the system, except when it uses
        global Betty functionality such as caches.
        """
        async with AsyncExitStack() as stack:
            if configuration is None:
                project_directory_path_str = await stack.enter_async_context(
                    TemporaryDirectory()
                )
                configuration = ProjectConfiguration(
                    Path(project_directory_path_str) / "betty.json"
                )
            yield cls(
                app,
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
            await self._assert_configuration()
        except BaseException:
            await self.shutdown()
            raise

    async def _assert_configuration(self) -> None:
        with (
            HumanFacingExceptionGroup().assert_valid() as errors,
            errors.catch(Key("entity_types")),
        ):
            await self.configuration.entity_types.validate(
                await self.plugins(EntityDefinition)
            )

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
            return hashid(str(self._configuration.configuration_file_path))
        return self._configuration.name

    @property
    def ancestry(self) -> Ancestry:
        """
        The project's ancestry.
        """
        return self._ancestry

    @service
    async def _project_assets(self) -> AssetRepository:
        asset_paths = [self.configuration.assets_directory_path]
        extensions = await self.extensions
        for project_extension in extensions.flatten():
            extension_assets_directory_path = (
                project_extension.plugin.assets_directory_path
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
    async def renderer(self) -> Renderer:
        """
        The (file) content renderer.
        """
        return ProxyRenderer(
            [
                await self.new_target(plugin.cls)
                for plugin in await self.plugins(RendererDefinition)
            ]
        )

    @service
    async def extensions(self) -> ProjectExtensions:
        """
        The enabled extensions.
        """
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
                enabled_extension_requirement = (
                    await enabled_extension_definition.cls.requirement(app=self.app)
                )
                if enabled_extension_requirement is not None:
                    enabled_extension_requirement.assert_met()
                if enabled_extension_definition.theme:
                    theme_count += 1
                if enabled_extension_id in configured_extension_configurations:
                    extension = await configured_extension_configurations[
                        enabled_extension_id
                    ].new_plugin_instance(extensions, factory=self.new_target)
                else:
                    extension = await self.new_target(enabled_extension_definition.cls)
                enabled_extension_batch.append(extension)
                extensions_sorter.done(enabled_extension_id)
            enabled_extensions.append(
                sorted(
                    enabled_extension_batch,
                    key=lambda extension: extension.plugin.id,
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
    async def new_target(self, cls: type[_T]) -> _T:
        """
        Create a new instance.

        :return:
            #. If ``cls`` extends :py:class:`betty.project.factory.ProjectDependentFactory`, this will call return
                ``cls``'s ``new()``'s return value.
            #. If ``cls`` extends :py:class:`betty.app.factory.AppDependentFactory`, this will call return ``cls``'s
                ``new()``'s return value.
            #. If ``cls`` extends :py:class:`betty.factory.IndependentFactory`, this will call return ``cls``'s
                ``new()``'s return value.
            #. Otherwise ``cls()`` will be called without arguments, and the resulting instance will be returned.

        :raises FactoryError: raised when ``cls`` could not be instantiated.
        """
        if issubclass(cls, ProjectDependentFactory):
            return cast(_T, await cls.new_for_project(self))
        return await self.app.new_target(cls)

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
        return await self.configuration.copyright_notice.new_plugin_instance(
            await self.plugins(CopyrightNoticeDefinition), factory=self.new_target
        )

    @service
    async def license(self) -> License:
        """
        The overall project license.
        """
        return await self.configuration.license.new_plugin_instance(
            await self.plugins(LicenseDefinition), factory=self.new_target
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
        return new_context(
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
    def __getitem__(
        self, extension: PluginIdentifier[ExtensionDefinition, Extension]
    ) -> Extension:
        pass

    def __getitem__(
        self, extension: PluginIdentifier[ExtensionDefinition, Extension]
    ) -> Extension:
        extension_id = resolve_id(extension)
        for project_extension in self.flatten():
            if project_extension.plugin.id == extension_id:
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

    def __contains__(
        self, extension: PluginIdentifier[ExtensionDefinition, Extension]
    ) -> bool:
        if isinstance(extension, type) and issubclass(extension, Extension):
            extension = extension.plugin
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


_ProjectContextT = TypeVar(
    "_ProjectContextT", bound=ProjectContext, default=ProjectContext
)


@final
class ProjectSchema(ProjectDependentFactory, Schema):
    """
    A JSON Schema for a project.
    """

    @classmethod
    async def def_url(cls, project: Project, def_name: str) -> str:
        """
        Get the URL to a project's JSON Schema definition.
        """
        return f"{await cls.url(project)}#/$defs/{def_name}"

    @classmethod
    async def url(cls, project: Project) -> str:
        """
        Get the URL to a project's JSON Schema.
        """
        url_generator = await project.url_generator
        return url_generator.generate("betty-static:///schema.json", absolute=True)

    @classmethod
    def www_path(cls, project: Project) -> Path:
        """
        Get the path to the schema file in a site's public WWW directory.
        """
        return project.configuration.www_directory_path / "schema.json"

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        schema = cls()
        schema._schema["$id"] = await cls.url(project)

        # Add entity schemas.
        for entity_type in await project.plugins(EntityDefinition):
            entity_type_schema = await entity_type.cls.linked_data_schema(project)
            entity_type_schema.embed(schema)
            def_name = f"{kebab_case_to_lower_camel_case(entity_type.id)}EntityCollectionResponse"
            schema.defs[def_name] = {
                "type": "object",
                "properties": {
                    "collection": ToManySchema().embed(schema),
                },
            }

        # Add the HTTP error response.
        schema.defs["errorResponse"] = {
            "type": "object",
            "properties": {
                "$schema": JsonSchemaReference().embed(schema),
                "message": {
                    "type": "string",
                },
            },
            "required": [
                "$schema",
                "message",
            ],
            "additionalProperties": False,
        }

        schema._schema["anyOf"] = [
            {"$ref": f"#/$defs/{def_name}"} for def_name in schema.defs
        ]

        return schema
