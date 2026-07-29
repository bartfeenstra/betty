"""
Provide the project API.

Projects are how people use Betty. A project is a workspace, starting out with the user's configuration,
and combining it with the resulting ancestry, allowing the user to perform tasks, such as generating a
site from the entire project.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from collections.abc import MutableSequence
from contextlib import AsyncExitStack, asynccontextmanager
from operator import not_
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, Final, Literal, Never, Self, final
from urllib.parse import urlsplit

from babel import Locale

from betty.about import version_major
from betty.app import App
from betty.assertions.int import assert_int
from betty.assertions.url import assert_url
from betty.attrs.locale import new_locale_attr
from betty.attrs.localizable import new_localizable_attr
from betty.attrs.machine_name import new_machine_name_attr
from betty.attrs.owner import CollectionOwnerAttr, OwnerAttr
from betty.attrs.path import new_path_attr
from betty.attrs.plugin_definitions import new_plugin_definition_datas_attr
from betty.collections import _empty_frozen_mapping
from betty.collections.keyed.adapter import (
    KeyedCollectionAdapter,
    MutableKeyedCollectionAdapter,
)
from betty.collections.sequence.adapter import MutableResolvedSequenceAdapter
from betty.copyright_notice import (
    CopyrightNotice,
    CopyrightNoticeDefinition,
    CopyrightNoticeManufacturer,
)
from betty.data import Data
from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.bool import BoolDefinition
from betty.datas.int import IntDefinition
from betty.datas.plugin.definition.copyright_notice import CopyrightNoticeDefinitionData
from betty.datas.plugin.definition.event_type import EventTypeDefinitionData
from betty.datas.plugin.definition.gender import GenderDefinitionData
from betty.datas.plugin.definition.license import LicenseDefinitionData
from betty.datas.plugin.definition.place_type import PlaceTypeDefinitionData
from betty.datas.plugin.definition.role import RoleDefinitionData
from betty.datas.str import StrDefinition
from betty.definition.cls import OnSetCls
from betty.dirs import builtin_asset_directory
from betty.document import Document, DocumentProviderDefinition
from betty.entity import EntityDefinition
from betty.entity.collection.pool import EntityPool
from betty.event_type import EventTypeDefinition
from betty.exception import HumanFacingException
from betty.freezer import Frozen
from betty.gender import GenderDefinition
from betty.gettext import TranslationsRepository
from betty.hashid import hashid
from betty.html.css import CssResourceDefinition
from betty.html.js import JsResourceDefinition
from betty.jinja.filter import JinjaFilterDefinition
from betty.jinja.test import JinjaTestDefinition
from betty.license import License, LicenseDefinition, LicenseManufacturer
from betty.licenses.all_rights_reserved import AllRightsReserved
from betty.link import LinkDefinition
from betty.load import (
    Enricher,
    EnricherDefinition,
    EnricherManufacturer,
    Loader,
    LoaderDefinition,
    LoaderManufacturer,
)
from betty.locale import (
    ResolvableLocale,
    default_locale,
    resolve_locale,
    to_language_tag,
)
from betty.localizable import resolve_localizable
from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.localizer import Localizer, LocalizerRepository
from betty.machine_name import MachineName, ResolvableMachineName
from betty.pathlib import resolve_path
from betty.place_type import PlaceTypeDefinition
from betty.plugin.resolve import (
    ResolvablePluginDefinition,
    ResolvablePluginId,
    resolve_plugin_id,
)
from betty.portable import KeyedPorter
from betty.porters.fields import FieldsPorter
from betty.porters.keyed_mapping import KeyedMappingPorter
from betty.porters.omit_field import OmitFieldPorter
from betty.privacy.privatizer import Privatizer
from betty.prop import HasProps
from betty.render import RenderDispatcher, RendererDefinition
from betty.requirements.service_level import RequirableServiceLevel
from betty.role import RoleDefinition
from betty.sample import Sample, Size
from betty.search import Search
from betty.server import ServerDefinition
from betty.service import (
    Service,
)
from betty.service_level import DownstreamServiceLevel, Plugins
from betty.service_provider import (
    ServiceProvider,
    ServiceProviderDefinition,
    ServiceProviderManufacturer,
)
from betty.services.asset import AssetRepositoryService
from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.collection.keyed import PluginDefinitionsService
from betty.services.plugin.instance.collection.keyed import PluginInstancesService
from betty.services.plugin.instance.single import PluginInstanceService
from betty.services.simple import service
from betty.store import TransientStore
from betty.stores.file import TransientBinaryFileStore, TransientPickledFileStore
from betty.stores.no_op import NoOpStore
from betty.url_generators import entity_type as entity_type

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable, Sequence
    from pathlib import Path

    from betty.asset import AssetDirectoryDefinition
    from betty.collection.keyed import KeyedCollection
    from betty.jinja import Environment
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.media_type import ResolvableMediaType
    from betty.pathlib import StrPath
    from betty.plugin import PluginDefinition
    from betty.plugin.discovery import ResolvableDiscovery as ResolvableDiscovery
    from betty.plugin.factory import (
        ResolvablePluginManufacturer,
        ResolvablePluginManufacturerSequence,
    )
    from betty.services.plugin import SupportedPlugins
    from betty.services.plugin.instance import (
        ServicePluginInstance,
        ServicePluginInstances,
    )
    from betty.services.simple.synchronous import TypedSynchronousServiceOrFactory
    from betty.url_generator import UrlGenerator


default_lifetime_threshold: Final[int] = 123
"""
The default age by which people are presumed dead.

