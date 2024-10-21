"""
Provide the project API.

Projects are how people use Betty. A project is a workspace, starting out with the user's configuration,
and combining it with the resulting ancestry, allowing the user to perform tasks, such as generating a
site from the entire project.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager, AsyncExitStack
from graphlib import TopologicalSorter
from pathlib import Path
from typing import (
    final,
    Self,
    TYPE_CHECKING,
    TypeVar,
    Iterator,
    overload,
    cast,
    Awaitable,
)

from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty import fs, event_dispatcher
from betty.ancestry import Ancestry
from betty.ancestry.event_type import EVENT_TYPE_REPOSITORY
from betty.ancestry.gender import GENDER_REPOSITORY, Gender
from betty.ancestry.place_type import PLACE_TYPE_REPOSITORY, PlaceType
from betty.ancestry.presence_role import PRESENCE_ROLE_REPOSITORY, PresenceRole
from betty.assets import AssetRepository
from betty.concurrent import AsynchronizedLock
from betty.config import Configurable
from betty.copyright_notice import CopyrightNotice, COPYRIGHT_NOTICE_REPOSITORY
from betty.core import CoreComponent
from betty.event_dispatcher import EventDispatcher, EventHandlerRegistry
from betty.factory import TargetFactory
from betty.hashid import hashid
from betty.job import Context
from betty.json.schema import Schema, JsonSchemaReference
from betty.locale.localizable import _
from betty.locale.localizer import LocalizerRepository
from betty.model import Entity, EntityReferenceCollectionSchema
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.project import extension
from betty.project.config import ProjectConfiguration
from betty.project.extension import Extension, Theme, sort_extension_type_graph
from betty.project.factory import ProjectDependentFactory
from betty.project.url import (
    LocalizedUrlGenerator as ProjectLocalizedUrlGenerator,
    StaticUrlGenerator as ProjectStaticUrlGenerator,
)
from betty.render import Renderer, SequentialRenderer, RENDERER_REPOSITORY
from betty.string import kebab_case_to_lower_camel_case
from betty.typing import internal

if TYPE_CHECKING:
    from betty.license import License
    from betty.url import LocalizedUrlGenerator, StaticUrlGenerator
    from betty.ancestry.event_type import EventType
    from betty.machine_name import MachineName
    from betty.plugin import PluginIdentifier
    from collections.abc import Sequence
    from collections.abc import AsyncIterator
    from betty.app import App
    from betty.jinja2 import Environment
    from betty.plugin import PluginRepository

_T = TypeVar("_T")
_EntityT = TypeVar("_EntityT", bound=Entity)


_ProjectDependentT = TypeVar("_ProjectDependentT")


@final
class Project(Configurable[ProjectConfiguration], TargetFactory, CoreComponent):
    """
    Define a Betty project.

    A project combines project configuration and the resulting ancestry.
    """

    def __init__(
        self,
        app: App,
        configuration: ProjectConfiguration,
        *,
        ancestry: Ancestry,
    ):
        super().__init__(configuration=configuration)
        self._app = app
        self._ancestry = ancestry

        self._assets: AssetRepository | None = None
        self._assets_lock = AsynchronizedLock.threading()
        self._localizers: LocalizerRepository | None = None
        self._localizers_lock = AsynchronizedLock.threading()
        self._localized_url_generator: LocalizedUrlGenerator | None = None
        self._localized_url_generator_lock = AsynchronizedLock.threading()
        self._static_url_generator: StaticUrlGenerator | None = None
        self._static_url_generator_lock = AsynchronizedLock.threading()
        self._jinja2_environment: Environment | None = None
        self._jinja2_environment_lock = AsynchronizedLock.threading()
        self._renderer: Renderer | None = None
        self._renderer_lock = AsynchronizedLock.threading()
        self._extensions: ProjectExtensions | None = None
        self._extensions_lock = AsynchronizedLock.threading()
        self._event_dispatcher: EventDispatcher | None = None
        self._entity_types: set[type[Entity]] | None = None
        self._copyright_notice: CopyrightNotice | None = None
        self._copyright_notice_lock = AsynchronizedLock.threading()
        self._copyright_notice_repository: PluginRepository[CopyrightNotice] | None = (
            None
        )
        self._license: License | None = None
        self._license_lock = AsynchronizedLock.threading()
        self._license_repository: PluginRepository[License] | None = None
        self._licenses_lock = AsynchronizedLock.threading()
        self._event_type_repository: PluginRepository[EventType] | None = None
        self._place_type_repository: PluginRepository[PlaceType] | None = None
        self._presence_role_repository: PluginRepository[PresenceRole] | None = None
        self._gender_repository: PluginRepository[Gender] | None = None
        self._extension_repository: PluginRepository[Extension] | None = None

    @classmethod
    async def new(
        cls,
        app: App,
        *,
        configuration: ProjectConfiguration,
        ancestry: Ancestry | None = None,
    ) -> Self:
        """
        Create a new instance.
        """
        return cls(
            app,
            configuration,
            ancestry=await Ancestry.new() if ancestry is None else ancestry,
        )

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
                configuration = await ProjectConfiguration.new(
                    Path(
                        project_directory_path_str,  # type: ignore[arg-type]
                    )
                    / "betty.json"
                )
            yield await cls.new(app, configuration=configuration, ancestry=ancestry)

    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        try:
            for project_extension_batch in await self.extensions:
                batch_event_handlers = EventHandlerRegistry()
                for project_extension in project_extension_batch:
                    await project_extension.bootstrap()
                    self._shutdown_stack.append(project_extension)
                    project_extension.register_event_handlers(batch_event_handlers)
                self.event_dispatcher.add_registry(batch_event_handlers)
        except BaseException:
            await self.shutdown()
            raise

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

    @property
    def assets(self) -> Awaitable[AssetRepository]:
        """
        The assets file system.
        """
        return self._get_assets()

    async def _get_assets(self) -> AssetRepository:
        async with self._assets_lock:
            if self._assets is None:
                self.assert_bootstrapped()
                asset_paths = [self.configuration.assets_directory_path]
                extensions = await self.extensions
                for extension in extensions.flatten():
                    extension_assets_directory_path = extension.assets_directory_path()
                    if extension_assets_directory_path is not None:
                        asset_paths.append(extension_assets_directory_path)
                # Mimic :py:attr:`betty.app.App.assets`.
                asset_paths.append(fs.ASSETS_DIRECTORY_PATH)
                self._assets = AssetRepository(*asset_paths)
        return self._assets

    @property
    def localizers(self) -> Awaitable[LocalizerRepository]:
        """
        The available localizers.
        """
        return self._get_localizers()

    async def _get_localizers(self) -> LocalizerRepository:
        async with self._localizers_lock:
            if self._localizers is None:
                self.assert_bootstrapped()
                self._localizers = LocalizerRepository(await self.assets)
        return self._localizers

    @property
    def localized_url_generator(self) -> Awaitable[LocalizedUrlGenerator]:
        """
        The URL generator for localizable resources.
        """
        return self._get_localized_url_generator()

    async def _get_localized_url_generator(self) -> LocalizedUrlGenerator:
        async with self._localized_url_generator_lock:
            if self._localized_url_generator is None:
                self.assert_bootstrapped()
                self._localized_url_generator = (
                    await ProjectLocalizedUrlGenerator.new_for_project(self)
                )
        return self._localized_url_generator

    @property
    def static_url_generator(self) -> Awaitable[StaticUrlGenerator]:
        """
        The URL generator for static resources.
        """
        return self._get_static_url_generator()

    async def _get_static_url_generator(self) -> StaticUrlGenerator:
        async with self._static_url_generator_lock:
            if self._static_url_generator is None:
                self.assert_bootstrapped()
                self._static_url_generator = (
                    await ProjectStaticUrlGenerator.new_for_project(self)
                )
        return self._static_url_generator

    @property
    def jinja2_environment(self) -> Awaitable[Environment]:
        """
        The Jinja2 environment.
        """
        return self._get_jinja2_environment()

    async def _get_jinja2_environment(self) -> Environment:
        async with self._jinja2_environment_lock:
            if not self._jinja2_environment:
                from betty.jinja2 import Environment

                self.assert_bootstrapped()
                self._jinja2_environment = await Environment.new_for_project(self)

        return self._jinja2_environment

    @property
    def renderer(self) -> Awaitable[Renderer]:
        """
        The (file) content renderer.
        """
        return self._get_renderer()

    async def _get_renderer(self) -> Renderer:
        async with self._renderer_lock:
            if not self._renderer:
                self.assert_bootstrapped()
                self._renderer = SequentialRenderer(
                    [
                        await self.new_target(plugin)
                        for plugin in await RENDERER_REPOSITORY.select()
                    ]
                )
        return self._renderer

    @property
    def extensions(self) -> Awaitable[ProjectExtensions]:
        """
        The enabled extensions.
        """
        return self._get_extensions()

    async def _get_extensions(self) -> ProjectExtensions:
        async with self._extensions_lock:
            if self._extensions is None:
                self._extensions = await self._init_extensions()
        return self._extensions

    async def _init_extensions(self) -> ProjectExtensions:
        self.assert_bootstrapped()
        extensions = {}
        for extension_configuration in self.configuration.extensions.values():
            extension = await self.extension_repository.get(extension_configuration.id)
            extension_requirement = await extension.requirement()
            extension_requirement.assert_met()
            extensions[extension] = extension_configuration

        extensions_sorter = TopologicalSorter[type[Extension]]()
        await sort_extension_type_graph(extensions_sorter, extensions)
        extensions_sorter.prepare()

        theme_count = 0
        project_extension_instances = []
        while extensions_sorter.is_active():
            extensions_batch = extensions_sorter.get_ready()
            extension_instances_batch = []
            for extension in extensions_batch:
                if issubclass(extension, Theme):
                    theme_count += 1
                if extension in extensions:
                    extension_instance = await extensions[
                        extension
                    ].new_plugin_instance(self.extension_repository)
                else:
                    extension_instance = await self.extension_repository.new_target(
                        extension
                    )
                extension_instances_batch.append(extension_instance)
                extensions_sorter.done(extension)
            project_extension_instances.append(
                sorted(
                    extension_instances_batch,
                    key=lambda extension_instance: extension_instance.plugin_id(),
                )
            )
        initialized_extensions = ProjectExtensions(project_extension_instances)

        # Users may not realize no theme is enabled, and be confused by their site looking bare.
        # Warn them out of courtesy.
        if theme_count == 0:
            logging.getLogger().warning(
                _(
                    'Your project has no theme enabled. This means your site\'s pages may look bare. Try the "cotton-candy" extension.'
                ).localize(await self.app.localizer)
            )

        return initialized_extensions

    @property
    def event_dispatcher(self) -> EventDispatcher:
        """
        The event dispatcher.
        """
        if self._event_dispatcher is None:
            self.assert_bootstrapped()
            self._event_dispatcher = EventDispatcher()

        return self._event_dispatcher

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
            or fs.ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        )

    @property
    def copyright_notice(self) -> Awaitable[CopyrightNotice]:
        """
        The overall project copyright.
        """
        return self._get_copyright_notice()

    async def _get_copyright_notice(self) -> CopyrightNotice:
        async with self._copyright_notice_lock:
            if self._copyright_notice is None:
                self.assert_bootstrapped()
                self._copyright_notice = (
                    await self.configuration.copyright_notice.new_plugin_instance(
                        self.copyright_notice_repository
                    )
                )
        return self._copyright_notice

    @property
    def copyright_notice_repository(self) -> PluginRepository[CopyrightNotice]:
        """
        The copyright notices available to this project.

        Read more about :doc:`/development/plugin/copyright-notice`.
        """
        if self._copyright_notice_repository is None:
            self.assert_bootstrapped()
            self._copyright_notice_repository = ProxyPluginRepository(
                COPYRIGHT_NOTICE_REPOSITORY,
                StaticPluginRepository(
                    *self.configuration.copyright_notices.new_plugins()
                ),
                factory=self.new_target,
            )

        return self._copyright_notice_repository

    @property
    def license(self) -> Awaitable[License]:
        """
        The overall project license.
        """
        return self._get_license()

    async def _get_license(self) -> License:
        async with self._license_lock:
            if self._license is None:
                self._license = await self.configuration.license.new_plugin_instance(
                    await self.license_repository
                )
        return self._license

    @property
    def license_repository(self) -> Awaitable[PluginRepository[License]]:
        """
        The licenses available to this project.

        Read more about :doc:`/development/plugin/license`.
        """
        return self._get_licenses()

    async def _get_licenses(self) -> PluginRepository[License]:
        async with self._licenses_lock:
            if self._license_repository is None:
                self.assert_bootstrapped()
                self._license_repository = ProxyPluginRepository(
                    await self._app.spdx_license_repository,
                    StaticPluginRepository(*self.configuration.licenses.new_plugins()),
                    factory=self.new_target,
                )

        return self._license_repository

    @property
    def event_type_repository(self) -> PluginRepository[EventType]:
        """
        The event types available to this project.
        """
        if self._event_type_repository is None:
            self.assert_bootstrapped()
            self._event_type_repository = ProxyPluginRepository(
                EVENT_TYPE_REPOSITORY,
                StaticPluginRepository(*self.configuration.event_types.new_plugins()),
                factory=self.new_target,
            )

        return self._event_type_repository

    @property
    def place_type_repository(self) -> PluginRepository[PlaceType]:
        """
        The place types available to this project.
        """
        if self._place_type_repository is None:
            self.assert_bootstrapped()
            self._place_type_repository = ProxyPluginRepository(
                PLACE_TYPE_REPOSITORY,
                StaticPluginRepository(*self.configuration.place_types.new_plugins()),
                factory=self.new_target,
            )

        return self._place_type_repository

    @property
    def presence_role_repository(self) -> PluginRepository[PresenceRole]:
        """
        The presence roles available to this project.
        """
        if self._presence_role_repository is None:
            self.assert_bootstrapped()
            self._presence_role_repository = ProxyPluginRepository(
                PRESENCE_ROLE_REPOSITORY,
                StaticPluginRepository(
                    *self.configuration.presence_roles.new_plugins()
                ),
                factory=self.new_target,
            )

        return self._presence_role_repository

    @property
    def gender_repository(self) -> PluginRepository[Gender]:
        """
        The genders available to this project.

        Read more about :doc:`/development/plugin/gender`.
        """
        if self._gender_repository is None:
            self.assert_bootstrapped()
            self._gender_repository = ProxyPluginRepository(
                GENDER_REPOSITORY,
                StaticPluginRepository(*self.configuration.genders.new_plugins()),
                factory=self.new_target,
            )

        return self._gender_repository

    @property
    def extension_repository(self) -> PluginRepository[Extension]:
        """
        The extensions available to this project.

        Read more about :doc:`/development/plugin/extension`.
        """
        if self._extension_repository is None:
            self.assert_bootstrapped()
            self._extension_repository = ProxyPluginRepository(
                extension.EXTENSION_REPOSITORY, factory=self.new_target
            )

        return self._extension_repository


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
    def __getitem__(self, extension_id: MachineName) -> Extension:
        pass

    @overload
    def __getitem__(self, extension_type: type[_ExtensionT]) -> _ExtensionT:
        pass

    def __getitem__(
        self, extension_identifier: PluginIdentifier[Extension]
    ) -> Extension:
        for project_extension in self.flatten():
            if isinstance(extension_identifier, str):
                if project_extension.plugin_id() == extension_identifier:
                    return project_extension
            elif type(project_extension) is extension_identifier:
                return project_extension
        raise KeyError(f'Unknown extension of type "{extension_identifier}"')

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

    def __contains__(self, extension_identifier: PluginIdentifier[Extension]) -> bool:
        try:
            self[extension_identifier]
        except KeyError:
            return False
        else:
            return True


class ProjectEvent(event_dispatcher.Event):
    """
    An event that is dispatched within the context of a :py:class:`betty.project.Project`.
    """

    def __init__(self, job_context: ProjectContext):
        self._job_context = job_context

    @property
    def project(self) -> Project:
        """
        The :py:class:`betty.project.Project` this event is dispatched within.
        """
        return self.job_context.project

    @property
    def job_context(self) -> ProjectContext:
        """
        The site generation job context.
        """
        return self._job_context


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
        static_url_generator = await project.static_url_generator
        return static_url_generator.generate("/schema.json", absolute=True)

    @classmethod
    def www_path(cls, project: Project) -> Path:
        """
        Get the path to the schema file in a site's public WWW directory.
        """
        return project.configuration.www_directory_path / "schema.json"

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        from betty import model

        schema = cls()
        schema._schema["$id"] = await cls.url(project)

        # Add entity schemas.
        async for entity_type in model.ENTITY_TYPE_REPOSITORY:
            entity_type_schema = await entity_type.linked_data_schema(project)
            entity_type_schema.embed(schema)
            def_name = f"{kebab_case_to_lower_camel_case(entity_type.plugin_id())}EntityCollectionResponse"
            schema.defs[def_name] = {
                "type": "object",
                "properties": {
                    "collection": EntityReferenceCollectionSchema().embed(schema),
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


class ProjectContext(Context):
    """
    A job context for a project.
    """

    def __init__(self, project: Project):
        super().__init__()
        self._project = project

    @property
    def project(self) -> Project:
        """
        The Betty project this job context is run within.
        """
        return self._project
