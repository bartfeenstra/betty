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
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, Literal, Self, final
from urllib.parse import urlsplit

from babel import Locale

from betty.about import VERSION_MAJOR
from betty.app import App
from betty.assertion import assert_number, assert_url
from betty.asset import AssetRepositoryService
from betty.attrs.attr import AttrAttr
from betty.attrs.collection.keyed import KeyedCollectionAttr
from betty.attrs.collection.sequence import SequenceAttr
from betty.attrs.localizable import LocalizableAttr
from betty.attrs.machine_name import MachineNameAttr
from betty.attrs.optional import Optional
from betty.attrs.plugin_definitions import PluginDefinitionDatasAttr
from betty.cache import Cache
from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.cache.no_op import NoOpCache
from betty.collection.keyed.adapter import (
    KeyedCollectionAdapter,
    MutableKeyedCollectionAdapter,
)
from betty.collection.sequence.adapter import MutableResolvedSequenceAdapter
from betty.copyright_notice import (
    CopyrightNotice,
    CopyrightNoticeDefinition,
    CopyrightNoticeManufacturer,
)
from betty.data import Data
from betty.datas.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record.object import AttrDefinition, ObjectDefinition
from betty.datas.bool import BoolDefinition
from betty.datas.copyright_notice_definition import CopyrightNoticeDefinitionData
from betty.datas.event_type_definition import EventTypeDefinitionData
from betty.datas.gender_definition import GenderDefinitionData
from betty.datas.int import IntDefinition
from betty.datas.license_definition import LicenseDefinitionData
from betty.datas.locale import LocaleDefinition
from betty.datas.path import PathDefinition
from betty.datas.place_type_definition import PlaceTypeDefinitionData
from betty.datas.role_definition import RoleDefinitionData
from betty.datas.str import StrDefinition
from betty.dirs import BUILTIN_ASSET_DIRECTORY
from betty.document import Document, DocumentProviderDefinition
from betty.entity import EntityDefinition
from betty.entity.collection.pool import EntityPool
from betty.event_type import EventTypeDefinition
from betty.exception import HumanFacingException
from betty.extension import Extension, ExtensionDefinition, ExtensionManufacturer
from betty.gender import GenderDefinition
from betty.hashid import hashid
from betty.html.css import CssResourceDefinition
from betty.html.js import JsResourceDefinition
from betty.indicator.selector import Attr as AttrSelector
from betty.jinja.filter import JinjaFilterDefinition
from betty.jinja.test import JinjaTestDefinition
from betty.license import License, LicenseDefinition, LicenseManufacturer
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
    DEFAULT_LOCALE,
    ResolvableLocale,
    resolve_locale,
    to_language_tag,
)
from betty.locale.localizable import resolve_localizable
from betty.locale.localizable.gettext import _
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import AssetTranslationRepository, TranslationRepository
from betty.machine_name import MachineName, ResolvableMachineName
from betty.pathlib import resolve_path
from betty.place_type import PlaceTypeDefinition
from betty.plugin.resolve import (
    ResolvablePluginDefinition,
    ResolvablePluginId,
    resolve_plugin_id,
)
from betty.privacy.privatizer import Privatizer
from betty.render import RenderDispatcher, RendererDefinition
from betty.role import RoleDefinition
from betty.sample import Sample, Size
from betty.server import ServerDefinition
from betty.service import Service
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.definition.collection.keyed import PluginDefinitionsService
from betty.service.plugin.instance.collection.keyed import PluginInstancesService
from betty.service.plugin.instance.single import PluginInstanceService
from betty.service.simple import service
from betty.service_level import DownstreamServiceLevel
from betty.service_level.requirement import RequirableServiceLevel

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
    from pathlib import Path

    from betty.asset import AssetDirectoryDefinition
    from betty.collection.keyed import KeyedCollection
    from betty.jinja import Environment
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.media_type import ResolvableMediaType
    from betty.pathlib import StrPath
    from betty.plugin import PluginDefinition
    from betty.plugin.discovery import ResolvableDiscovery
    from betty.plugin.factory import (
        ResolvablePluginManufacturer,
        ResolvablePluginManufacturerSequence,
    )
    from betty.service.plugin import SupportedPlugins
    from betty.service.plugin.instance import (
        ServicePluginInstance,
        ServicePluginInstances,
    )
    from betty.service.simple.synchronous import TypedSynchronousServiceOrFactory
    from betty.url import UrlGenerator