This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
the oldest verified person to ever have lived.
"""


@final
class Project(DownstreamServiceLevel[App], RequirableServiceLevel, HasPluginServices):
    """
    Define a Betty project.

    A project combines project configuration and the resulting ancestry.

    .. list-table::
       :widths: 10 20
       :header-rows: 0

       * - Configuration
         - :py:class:`betty.project.ProjectData`
    """

    asset_directories = AssetRepositoryService()
    copyright_notice = PluginInstanceService(CopyrightNoticeDefinition)
    css_resources = PluginDefinitionsService(CssResourceDefinition)
    document_providers = PluginInstancesService(DocumentProviderDefinition)
    enrichers = PluginInstancesService(EnricherDefinition)
    jinja_filters = PluginInstancesService(JinjaFilterDefinition)
    jinja_tests = PluginInstancesService(JinjaTestDefinition)
    js_resources = PluginDefinitionsService(JsResourceDefinition)
    license = PluginInstanceService(LicenseDefinition)
    links = PluginDefinitionsService(LinkDefinition)
    loaders = PluginInstancesService(LoaderDefinition)
    renderers = PluginInstancesService(RendererDefinition)
    servers = PluginInstancesService(ServerDefinition)
    service_providers = PluginInstancesService(ServiceProviderDefinition)

    def __init__(
        self,
        directory: StrPath,
        *,
        app: App,
        title: ResolvableLocalizable,
        url: str,
        ancestry: EntityPool | None = None,
        assets: Iterable[ResolvablePluginDefinition[AssetDirectoryDefinition]] = (),
        author: ResolvableLocalizable | None = None,
        cache: TypedSynchronousServiceOrFactory[Project, TransientStore[Any]]
        | None = None,
        clean_urls: bool = False,
        copyright_notice: ServicePluginInstance[CopyrightNoticeDefinition]
        | None = None,
        debug: bool = False,
        enrichers: ServicePluginInstances[EnricherDefinition] = (),
        service_providers: ServicePluginInstances[ServiceProviderDefinition] = (),
        generate_entity_list_html: Iterable[ResolvablePluginId[EntityDefinition]] = (),
        license: ServicePluginInstance[LicenseDefinition] | None = None,  # noqa: A002
        lifetime_threshold: int | None = None,
        links: Iterable[ResolvablePluginDefinition[LinkDefinition]] = (),
        loaders: ServicePluginInstances[LoaderDefinition] = (),
        locales: Iterable[ProjectLocale | ResolvableLocale] = (),
        localizers: TypedSynchronousServiceOrFactory[Project, LocalizerRepository]
        | None = None,
        logo: StrPath | None = None,
        name: ResolvableMachineName | None = None,
        plugins: Plugins = _empty_frozen_mapping,
        servers: ServicePluginInstances[ServerDefinition] = (),
        supported_plugins: SupportedPlugins = (),
        _plugin_discoveries: Iterable[PluginDefinition] = (),
    ):
        from betty.copyright_notices.project_author import ProjectAuthor

        cls = type(self)
        if cache is not None:
            cls.cache.override(
                self, Service(cache) if isinstance(cache, TransientStore) else cache
            )
        if localizers is not None:
            cls.localizers.override(
                self,
                Service(localizers)
                if isinstance(localizers, LocalizerRepository)
                else localizers,
            )
        super().__init__(
            plugins=plugins, supported_plugins=supported_plugins, upstream=app
        )
        cls.asset_directories.add_init_plugins(self, *assets)
        cls.copyright_notice.add_init_plugins(self, copyright_notice or ProjectAuthor)
        cls.enrichers.add_init_plugins(self, *enrichers)
        cls.service_providers.add_init_plugins(self, *service_providers)
        cls.license.add_init_plugins(self, license or AllRightsReserved)
        cls.links.add_init_plugins(self, *links)
        cls.loaders.add_init_plugins(self, *loaders)
        cls.servers.add_init_plugins(self, *servers)
        self.ancestry: Final[EntityPool] = (
            EntityPool() if ancestry is None else ancestry
        )
        """
        The project's ancestry.
        """
        self.author: Final[Localizable | None] = (
            None if author is None else resolve_localizable(author)
        )
        """
        The project's author.
        """
        self.clean_urls: Final[bool] = clean_urls
        """
        Whether to generate clean URLs such as ``/person/first-person`` instead of ``/person/first-person/index.html``.

        Generated artifacts will require web server that supports this.
        """
        self.debug: Final[bool] = debug
        """
        Whether to enable debugging for project jobs.

        This setting is disabled by default.

        Enabling this generally results in:

        - More verbose logging output
        - job artifacts (e.g. generated sites)
        """
        self.directory: Final[Path] = resolve_path(directory)
        """
        The project directory path.

        Betty will look for resources in this directory, and place generated artifacts there. It is expected
        that no other applications or projects share this same directory.
        """
        self.output_directory: Final[Path] = self.directory / "output"
        """
        The output directory path.
        """
        self.asset_directory: Final[Path] = self.directory / "asset"
        """
        The :doc:`asset directory path </usage/assets>`.
        """

        self.www_directory: Final[Path] = self.output_directory / "www"
        """
        The WWW directory path.
        """
        self._generate_entity_list_html = (
            ()
            if generate_entity_list_html is None
            else tuple(map(resolve_plugin_id, generate_entity_list_html))
        )
        self.lifetime_threshold: Final[int] = (
            lifetime_threshold or default_lifetime_threshold
        )
        """
        The lifetime threshold indicates when people are considered dead.

        This setting defaults to :py:const:`betty.project.default_lifetime_threshold`.

        The value is an integer expressing the age in years over which people are
        presumed to have died.
        """
        self.locales: KeyedCollection[Locale, ResolvableLocale, ProjectLocale] = (
            KeyedCollectionAdapter(
                {
                    project_locale.locale: project_locale
                    for locale in (locales or (default_locale,))
                    if (
                        project_locale := locale
                        if isinstance(locale, ProjectLocale)
                        else ProjectLocale(resolve_locale(locale))
                    )
                },
                key_resolver=resolve_locale,
            )
        )
        """
        The project locales.
        """
        self.default_locale: Final[ProjectLocale] = next(iter(self.locales))
        """
        The default locale.
        """
        self.multilingual: Final[bool] = len(self.locales) > 1
        """
        Whether the project is multilingual.
        """
        self.logo: Final[Path] = (
            builtin_asset_directory / "public" / "static" / "betty-512x512.png"
            if logo is None
            else resolve_path(logo)
        )
        """
        The path to the logo file.
        """
        self.name: Final[MachineName] = (
            MachineName(hashid(str(directory)))
            if name is None
            else MachineName.resolve(name)
        )
        """
        The project name.

        If no project name was configured, this defaults to the hash of the project directory path.
        """
        self._plugin_discoveries = _plugin_discoveries
        self.title: Final[Localizable] = (
            None if title is None else resolve_localizable(title)
        )
        """
        The human-readable project title.
        """
        self.url: Final[str] = url
        """
        The project's public URL.
        """
        url_parts = urlsplit(self.url)
        self.base_url: Final[str] = f"{url_parts.scheme}://{url_parts.netloc}"
        """
        The project's public URL's base URL.

        If the public URL is ``https://example.com``, the base URL is ``https://example.com``.
        If the public URL is ``https://example.com/my-ancestry-site``, the base URL is ``https://example.com``.
        If the public URL is ``https://my-ancestry-site.example.com``, the base URL is ``https://my-ancestry-site.example.com``.
        """
        self.root_path: Final[str] = url_parts.path.rstrip("/")
        """
        The project's public URL's root path.

        If the public URL is ``https://example.com``, the root path is an empty string.
        If the public URL is ``https://example.com/my-ancestry-site``, the root path is ``/my-ancestry-site``.
        """
        self._cache_directory = self.directory / ".cache" / version_major

    @classmethod
    async def new(cls, app: App, data: ProjectData, *, directory: StrPath) -> Self:
        """
        Create a new instance.
        """
        return cls(
            directory,
            _plugin_discoveries=(
                plugin.new_plugin()
                for plugin in (
                    *data.copyright_notices,
                    *data.genders,
                    *data.licenses,
                    *data.place_types,
                    *data.roles,
                )
            ),
            app=app,
            author=data.author,
            clean_urls=data.clean_urls,
            copyright_notice=data.copyright_notice,
            debug=data.debug,
            enrichers=data.enrichers,
            license=data.license,
            lifetime_threshold=data.lifetime_threshold,
            loaders=data.loaders,
            locales=data.locales,
            logo=data.logo,
            service_providers=data.service_providers,
            title=data.title,
            url=data.url,
        )

    @classmethod
    @asynccontextmanager
    async def new_isolated(
        cls,
        *,
        ancestry: EntityPool | None = None,
        app: App | None = None,
        assets: Iterable[ResolvablePluginDefinition[AssetDirectoryDefinition]] = (),
        author: ResolvableLocalizable | None = None,
        cache: TypedSynchronousServiceOrFactory[Project, TransientStore[Any]]
        | None
        | Literal[False] = False,
        clean_urls: bool = False,
        debug: bool = False,
        directory: StrPath | None = None,
        enrichers: ServicePluginInstances[EnricherDefinition] = (),
        generate_entity_list_html: Iterable[ResolvablePluginId[EntityDefinition]] = (),
        service_providers: ServicePluginInstances[ServiceProviderDefinition] = (),
        lifetime_threshold: int | None = None,
        links: Iterable[ResolvablePluginDefinition[LinkDefinition]] = (),
        loaders: ServicePluginInstances[LoaderDefinition] = (),
        locales: Iterable[ProjectLocale | ResolvableLocale] = (),
        localizers: TypedSynchronousServiceOrFactory[Project, LocalizerRepository]
        | None = None,
        logo: StrPath | None = None,
        name: ResolvableMachineName | None = None,
        plugins: Plugins = _empty_frozen_mapping,
        servers: ServicePluginInstances[ServerDefinition] = (),
        supported_plugins: SupportedPlugins = (),
        title: ResolvableLocalizable | None = None,
        url: str | None = None,
    ) -> AsyncIterator[Self]:
        """
        Creat a new, isolated, temporary project.

        The project will not leave any traces on the system, except when it uses
        global Betty functionality such as caches.
        """
        async with AsyncExitStack() as exit_stack:
            if app is None:
                app = await exit_stack.enter_async_context(App.new_isolated())
            if directory is None:
                directory: StrPath = await to_thread(mkdtemp)  # ty:ignore[invalid-assignment]
                exit_stack.push_async_callback(
                    to_thread, rmtree, directory, ignore_errors=True
                )
            async with cls(
                directory,
                ancestry=ancestry,
                app=app,
                assets=assets,
                author=author,
                cache=NoOpStore() if cache is False else cache,
                clean_urls=clean_urls,
                debug=debug,
                enrichers=enrichers,
                service_providers=service_providers,
                generate_entity_list_html=generate_entity_list_html,
                lifetime_threshold=lifetime_threshold,
                links=links,
                loaders=loaders,
                locales=locales,
                localizers=localizers or LocalizerRepository(),
                logo=logo,
                name=name,
                plugins=plugins,
                servers=servers,
                supported_plugins=supported_plugins,
                title=title or "Betty",
                url=url or "https://example.com",
            ) as project:
                yield project

    def localize_www_directory(self, locale: Locale) -> Path:
        """
        Get the WWW directory path for a locale.
        """
        if self.multilingual:
            return self.www_directory / self.locales[locale].slug
        return self.www_directory

    @service
    async def generate_entity_list_html(
        self,
    ) -> KeyedCollection[
        MachineName, ResolvablePluginId[EntityDefinition], EntityDefinition
    ]:
        """
        Which entity types to generate list HTML pages for.
        """
        if self._generate_entity_list_html is None:
            entity_types = [
                entity_type
                async for entity_type in self.plugins[EntityDefinition]
                if entity_type.public_facing
            ]
        else:
            entity_types = await gather(
                *map(
                    self.plugins[EntityDefinition].get, self._generate_entity_list_html
                )
            )
        return KeyedCollectionAdapter(
            {entity_type.id: entity_type for entity_type in entity_types},
            key_resolver=resolve_plugin_id,
        )

    @service
    def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        return LocalizerRepository(
            translations=TranslationsRepository(
                assets=self.asset_directories, cache=self.binary_file_cache
            )
        )

    @service
    async def public_localizers(self) -> Sequence[Localizer]:
        """
        The public localizers.
        """
        return await gather(*[
            self.localizers.get(locale.locale) for locale in self.locales
        ])

    @service
    async def url_generator(self) -> UrlGenerator:
        """
        The URL generator.
        """
        from betty.url_generators.dispatcher import UrlGeneratorDispatcher
        from betty.url_generators.entity import EntityUrlGenerator
        from betty.url_generators.entity_type import EntityTypeUrlGenerator
        from betty.url_generators.entity_url import EntityUrlUrlGenerator
        from betty.url_generators.localized_path_url import LocalizedPathUrlUrlGenerator
        from betty.url_generators.passthrough import PassthroughUrlGenerator
        from betty.url_generators.path import PathUrlGenerator
        from betty.url_generators.static_path_url import StaticPathUrlUrlGenerator

        path_url_generator = await PathUrlGenerator.new(self)
        entity_url_generator = EntityUrlGenerator(path_url_generator)
        return UrlGeneratorDispatcher(
            EntityTypeUrlGenerator(path_url_generator),
            entity_url_generator,
            EntityUrlUrlGenerator(self.ancestry, entity_url_generator),
            LocalizedPathUrlUrlGenerator(path_url_generator),
            StaticPathUrlUrlGenerator(path_url_generator),
            PassthroughUrlGenerator(),
        )

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
        The content renderer.
        """
        return RenderDispatcher(*await gather(*self.renderers))

    @service
    def privatizer(self) -> Privatizer:
        """
        The privatizer.
        """
        return Privatizer(self.lifetime_threshold, user=self.upstream.user)

    async def new_document(
        self,
        resource: object = None,
        resource_url: object = None,
        /,
        *,
        media_type: ResolvableMediaType | None = None,
        **document_vars: Any,
    ) -> Document:
        """
        Create a new document.
        """
        return Document(
            resource,
            resource_url,
            media_type=media_type,
            **{
                key: value
                for document_provider in await gather(*self.document_providers)
                for (key, value) in document_provider.new_document_vars().items()
            },
            **document_vars,
        )

    @service
    def cache(self) -> TransientStore[Any]:
        """
        The project cache.
        """
        return TransientPickledFileStore[Any](self._cache_directory)

    @service
    def binary_file_cache(self) -> TransientBinaryFileStore:
        """
        The project binary file cache.
        """
        return TransientBinaryFileStore(self._cache_directory)

    @service
    async def search(self) -> Search:
        """
        The search index.
        """
        return Search(
            {
                entity_type.id: entity_type
                async for entity_type in self.plugins[EntityDefinition]
            },
            project=self,
        )


