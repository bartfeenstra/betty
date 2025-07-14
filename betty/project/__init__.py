"""
Provide the project API.

Projects are how people use Betty. A project is a workspace, starting out with the user's configuration,
and combining it with the resulting ancestry, allowing the user to perform tasks, such as generating a
site from the entire project.
"""

from __future__ import annotations

import logging
from contextlib import AsyncExitStack, asynccontextmanager
from graphlib import TopologicalSorter
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Self,
    TypeVar,
    cast,
    final,
    overload,
)

from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty import event_dispatcher, fs, model
from betty.ancestry import Ancestry
from betty.ancestry.event_type import EVENT_TYPE_REPOSITORY
from betty.ancestry.gender import GENDER_REPOSITORY, Gender
from betty.ancestry.place_type import PLACE_TYPE_REPOSITORY, PlaceType
from betty.ancestry.presence_role import PRESENCE_ROLE_REPOSITORY, PresenceRole
from betty.assets import AssetRepository
from betty.concurrent import ensure_manager
from betty.config import Configurable
from betty.copyright_notice import COPYRIGHT_NOTICE_REPOSITORY, CopyrightNotice
from betty.event_dispatcher import EventDispatcher, EventHandlerRegistry
from betty.factory import TargetFactory
from betty.hashid import hashid
from betty.job import Context
from betty.json.schema import JsonSchemaReference, Schema
from betty.locale.localizable import _
from betty.locale.localizer import LocalizerRepository
from betty.model import Entity, ToManySchema
from betty.plugin import resolve_identifier
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.project import extension
from betty.project.config import ProjectConfiguration
from betty.project.extension import Extension, Theme, sort_extension_type_graph
from betty.project.factory import ProjectDependentFactory
from betty.project.url import (
    LocalizedUrlGenerator as ProjectLocalizedUrlGenerator,
)
from betty.project.url import (
    StaticUrlGenerator as ProjectStaticUrlGenerator,
)
from betty.project.url import (
    new_project_url_generator,
)
from betty.render import RENDERER_REPOSITORY, Renderer, SequentialRenderer
from betty.service import ServiceProvider, service
from betty.string import kebab_case_to_lower_camel_case
from betty.typing import internal
from betty.warnings import deprecated

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator, Sequence
    from multiprocessing.managers import SyncManager

    from betty.ancestry.event_type import EventType
    from betty.app import App
    from betty.jinja2 import Environment
    from betty.license import License
    from betty.machine_name import MachineName
    from betty.plugin import PluginIdentifier, PluginRepository
    from betty.url import LocalizedUrlGenerator, StaticUrlGenerator, UrlGenerator

_T = TypeVar("_T")
_EntityT = TypeVar("_EntityT", bound=Entity)

_ProjectDependentT = TypeVar("_ProjectDependentT")


