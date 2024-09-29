"""
Provide the project API.

Projects are how people use Betty. A project is a workspace, starting out with the user's configuration,
and combining it with the resulting ancestry, allowing the user to perform tasks, such as generating a
site from the entire project.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from graphlib import TopologicalSorter
from pathlib import Path
from typing import (
    Any,
    final,
    Self,
    TYPE_CHECKING,
    TypeVar,
    Iterator,
    overload,
    cast,
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
from betty.asyncio import wait_to_thread
from betty.config import (
    Configurable,
)
from betty.copyright_notice import CopyrightNotice, COPYRIGHT_NOTICE_REPOSITORY
from betty.core import CoreComponent
from betty.event_dispatcher import EventDispatcher, EventHandlerRegistry
from betty.factory import FactoryProvider
from betty.hashid import hashid
from betty.job import Context
from betty.json.schema import (
    Schema,
    JsonSchemaReference,
)
from betty.locale.localizable import _
from betty.locale.localizer import LocalizerRepository
from betty.model import Entity, EntityReferenceCollectionSchema
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.project import extension
from betty.project.config import ProjectConfiguration
from betty.project.extension import (
    Extension,
    ConfigurableExtension,
    build_extension_type_graph,
    Theme,
)
from betty.project.factory import ProjectDependentFactory
from betty.project.url import (
    LocalizedUrlGenerator as ProjectLocalizedUrlGenerator,
    StaticUrlGenerator as ProjectStaticUrlGenerator,
)
from betty.render import Renderer, SequentialRenderer, RENDERER_REPOSITORY
from betty.string import kebab_case_to_lower_camel_case
from betty.typing import internal

if TYPE_CHECKING:
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
class Project(Configurable[ProjectConfiguration], FactoryProvider[Any], CoreComponent):
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
        super().__init__()
        self._app = app
        self._configuration = configuration
        self._ancestry = Ancestry() if ancestry is None else ancestry

        self._assets: AssetRepository | None = None
        self._localizers: LocalizerRepository | None = None
        self._url_generator: LocalizedUrlGenerator | None = None
        self._static_url_generator: StaticUrlGenerator | None = None
        self._jinja2_environment: Environment | None = None
        self._renderer: Renderer | None = None
        self._extensions: ProjectExtensions | None = None
        self._event_dispatcher: EventDispatcher | None = None
        self._entity_types: set[type[Entity]] | None = None
        self._copyright_notice: CopyrightNotice | None = None
        self._copyright_notices: PluginRepository[CopyrightNotice] | None = None
        self._event_types: PluginRepository[EventType] | None = None
        self._place_types: PluginRepository[PlaceType] | None = None
        self._presence_roles: PluginRepository[PresenceRole] | None = None
        self._genders: PluginRepository[Gender] | None = None

    @classmethod
    @asynccontextmanager
    async def new_temporary(
        cls, app: App, *, ancestry: Ancestry | None = None
    ) -> AsyncIterator[Self]:
        """
        Creat a new, temporary, isolated project.

        The project will not leave any traces on the system, except when it uses
        global Betty functionality such as caches.
        """
        async with (
            TemporaryDirectory() as project_directory_path_str,
        ):
            yield cls(
                app,
                ProjectConfiguration(Path(project_directory_path_str) / "betty.json"),
                ancestry=ancestry,
            )

    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        try:
            for project_extension_batch in self.extensions:
                batch_event_handlers = EventHandlerRegistry()
                for project_extension in project_extension_batch:
                    await self._async_exit_stack.enter_async_context(project_extension)
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
    def assets(self) -> AssetRepository:
        """
        The assets file system.
        """
        if self._assets is None:
            self._assert_bootstrapped()
            asset_paths = [self.configuration.assets_directory_path]
            for extension in self.extensions.flatten():
                extension_assets_directory_path = extension.assets_directory_path()
                if extension_assets_directory_path is not None:
                    asset_paths.append(extension_assets_directory_path)
            # Mimic :py:attr:`betty.app.App.assets`.
            asset_paths.append(fs.ASSETS_DIRECTORY_PATH)
            self._assets = AssetRepository(*asset_paths)
        return self._assets

    @property
    def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        if self._localizers is None:
            self._assert_bootstrapped()
            self._localizers = LocalizerRepository(self.assets)
        return self._localizers

    @property
    def localized_url_generator(self) -> LocalizedUrlGenerator:
        """
        The URL generator for localizable resources.
        """
        if self._url_generator is None:
            self._assert_bootstrapped()
            self._url_generator = wait_to_thread(
                ProjectLocalizedUrlGenerator.new_for_project(self)
            )
        return self._url_generator

    @property
    def static_url_generator(self) -> StaticUrlGenerator:
        """
        The URL generator for static resources.
        """
        if self._static_url_generator is None:
            self._assert_bootstrapped()
            self._static_url_generator = wait_to_thread(
                ProjectStaticUrlGenerator.new_for_project(self)
            )
        return self._static_url_generator

    @property
    def jinja2_environment(self) -> Environment:
        """
        The Jinja2 environment.
        """
        if not self._jinja2_environment:
            from betty.jinja2 import Environment

            self._assert_bootstrapped()
            self._jinja2_environment = Environment(self)

        return self._jinja2_environment

    @property
    def renderer(self) -> Renderer:
        """
        The (file) content renderer.
        """
        if not self._renderer:
            self._assert_bootstrapped()
            self._renderer = wait_to_thread(self._init_renderer())

        return self._renderer

    async def _init_renderer(self) -> Renderer:
        return SequentialRenderer(
            [await self.new(plugin) for plugin in await RENDERER_REPOSITORY.select()]
        )

    @property
    def extensions(self) -> ProjectExtensions:
        """
        The enabled extensions.
        """
        if self._extensions is None:
            self._assert_bootstrapped()
            self._extensions = wait_to_thread(self._init_extensions())

        return self._extensions

    async def _init_extensions(self) -> ProjectExtensions:
        extension_types_enabled_in_configuration = set()
        for project_extension_configuration in self.configuration.extensions.values():
            if project_extension_configuration.enabled:
                await project_extension_configuration.extension_type.enable_requirement().assert_met()
                extension_types_enabled_in_configuration.add(
                    project_extension_configuration.extension_type
                )

        extension_types_sorter = TopologicalSorter(
            await build_extension_type_graph(extension_types_enabled_in_configuration)
        )
        extension_types_sorter.prepare()

        extensions = []
        while extension_types_sorter.is_active():
            extension_types_batch = extension_types_sorter.get_ready()
            extensions_batch = []
            for extension_type in extension_types_batch:
                extension = await self.new(extension_type)
                if (
                    isinstance(extension, ConfigurableExtension)
                    and extension_type in self.configuration.extensions
                ):
                    extension.configuration.update(
                        self.configuration.extensions[
                            extension_type
                        ].extension_configuration
                    )
                extensions_batch.append(extension)
                extension_types_sorter.done(extension_type)
            extensions.append(
                sorted(extensions_batch, key=lambda extension: extension.plugin_id())
            )
        initialized_extensions = ProjectExtensions(extensions)

        # Users may not realize no theme is enabled, and be confused by their site looking bare.
        # Warn them out of courtesy.
        theme_count = len(
            [extension for extension in extensions if isinstance(extension, Theme)]
        )
        if theme_count == 0:
            logging.getLogger().warning(
                _(
                    'Your project has no theme enabled. This means your site\'s pages may look bare. Try the "cotton-candy" extension.'
                ).localize(self.app.localizer)
            )

        return initialized_extensions

    @property
    def event_dispatcher(self) -> EventDispatcher:
        """
        The event dispatcher.
        """
        if self._event_dispatcher is None:
            self._assert_bootstrapped()
            self._event_dispatcher = EventDispatcher()

        return self._event_dispatcher

    @override
    async def new(self, cls: type[_T]) -> _T:
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
        return await self.app.new(cls)

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
    def copyright_notice(self) -> CopyrightNotice:
        """
        The overall project copyright.
        """
        if self._copyright_notice is None:
            self._copyright_notice = wait_to_thread(self._init_copyright())
        return self._copyright_notice

    async def _init_copyright(self) -> CopyrightNotice:
        return await self.new(
            await self.copyright_notices.get(self.configuration.copyright_notice)
        )

    @property
    def copyright_notices(self) -> PluginRepository[CopyrightNotice]:
        """
        The copyright notices available to this project.

        Read more about :doc:`/development/plugin/copyright-notice`.
        """
        if self._copyright_notices is None:
            self._assert_bootstrapped()
            self._copyright_notices = ProxyPluginRepository(
                COPYRIGHT_NOTICE_REPOSITORY,
                StaticPluginRepository(*self.configuration.copyright_notices.plugins),
            )

        return self._copyright_notices

    @property
    def event_types(self) -> PluginRepository[EventType]:
        """
        The event types available to this project.
        """
        if self._event_types is None:
            self._assert_bootstrapped()
            self._event_types = ProxyPluginRepository(
                EVENT_TYPE_REPOSITORY,
                StaticPluginRepository(*self.configuration.event_types.plugins),
            )

        return self._event_types

    @property
    def place_types(self) -> PluginRepository[PlaceType]:
        """
        The place types available to this project.
        """
        if self._place_types is None:
            self._assert_bootstrapped()
            self._place_types = ProxyPluginRepository(
                PLACE_TYPE_REPOSITORY,
                StaticPluginRepository(*self.configuration.place_types.plugins),
            )

        return self._place_types

    @property
    def presence_roles(self) -> PluginRepository[PresenceRole]:
        """
        The presence roles available to this project.
        """
        if self._presence_roles is None:
            self._assert_bootstrapped()
            self._presence_roles = ProxyPluginRepository(
                PRESENCE_ROLE_REPOSITORY,
                StaticPluginRepository(*self.configuration.presence_roles.plugins),
            )

        return self._presence_roles

    @property
    def genders(self) -> PluginRepository[Gender]:
        """
        The genders available to this project.

        Read more about :doc:`/development/plugin/gender`.
        """
        if self._genders is None:
            self._assert_bootstrapped()
            self._genders = ProxyPluginRepository(
                GENDER_REPOSITORY,
                StaticPluginRepository(*self.configuration.genders.plugins),
            )

        return self._genders


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
        if isinstance(extension_identifier, str):
            extension_type = wait_to_thread(
                extension.EXTENSION_REPOSITORY.get(extension_identifier)
            )
        else:
            extension_type = extension_identifier
        for project_extension in self.flatten():
            if type(project_extension) is extension_type:
                return project_extension
        raise KeyError(f'Unknown extension of type "{extension_type}"')

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
class ProjectSchema(Schema):
    """
    A JSON Schema for a project.
    """

    @classmethod
    def def_url(cls, project: Project, def_name: str) -> str:
        """
        Get the URL to a project's JSON Schema definition.
        """
        return f"{cls.url(project)}#/$defs/{def_name}"

    @classmethod
    def url(cls, project: Project) -> str:
        """
        Get the URL to a project's JSON Schema.
        """
        return project.static_url_generator.generate("/schema.json", absolute=True)

    @classmethod
    def www_path(cls, project: Project) -> Path:
        """
        Get the path to the schema file in a site's public WWW directory.
        """
        return project.configuration.www_directory_path / "schema.json"

    @classmethod
    async def new(cls, project: Project) -> Self:
        """
        Create a new schema for the given project.
        """
        from betty import model

        schema = cls()
        schema._schema["$id"] = cls.url(project)

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