@final
@ObjectDefinition(
    label=_("Project locale"),
    porter=OnSetCls(
        lambda definition: KeyedMappingPorter("locale", FieldsPorter(definition))
    ),
    samples=[
        lambda: Sample(
            ProjectLocale(Locale("nl", "NL")), label="Minimal", size=Size.MINIMAL
        ),
        lambda: Sample(
            ProjectLocale(Locale("nl", "NL"), alias="nl"),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class ProjectLocale(
    Data[ObjectDefinition["ProjectLocale", Never, KeyedPorter["ProjectLocale"]]],
    HasProps,
    Frozen,
):
    """
    A locale to use for a project.

    .. data:: betty.project:ProjectLocale
    """

    locale = new_locale_attr()
    """
    The locale.
    """

    alias = OwnerAttr(StrDefinition(label=_("Alias"))).optional
    """
    A shorthand alias to use instead of the full language tag, such as when rendering URLs.
    """

    def __init__(self, /, locale: ResolvableLocale, *, alias: str | None = None):
        super().__init__()
        self.locale = locale
        if alias is not None and "/" in alias:
            raise HumanFacingException(_("Locale aliases must not contain slashes."))
        self.alias = alias
        self.slug: Final[str] = alias or to_language_tag(self.locale)
        """
        The URL slug.
        """


@final
@ObjectDefinition(
    label=_("Project configuration"),
    samples=[
        lambda: Sample(
            ProjectData(title="Betty", url="https://example.com"),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            ProjectData(
                author="Bart Feenstra",
                clean_urls=True,
                copyright_notice=CopyrightNoticeManufacturer
                .data()
                .samples.get(Size.FULL)
                .subject,
                copyright_notices=[
                    CopyrightNoticeDefinitionData.data().samples.get(Size.FULL).subject
                ],
                debug=True,
                generate_entity_list_html=["person", "place"],
                event_types=[
                    EventTypeDefinitionData.data().samples.get(Size.FULL).subject
                ],
                genders=[GenderDefinitionData.data().samples.get(Size.FULL).subject],
                logo=builtin_asset_directory
                / "public"
                / "static"
                / "betty-512x512.png",
                license=LicenseManufacturer.data().samples.get(Size.FULL).subject,
                licenses=[LicenseDefinitionData.data().samples.get(Size.FULL).subject],
                lifetime_threshold=123,
                locales=[ProjectLocale.data().samples.get(Size.FULL).subject],
                name="betty-ancestry",
                place_types=[
                    PlaceTypeDefinitionData.data().samples.get(Size.FULL).subject
                ],
                roles=[RoleDefinitionData.data().samples.get(Size.FULL).subject],
                title="Betty's ancestry",
                url="https://ancestry.example.com/betty",
            ),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class ProjectData(Data, HasProps):
    """
    Configuration for a :py:class:`betty.project.Project`.

    .. data:: betty.project:ProjectData
    """

    author = new_localizable_attr(label=_("Author")).optional
    """
    The project's author.
    """

    clean_urls = OwnerAttr(
        BoolDefinition(
            label=_("Clean URLs"),
            description=_(
                "Whether to use clean URLs: {clean_example} instead of {unclean_example}."
            ).format(
                clean_example=Quote("/path"), unclean_example=Quote("/path/index.html")
            ),
        )
    ).default(lambda: False)
    """
    Whether to generate clean URLs.
    """

    copyright_notice = OwnerAttr(CopyrightNoticeManufacturer).setter(
        CopyrightNoticeManufacturer.resolve
    )
    """
    The project-wide copyright notice.
    """

    @copyright_notice.default
    def copyright_notice(self) -> CopyrightNoticeManufacturer:  # noqa: D102
        from betty.copyright_notices.project_author import ProjectAuthor

        return CopyrightNoticeManufacturer(ProjectAuthor)

    copyright_notices = new_plugin_definition_datas_attr(
        CopyrightNoticeDefinition, CopyrightNoticeDefinitionData
    )
    """
    The :py:class:`betty.copyright_notice.CopyrightNotice` plugins created by this project.
    """

    debug = OwnerAttr(
        BoolDefinition(
            label=_("Debugging mode"),
            description=_(
                "Whether to output more detailed logs and disable optimizations that make debugging harder."
            ),
        )
    ).default(lambda: False)
    """
    Whether to enable debugging for project jobs.
    """

    enrichers = CollectionOwnerAttr(
        FieldDefinition(
            KeyedCollectionDefinition(
                value=EnricherManufacturer,
                label=EnricherDefinition.type().label_plural,
                factory=lambda: MutableKeyedCollectionAdapter(
                    key=lambda data: data.plugin_id,
                    key_resolver=resolve_plugin_id,
                    value_resolver=EnricherManufacturer.resolve,
                ),
            ),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
    )
    """
    The enrichers to enable for the project.
    """

    event_types = new_plugin_definition_datas_attr(
        EventTypeDefinition, EventTypeDefinitionData
    )
    """
    The :py:class:`betty.event_type.EventType` plugins created by this project.
    """

    service_providers = CollectionOwnerAttr(
        FieldDefinition(
            KeyedCollectionDefinition(
                value=ServiceProviderManufacturer,
                label=ServiceProviderDefinition.type().label_plural,
                factory=lambda: MutableKeyedCollectionAdapter(
                    key=lambda data: data.plugin_id,
                    key_resolver=resolve_plugin_id,
                    value_resolver=ServiceProviderManufacturer.resolve,
                ),
            ),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
    )
    """
    The service providers to enable for the project.
    """

    generate_entity_list_html = CollectionOwnerAttr(
        FieldDefinition(
            SequenceDefinition[
                MutableSequence[ResolvablePluginId[EntityDefinition]],
                ResolvablePluginId[EntityDefinition],
            ](
                cls=list,
                label=_("Entity types to generate list HTML pages for"),
                value=MachineName,
                factory=lambda: MutableResolvedSequenceAdapter(
                    [], value_resolver=resolve_plugin_id
                ),
            ),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
    )
    """
    Which entity types to generate list HTML pages for.
    """

    genders = new_plugin_definition_datas_attr(GenderDefinition, GenderDefinitionData)
    """
    The :py:class:`betty.gender.Gender` plugins created by this project.
    """

    license = OwnerAttr(LicenseManufacturer).setter(LicenseManufacturer.resolve)
    """
    The project-wide license.
    """

    @license.default  # noqa: A003
    def license(self) -> LicenseManufacturer:  # noqa: D102
        return LicenseManufacturer(AllRightsReserved)

    licenses = new_plugin_definition_datas_attr(
        LicenseDefinition, LicenseDefinitionData
    )
    """
    The :py:class:`betty.license.License` plugins created by this project.
    """

    lifetime_threshold = (
        OwnerAttr(
            IntDefinition(
                label=_("Lifetime threshold"),
                description=_(
                    "The number of years people are expected to live at most, e.g. after which they are presumed to have died."
                ),
            )
        )
        .setter(assert_int(minimum=1))
        .default(lambda: default_lifetime_threshold)
    )
    """
    The lifetime threshold indicates when people are considered dead.
    """

    loaders = CollectionOwnerAttr(
        FieldDefinition(
            KeyedCollectionDefinition(
                value=LoaderManufacturer,
                label=LoaderDefinition.type().label_plural,
                factory=lambda: MutableKeyedCollectionAdapter(
                    key=lambda data: data.plugin_id,
                    key_resolver=resolve_plugin_id,
                    value_resolver=LoaderManufacturer.resolve,
                ),
            ),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
    )
    """
    The loaders to enable for the project.
    """

    locales = CollectionOwnerAttr(
        FieldDefinition(
            KeyedCollectionDefinition(
                value=ProjectLocale,
                label=_("Locales"),
                order_dump=True,
                factory=lambda: MutableKeyedCollectionAdapter(
                    key=lambda item: item.locale,
                    key_resolver=resolve_locale,
                    value_resolver=lambda value: (
                        value
                        if isinstance(value, ProjectLocale)
                        else ProjectLocale(resolve_locale(value))
                    ),
                ),
            ),
            optional=True,
            porter=OmitFieldPorter.new(not_),
        )
    ).default(lambda: [default_locale])
    """
    The configured locales.
    """

    logo = new_path_attr(label=_("Logo")).optional
    """
    The project logo.
    """

    name = new_machine_name_attr().optional
    """
    The project's machine name.
    """

    place_types = new_plugin_definition_datas_attr(
        PlaceTypeDefinition, PlaceTypeDefinitionData
    )
    """
    The :py:class:`betty.place_type.PlaceType` plugins created by this project.
    """

    roles = new_plugin_definition_datas_attr(RoleDefinition, RoleDefinitionData)
    """
    The :py:class:`betty.role.Role` plugins created by this project.
    """

    title = new_localizable_attr(label=_("Title"))
    """
    The human-readable project title.
    """

    url = OwnerAttr(
        StrDefinition(
            label=_("URL"),
            description=_(
                "The absolute, public URL at which the site will be published."
            ),
        )
    ).setter(assert_url())
    """
    The project's public URL.
    """

    def __init__(
        self,
        *,
        title: ResolvableLocalizable,
        url: str,
        author: ResolvableLocalizable | None = None,
        clean_urls: bool = False,
        copyright_notice: ResolvablePluginManufacturer[
            CopyrightNoticeDefinition, CopyrightNotice
        ]
        | None = None,
        copyright_notices: Iterable[CopyrightNoticeDefinitionData] = (),
        debug: bool = False,
        enrichers: ResolvablePluginManufacturerSequence[
            EnricherDefinition, Enricher
        ] = (),
        event_types: Iterable[EventTypeDefinitionData] = (),
        service_providers: ResolvablePluginManufacturerSequence[
            ServiceProviderDefinition, ServiceProvider
        ] = (),
        generate_entity_list_html: Iterable[ResolvablePluginId[EntityDefinition]] = (),
        genders: Iterable[GenderDefinitionData] = (),
        license: ResolvablePluginManufacturer[LicenseDefinition, License] | None = None,  # noqa: A002
        licenses: Iterable[LicenseDefinitionData] = (),
        lifetime_threshold: int = default_lifetime_threshold,
        loaders: ResolvablePluginManufacturerSequence[LoaderDefinition, Loader] = (),
        locales: Iterable[ResolvableLocale | ProjectLocale] = (),
        logo: StrPath | None = None,
        name: ResolvableMachineName | None = None,
        place_types: Iterable[PlaceTypeDefinitionData] = (),
        roles: Iterable[RoleDefinitionData] = (),
    ):
        super().__init__()
        self.author = author
        self.clean_urls = clean_urls
        if copyright_notice is not None:
            self.copyright_notice = CopyrightNoticeManufacturer.resolve(
                copyright_notice
            )
        if copyright_notices is not None:
            self.copyright_notices = copyright_notices
        self.debug = debug
        self.enrichers = enrichers
        self.event_types = event_types
        self.service_providers = service_providers
        self.generate_entity_list_html = generate_entity_list_html
        self.genders = genders
        if license is not None:
            self.license = LicenseManufacturer.resolve(license)
        self.licenses = licenses
        self.lifetime_threshold = lifetime_threshold
        self.loaders = loaders
        if logo is not None:
            self.logo = resolve_path(logo)
        self.locales = locales
        self.name = name
        self.place_types = place_types
        self.roles = roles
        self.title = title
        self.url = url