@final
class Project(Configurable[ProjectConfiguration], TargetFactory, ServiceProvider):
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
                    Path(project_directory_path_str) / "betty.json"
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
            await self._assert_configuration()
        except BaseException:
            await self.shutdown()
            raise

    async def _assert_configuration(self) -> None:
        await self.configuration.entity_types.validate(self.entity_type_repository)

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
    async def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        asset_paths = [self.configuration.assets_directory_path]
        extensions = await self.extensions
        for project_extension in extensions.flatten():
            extension_assets_directory_path = project_extension.assets_directory_path()
            if extension_assets_directory_path is not None:
                asset_paths.append(extension_assets_directory_path)
        # Mimic :py:attr:`betty.app.App.assets`.
        asset_paths.append(fs.ASSETS_DIRECTORY_PATH)
        return AssetRepository(*asset_paths)

    @service
    async def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        return LocalizerRepository(await self.assets)

    @service
    async def url_generator(self) -> UrlGenerator:
        """
        The URL generator.
        """
        return await new_project_url_generator(self)

    @service
    @deprecated(
        "This service has been deprecated since Betty 0.4.8, and will be removed in Betty 0.5. Instead use `Project.url_generator`."
    )
    async def localized_url_generator(self) -> LocalizedUrlGenerator:
        """
        The URL generator for localizable resources.
        """
        return await ProjectLocalizedUrlGenerator.new_for_project(self)

    @service
    @deprecated(
        "This service has been deprecated since Betty 0.4.8, and will be removed in Betty 0.5. Instead use `Project.url_generator`."
    )
    async def static_url_generator(self) -> StaticUrlGenerator:
        """
        The URL generator for static resources.
        """
        return await ProjectStaticUrlGenerator.new_for_project(self)

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
        return SequentialRenderer(
            [
                await self.new_target(plugin)
                for plugin in await RENDERER_REPOSITORY.select()
            ]
        )

    @service
    async def extensions(self) -> ProjectExtensions:
        """
        The enabled extensions.
        """
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
                    'Your project has no theme enabled. This means your site\'s pages may look bare. Try the "raspberry-mint" extension.'
                ).localize(await self.app.localizer)
            )

        return initialized_extensions

    @service
    def event_dispatcher(self) -> EventDispatcher:
        """
        The event dispatcher.
        """
        return EventDispatcher()

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

    @service
    async def copyright_notice(self) -> CopyrightNotice:
        """
        The overall project copyright.
        """
        return await self.configuration.copyright_notice.new_plugin_instance(
            self.copyright_notice_repository
        )

    @service
    def copyright_notice_repository(self) -> PluginRepository[CopyrightNotice]:
        """
        The copyright notices available to this project.

        Read more about :doc:`/development/plugin/copyright-notice`.
        """
        return ProxyPluginRepository(
            COPYRIGHT_NOTICE_REPOSITORY,
            StaticPluginRepository(*self.configuration.copyright_notices.new_plugins()),
            factory=self.new_target,
            schema_template=Schema(
                def_name="copyrightNotice", title="Copyright notice"
            ),
        )

    @service
    async def license(self) -> License:
        """
        The overall project license.
        """
        return await self.configuration.license.new_plugin_instance(
            await self.license_repository
        )

    @service
    async def license_repository(self) -> PluginRepository[License]:
        """
        The licenses available to this project.

        Read more about :doc:`/development/plugin/license`.
        """
        return ProxyPluginRepository(
            await self._app.spdx_license_repository,
            StaticPluginRepository(*self.configuration.licenses.new_plugins()),
            factory=self.new_target,
            schema_template=Schema(def_name="license", title="License"),
        )

    @service
    def event_type_repository(self) -> PluginRepository[EventType]:
        """
        The event types available to this project.
        """
        return ProxyPluginRepository(
            EVENT_TYPE_REPOSITORY,
            StaticPluginRepository(*self.configuration.event_types.new_plugins()),
            factory=self.new_target,
            schema_template=Schema(def_name="eventType", title="Event type"),
        )

    @service
    def place_type_repository(self) -> PluginRepository[PlaceType]:
        """
        The place types available to this project.
        """
        return ProxyPluginRepository(
            PLACE_TYPE_REPOSITORY,
            StaticPluginRepository(*self.configuration.place_types.new_plugins()),
            factory=self.new_target,
            schema_template=Schema(def_name="placeType", title="Place type"),
        )

    @service
    def presence_role_repository(self) -> PluginRepository[PresenceRole]:
        """
        The presence roles available to this project.
        """
        return ProxyPluginRepository(
            PRESENCE_ROLE_REPOSITORY,
            StaticPluginRepository(*self.configuration.presence_roles.new_plugins()),
            factory=self.new_target,
            schema_template=Schema(def_name="presenceRole", title="Presence role"),
        )

    @service
    def gender_repository(self) -> PluginRepository[Gender]:
        """
        The genders available to this project.

        Read more about :doc:`/development/plugin/gender`.
        """
        return ProxyPluginRepository(
            GENDER_REPOSITORY,
            StaticPluginRepository(*self.configuration.genders.new_plugins()),
            factory=self.new_target,
            schema_template=Schema(def_name="gender", title="Gender"),
        )

    @service
    def entity_type_repository(self) -> PluginRepository[Entity]:
        """
        The entity types available to this project.

        Read more about :doc:`/development/plugin/entity-type`.
        """
        return ProxyPluginRepository(
            model.ENTITY_TYPE_REPOSITORY,
            factory=self.new_target,
            schema_template=Schema(def_name="entityType", title="Entity type"),
        )

    @service
    def extension_repository(self) -> PluginRepository[Extension]:
        """
        The extensions available to this project.

        Read more about :doc:`/development/plugin/extension`.
        """
        return ProxyPluginRepository(
            extension.EXTENSION_REPOSITORY, factory=self.new_target
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
    def __getitem__(self, extension_id: MachineName) -> Extension:
        pass

    @overload
    def __getitem__(self, extension_type: type[_ExtensionT]) -> _ExtensionT:
        pass

    def __getitem__(
        self, extension_identifier: PluginIdentifier[Extension]
    ) -> Extension:
        extension_id = resolve_identifier(extension_identifier)
        for project_extension in self.flatten():
            if project_extension.plugin_id() == extension_id:
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


class ProjectContext(Context):
    """
    A job context for a project.
    """

    def __init__(self, project: Project, manager: SyncManager | None = None):
        manager = ensure_manager(manager)
        super().__init__(manager=manager)
        self._project = project

    @property
    def project(self) -> Project:
        """
        The Betty project this job context is run within.
        """
        return self._project