DEFAULT_LIFETIME_THRESHOLD = 123
"""
The default age by which people are presumed dead.

This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
the oldest verified person to ever have lived.
"""


@final
class Project(
    DownstreamServiceLevel[App], RequirableServiceLevel, PluginServiceProvider
):
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
    extensions = PluginInstancesService(ExtensionDefinition)
    jinja_filters = PluginInstancesService(JinjaFilterDefinition)
    jinja_tests = PluginInstancesService(JinjaTestDefinition)
    js_resources = PluginDefinitionsService(JsResourceDefinition)
    license = PluginInstanceService(LicenseDefinition)
    links = PluginDefinitionsService(LinkDefinition)
    loaders = PluginInstancesService(LoaderDefinition)
    renderers = PluginInstancesService(RendererDefinition)
    servers = PluginInstancesService(ServerDefinition)

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
        cache: TypedSynchronousServiceOrFactory[Project, Cache[Any]] | None = None,
        clean_urls: bool = False,
        copyright_notice: ServicePluginInstance[CopyrightNoticeDefinition]
        | None = None,
        debug: bool = False,
        enrichers: ServicePluginInstances[EnricherDefinition] = (),
        extensions: ServicePluginInstances[ExtensionDefinition] = (),
        generate_entity_list_html: Iterable[ResolvablePluginId[EntityDefinition]]
        | None = None,
        license: ServicePluginInstance[LicenseDefinition] | None = None,  # noqa: A002
        lifetime_threshold: int | None = None,
        links: Iterable[ResolvablePluginDefinition[LinkDefinition]] = (),
        loaders: ServicePluginInstances[LoaderDefinition] = (),
        locales: Iterable[ProjectLocale | ResolvableLocale] = (),
        logo: StrPath | None = None,
        name: ResolvableMachineName | None = None,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
        servers: ServicePluginInstances[ServerDefinition] = (),
        supported_plugins: SupportedPlugins = (),
        _plugin_discoveries: Iterable[PluginDefinition] = (),
    ):
        from betty.plugins.copyright_notice.project_author import ProjectAuthor
        from betty.plugins.license.all_rights_reserved import AllRightsReserved

        cls = type(self)
        if cache is not None:
            cls.cache.override(
                self, Service(cache) if isinstance(cache, Cache) else cache
            )
        super().__init__(
            plugins=plugins, supported_plugins=supported_plugins, upstream=app
        )
        cls.asset_directories.add_init_plugins(self, *assets)
        cls.copyright_notice.add_init_plugins(self, copyright_notice or ProjectAuthor)
        cls.enrichers.add_init_plugins(self, *enrichers)
        cls.extensions.add_init_plugins(self, *extensions)
        cls.license.add_init_plugins(self, license or AllRightsReserved)
        cls.links.add_init_plugins(self, *links)
        cls.loaders.add_init_plugins(self, *loaders)
        cls.servers.add_init_plugins(self, *servers)
        self._ancestry = EntityPool() if ancestry is None else ancestry
        self._author = None if author is None else resolve_localizable(author)
        self._clean_urls = clean_urls
        self._debug = debug
        self._directory = resolve_path(directory)
        self._generate_entity_list_html = (
            ()
            if generate_entity_list_html is None
            else tuple(map(resolve_plugin_id, generate_entity_list_html))
        )
        self._lifetime_threshold = lifetime_threshold or DEFAULT_LIFETIME_THRESHOLD
        self._locales = KeyedCollectionAdapter(
            {
                project_locale.locale: project_locale
                for locale in (locales or (DEFAULT_LOCALE,))
                if (
                    project_locale := locale
                    if isinstance(locale, ProjectLocale)
                    else ProjectLocale(resolve_locale(locale))
                )
            },
            key_resolver=resolve_locale,
        )
        self._logo = (
            BUILTIN_ASSET_DIRECTORY / "public" / "static" / "betty-512x512.png"
            if logo is None
            else resolve_path(logo)
        )
        self._name = (
            MachineName(hashid(str(directory)))
            if name is None
            else MachineName.resolve(name)
        )
        self._plugin_discoveries = _plugin_discoveries
        self._title = None if title is None else resolve_localizable(title)
        self._url = url
        url_parts = urlsplit(self.url)
        self._base_url = f"{url_parts.scheme}://{url_parts.netloc}"
        self._root_path = url_parts.path.rstrip("/")
        self._cache_directory = self.directory / ".cache" / VERSION_MAJOR

    @classmethod
    async def new(cls, app: App, data: ProjectData, *, directory: StrPath) -> Self:
        """
        Create a new instance.
        """
        return cls(
            directory,
            _plugin_discoveries=(
                *data.copyright_notices,
                *data.genders,
                *data.licenses,
                *data.place_types,
                *data.roles,
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
            extensions=data.extensions,
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
        cache: TypedSynchronousServiceOrFactory[Project, Cache[Any]]
        | None
        | Literal[False] = False,
        clean_urls: bool = False,
        debug: bool = False,
        directory: StrPath | None = None,
        enrichers: ServicePluginInstances[EnricherDefinition] = (),
        generate_entity_list_html: Iterable[ResolvablePluginId[EntityDefinition]]
        | None = None,
        extensions: ServicePluginInstances[ExtensionDefinition] = (),
        lifetime_threshold: int | None = None,
        links: Iterable[ResolvablePluginDefinition[LinkDefinition]] = (),
        loaders: ServicePluginInstances[LoaderDefinition] = (),
        locales: Iterable[ProjectLocale | ResolvableLocale] = (),
        logo: StrPath | None = None,
        name: ResolvableMachineName | None = None,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
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
                cache=NoOpCache() if cache is False else cache,
                clean_urls=clean_urls,
                debug=debug,
                enrichers=enrichers,
                extensions=extensions,
                generate_entity_list_html=generate_entity_list_html,
                lifetime_threshold=lifetime_threshold,
                links=links,
                loaders=loaders,
                locales=locales,
                logo=logo,
                name=name,
                plugins=plugins,
                servers=servers,
                supported_plugins=supported_plugins,
                title=title or "Betty",
                url=url or "https://example.com",
            ) as project:
                yield project

    @property
    def directory(self) -> Path:
        """
        The project directory path.

        Betty will look for resources in this directory, and place generated artifacts there. It is expected
        that no other applications or projects share this same directory.
        """
        return self._directory

    @property
    def output_directory(self) -> Path:
        """
        The output directory path.
        """
        return self.directory / "output"

    @property
    def asset_directory(self) -> Path:
        """
        The :doc:`asset directory path </usage/assets>`.
        """
        return self.directory / "asset"

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
        if self.multilingual:
            return self.www_directory / self.locales[locale].slug
        return self.www_directory

    @property
    def name(self) -> MachineName:
        """
        The project name.

        If no project name was configured, this defaults to the hash of the project directory path.
        """
        return self._name

    @property
    def ancestry(self) -> EntityPool:
        """
        The project's ancestry.
        """
        return self._ancestry

    @property
    def author(self) -> Localizable | None:
        """
        The project's author.
        """
        return self._author

    @property
    def base_url(self) -> str:
        """
        The project's public URL's base URL.

        If the public URL is ``https://example.com``, the base URL is ``https://example.com``.
        If the public URL is ``https://example.com/my-ancestry-site``, the base URL is ``https://example.com``.
        If the public URL is ``https://my-ancestry-site.example.com``, the base URL is ``https://my-ancestry-site.example.com``.
        """
        return self._base_url

    @property
    def clean_urls(self) -> bool:
        """
        Whether to generate clean URLs such as ``/person/first-person`` instead of ``/person/first-person/index.html``.

        Generated artifacts will require web server that supports this.
        """
        return self._clean_urls

    @property
    def debug(self) -> bool:
        """
        Whether to enable debugging for project jobs.

        This setting is disabled by default.

        Enabling this generally results in:

        - More verbose logging output
        - job artifacts (e.g. generated sites)
        """
        return self._debug

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

    @property
    def root_path(self) -> str:
        """
        The project's public URL's root path.

        If the public URL is ``https://example.com``, the root path is an empty string.
        If the public URL is ``https://example.com/my-ancestry-site``, the root path is ``/my-ancestry-site``.
        """
        return self._root_path

    @property
    def title(self) -> Localizable:
        """
        The human-readable project title.
        """
        return self._title

    @property
    def url(self) -> str:
        """
        The project's public URL.
        """
        return self._url

    @property
    def lifetime_threshold(self) -> int:
        """
        The lifetime threshold indicates when people are considered dead.

        This setting defaults to :py:const:`betty.project.DEFAULT_LIFETIME_THRESHOLD`.

        The value is an integer expressing the age in years over which people are
        presumed to have died.
        """
        return self._lifetime_threshold

    @property
    def locales(self) -> KeyedCollection[Locale, ResolvableLocale, ProjectLocale]:
        """
        The project locales.
        """
        return self._locales

    @property
    def default_locale(self) -> ProjectLocale:
        """
        The default locale.
        """
        return next(iter(self._locales))

    @property
    def multilingual(self) -> bool:
        """
        Whether the project is multilingual.
        """
        return len(self._locales) > 1

    @service
    async def translations(self) -> TranslationRepository:
        """
        The available translations.
        """
        return AssetTranslationRepository(
            self.asset_directories, self.binary_file_cache
        )

    @service
    async def localizers(self) -> LocalizerRepository:
        """
        The available localizers.
        """
        return LocalizerRepository(await self.translations)

    @service
    async def public_localizers(self) -> Sequence[Localizer]:
        """
        The public localizers.
        """
        localizers = await self.localizers
        return [localizers.get(locale) for locale in self.locales.keys()]  # noqa: SIM118

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
        The content renderer.
        """
        return RenderDispatcher(*await gather(*self.renderers))

    @property
    def logo(self) -> Path:
        """
        The path to the logo file.
        """
        return self._logo

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
    def cache(self) -> Cache[Any]:
        """
        The project cache.
        """
        return PickledFileCache[Any](self._cache_directory)

    @service
    def binary_file_cache(self) -> BinaryFileCache:
        """
        The project binary file cache.
        """
        return BinaryFileCache(self._cache_directory)


@final
@ObjectDefinition(
    label=_("Project locale"),
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
class ProjectLocale(Data["ObjectDefinition"]):
    """
    A locale to use for a project.

    .. data:: betty.project:ProjectLocale
    """

    def __init__(self, /, locale: ResolvableLocale, *, alias: str | None = None):
        super().__init__()
        self._locale = resolve_locale(locale)
        if alias is not None and "/" in alias:
            raise HumanFacingException(_("Locale aliases must not contain slashes."))
        self._alias = alias
        self._slug = alias or to_language_tag(self._locale)

    @property
    @AttrDefinition(LocaleDefinition())
    def locale(self) -> Locale:
        """
        The locale.
        """
        return self._locale

    @property
    @AttrDefinition(
        StrDefinition(label=_("Alias")),
        omit_load=True,
        omit_dump=lambda data: data is None,
    )
    def alias(self) -> str | None:
        """
        A shorthand alias to use instead of the full language tag, such as when rendering URLs.
        """
        return self._alias

    @property
    def slug(self) -> str:
        """
        The URL slug.
        """
        return self._slug


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
                logo=BUILTIN_ASSET_DIRECTORY
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
class ProjectData(Data):
    """
    Configuration for a :py:class:`betty.project.Project`.

    .. data:: betty.project:ProjectData
    """

    author = Optional(LocalizableAttr(label=_("Author")))
    """
    The project's author.
    """

    clean_urls = AttrAttr(
        BoolDefinition(
            label=_("Clean URLs"),
            description=_(
                'Whether to use clean URLs: "/path" instead of "/path/index.html".'
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )
    """
    Whether to generate clean URLs.
    """

    copyright_notice = Optional(
        AttrAttr(
            CopyrightNoticeManufacturer,
            omit_load=True,
            omit_dump=lambda data: data == ProjectData._default_copyright_notice(),
            default=lambda: ProjectData._default_copyright_notice(),  # noqa: PLW0108
            resolver=CopyrightNoticeManufacturer.resolve,
        )
    )
    """
    The project-wide copyright notice.
    """

    copyright_notices = PluginDefinitionDatasAttr(
        CopyrightNoticeDefinition, CopyrightNoticeDefinitionData
    )
    """
    The :py:class:`betty.copyright_notice.CopyrightNotice` plugins created by this project.
    """

    debug = AttrAttr(
        BoolDefinition(
            label=_("Debugging mode"),
            description=_(
                "Whether to output more detailed logs and disable optimizations that make debugging harder."
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )
    """
    Whether to enable debugging for project jobs.
    """

    enrichers = KeyedCollectionAttr(
        KeyedCollectionDefinition(
            value=EnricherManufacturer,
            label=EnricherDefinition.type().label_plural,
            key=AttrSelector("plugin_id"),
            factory=lambda: MutableKeyedCollectionAdapter(
                key=lambda data: data.plugin_id,
                key_resolver=resolve_plugin_id,
                value_resolver=EnricherManufacturer.resolve,
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: not data,
    )
    """
    The enrichers to enable for the project.
    """

    event_types = PluginDefinitionDatasAttr(
        EventTypeDefinition, EventTypeDefinitionData
    )
    """
    The :py:class:`betty.event_type.EventType` plugins created by this project.
    """

    extensions = KeyedCollectionAttr(
        KeyedCollectionDefinition(
            value=ExtensionManufacturer,
            label=ExtensionDefinition.type().label_plural,
            key=AttrSelector("plugin_id"),
            factory=lambda: MutableKeyedCollectionAdapter(
                key=lambda data: data.plugin_id,
                key_resolver=resolve_plugin_id,
                value_resolver=ExtensionManufacturer.resolve,
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: not data,
    )
    """
    The extensions to enable for the project.
    """

    generate_entity_list_html = Optional(
        SequenceAttr(
            SequenceDefinition[MutableSequence[ResolvablePluginId[EntityDefinition]]](
                cls=list,
                label=_("Entity types to generate list HTML pages for"),
                value=MachineName,
                factory=lambda: MutableResolvedSequenceAdapter(
                    [], value_resolver=resolve_plugin_id
                ),
            )
        )
    )
    """
    Which entity types to generate list HTML pages for.
    """

    genders = PluginDefinitionDatasAttr(GenderDefinition, GenderDefinitionData)
    """
    The :py:class:`betty.gender.Gender` plugins created by this project.
    """

    license = Optional(
        AttrAttr(
            LicenseManufacturer,
            omit_load=True,
            omit_dump=lambda data: data == ProjectData._default_license(),
            default=lambda: ProjectData._default_license(),  # noqa: PLW0108
            resolver=LicenseManufacturer.resolve,
        )
    )
    """
    The project-wide license.
    """

    licenses = PluginDefinitionDatasAttr(LicenseDefinition, LicenseDefinitionData)
    """
    The :py:class:`betty.license.License` plugins created by this project.
    """

    lifetime_threshold = AttrAttr(
        IntDefinition(
            label=_("Lifetime threshold"),
            description=_(
                "The number of years people are expected to live at most, e.g. after which they are presumed to have died."
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: data == DEFAULT_LIFETIME_THRESHOLD,
        resolver=assert_number(minimum=1),
    )
    """
    The lifetime threshold indicates when people are considered dead.
    """

    loaders = KeyedCollectionAttr(
        KeyedCollectionDefinition(
            value=LoaderManufacturer,
            label=LoaderDefinition.type().label_plural,
            key=AttrSelector("plugin_id"),
            factory=lambda: MutableKeyedCollectionAdapter(
                key=lambda data: data.plugin_id,
                key_resolver=resolve_plugin_id,
                value_resolver=LoaderManufacturer.resolve,
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: not data,
    )
    """
    The loaders to enable for the project.
    """

    locales = KeyedCollectionAttr(
        KeyedCollectionDefinition(
            value=ProjectLocale,
            label=_("Locales"),
            key=AttrSelector("locale"),
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
        omit_load=True,
        omit_dump=lambda data: not data,
        default=lambda: [DEFAULT_LOCALE],
    )
    """
    The configured locales.
    """

    logo = Optional(AttrAttr(PathDefinition(), label=_("Logo")))
    """
    The project logo.
    """

    name = Optional(MachineNameAttr())
    """
    The project's machine name.
    """

    place_types = PluginDefinitionDatasAttr(
        PlaceTypeDefinition, PlaceTypeDefinitionData
    )
    """
    The :py:class:`betty.place_type.PlaceType` plugins created by this project.
    """

    roles = PluginDefinitionDatasAttr(RoleDefinition, RoleDefinitionData)
    """
    The :py:class:`betty.role.Role` plugins created by this project.
    """

    title = LocalizableAttr(label=_("Title"))
    """
    The human-readable project title.
    """

    url = AttrAttr(
        StrDefinition(
            label=_("URL"),
            description=_(
                "The absolute, public URL at which the site will be published."
            ),
        ),
        resolver=assert_url(),
    )
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
        event_types: Iterable[EventTypeDefinition] = (),
        extensions: ResolvablePluginManufacturerSequence[
            ExtensionDefinition, Extension
        ] = (),
        generate_entity_list_html: Iterable[ResolvablePluginId[EntityDefinition]]
        | None = None,
        genders: Iterable[GenderDefinitionData] = (),
        license: ResolvablePluginManufacturer[LicenseDefinition, License] | None = None,  # noqa: A002
        licenses: Iterable[LicenseDefinitionData] = (),
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
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
        self.enrichers = enrichers  # ty:ignore[invalid-assignment]
        self.event_types = event_types
        self.extensions = extensions  # ty:ignore[invalid-assignment]
        self.generate_entity_list_html = generate_entity_list_html
        self.genders = genders
        if license is not None:
            self.license = LicenseManufacturer.resolve(license)
        self.licenses = licenses
        self.lifetime_threshold = lifetime_threshold
        self.loaders = loaders  # ty:ignore[invalid-assignment]
        self.logo = logo
        self.locales = locales  # ty:ignore[invalid-assignment]
        self.name = name
        self.place_types = place_types
        self.roles = roles
        self.title = title
        self.url = url

    @classmethod
    def _default_copyright_notice(cls) -> CopyrightNoticeManufacturer:
        from betty.plugins.copyright_notice.project_author import ProjectAuthor

        return CopyrightNoticeManufacturer(ProjectAuthor)

    @classmethod
    def _default_license(cls) -> LicenseManufacturer:
        from betty.plugins.license.all_rights_reserved import AllRightsReserved

        return LicenseManufacturer(AllRightsReserved)
