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
from typing import TYPE_CHECKING, Self, final
from urllib.parse import urlsplit

from aiofiles.tempfile import TemporaryDirectory
from babel import Locale

import betty
import betty.dirs
from betty.app import App
from betty.asset import (
    AssetDefinition,
    AssetRepository,
    ProxyAssetRepository,
    StaticAssetRepository,
)
from betty.collection.keyed.adapter import KeyedCollectionAdapter
from betty.data import Data
from betty.data.aggregate.record.object import AttrDefinition, ObjectDefinition
from betty.data.bool import BoolDefinition
from betty.data.str import StrDefinition
from betty.document import Document, DocumentProviderDefinition
from betty.entity.collection.pool import EntityPool
from betty.exception import HumanFacingException
from betty.extension import Extension, ExtensionDefinition
from betty.hashid import hashid
from betty.html.css import CssResourceDefinition
from betty.html.js import JsResourceDefinition
from betty.jinja.filter import JinjaFilterDefinition
from betty.jinja.test import JinjaTestDefinition
from betty.link import LinkDefinition
from betty.load import EnricherDefinition, LoaderDefinition
from betty.locale import (
    DEFAULT_LOCALE,
    ResolvableLocale,
    resolve_locale,
    to_language_tag,
)
from betty.locale.data import LocaleDefinition
from betty.locale.localizable import resolve_localizable
from betty.locale.localizable.gettext import _
from betty.locale.localize import Localizer, LocalizerRepository
from betty.locale.translation import (
    AssetTranslationRepository,
    ProxyTranslationRepository,
    TranslationRepository,
)
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin.resolve import resolve_plugin_id
from betty.plugins.entity.person import Person
from betty.privacy.privatizer import Privatizer
from betty.render import RenderDispatcher, RendererDefinition
from betty.sample import Sample, Size
from betty.service.level import DownstreamServiceLevel
from betty.service.level.requirement import RequirableServiceLevel
from betty.service.plugin.service import (
    ServicePluginProvider,
    ServicePlugins,
    SupportPlugins,
)
from betty.service.provider import service

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Collection, Iterable, Mapping

    from betty.collection.keyed import KeyedCollection
    from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
    from betty.entity import EntityDefinition
    from betty.jinja import Environment
    from betty.license import License, LicenseDefinition
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.plugin import PluginDefinition
    from betty.plugin.discovery import ResolvableDiscovery
    from betty.plugin.factory import PluginManufacturer
    from betty.plugin.resolve import ResolvablePluginId
    from betty.project.data import ProjectConfiguration
    from betty.service.plugin.service import ServicePluginCollection
    from betty.url import UrlGenerator


DEFAULT_LIFETIME_THRESHOLD = 123
"""
The default age by which people are presumed dead.

This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
the oldest verified person to ever have lived.
"""


type ProjectServicePlugin = (
    AssetDefinition
    | CssResourceDefinition
    | DocumentProviderDefinition
    | EnricherDefinition
    | ExtensionDefinition
    | JinjaFilterDefinition
    | JinjaTestDefinition
    | JsResourceDefinition
    | LinkDefinition
    | LoaderDefinition
)


@final
class Project(
    DownstreamServiceLevel[App], RequirableServiceLevel, ServicePluginProvider
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
        directory: Path,
        *,
        app: App,
        title: ResolvableLocalizable,
        url: str,
        ancestry: EntityPool | None = None,
        author: ResolvableLocalizable | None = None,
        clean_urls: bool = False,
        copyright_notice: PluginManufacturer[CopyrightNoticeDefinition]
        | type[CopyrightNotice]
        | None = None,
        debug: bool = False,
        entity_types: Iterable[
            ProjectEntityType | ResolvablePluginId[EntityDefinition]
        ] = (),
        license: PluginManufacturer[LicenseDefinition]  # noqa: A002
        | type[License]
        | None = None,
        lifetime_threshold: int | None = None,
        locales: Iterable[ProjectLocale | ResolvableLocale] = (),
        logo: Path | None = None,
        name: ResolvableMachineName | None = None,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
        service_plugins: ServicePlugins[ProjectServicePlugin] = (),
        support_plugins: SupportPlugins = (),
        _plugin_discoveries: Iterable[PluginDefinition] = (),
    ):
        from betty.plugins.copyright_notice.project_author import ProjectAuthor
        from betty.plugins.license.all_rights_reserved import AllRightsReserved

        copyright_notice = copyright_notice or ProjectAuthor
        license = license or AllRightsReserved  # noqa: A001
        super().__init__(
            plugins=plugins,
            service_plugin_types={
                AssetDefinition,
                CssResourceDefinition,
                DocumentProviderDefinition,
                EnricherDefinition,
                ExtensionDefinition,
                JinjaFilterDefinition,
                JinjaTestDefinition,
                JsResourceDefinition,
                LinkDefinition,
                LoaderDefinition,
            },
            service_plugins=service_plugins,
            support_plugins=(*support_plugins, copyright_notice, license),
            service_plugin_services=self,
            upstream=app,
        )
        self._ancestry = EntityPool() if ancestry is None else ancestry
        self._author = None if author is None else resolve_localizable(author)
        self._clean_urls = clean_urls
        self.__copyright_notice = copyright_notice
        self._debug = debug
        self._directory = directory
        self._entity_types = KeyedCollectionAdapter(
            {
                project_entity_type.entity_type: project_entity_type
                for entity_type in entity_types
                if (
                    project_entity_type := entity_type
                    if isinstance(entity_type, ProjectEntityType)
                    else ProjectEntityType(entity_type=entity_type)
                )
            },
            key_resolver=resolve_plugin_id,
        )
        self.__license = license
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
            betty.dirs.ASSETS_DIRECTORY_PATH
            / "universe"
            / "public"
            / "static"
            / "betty-512x512.png"
            if logo is None
            else logo
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

    @classmethod
    async def new(
        cls, app: App, data: ProjectConfiguration, *, directory: Path
    ) -> Self:
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
            license=data.license,
            lifetime_threshold=data.lifetime_threshold,
            locales=data.locales,
            logo=data.logo,
            service_plugins=data.extensions,
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
        author: ResolvableLocalizable | None = None,
        clean_urls: bool = False,
        debug: bool = False,
        directory: Path | None = None,
        entity_types: Iterable[
            ProjectEntityType | ResolvablePluginId[EntityDefinition]
        ] = (),
        lifetime_threshold: int | None = None,
        locales: Iterable[ProjectLocale | ResolvableLocale] = (),
        logo: Path | None = None,
        name: ResolvableMachineName | None = None,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None = None,
        service_plugins: ServicePlugins[ProjectServicePlugin] = (),
        support_plugins: SupportPlugins = (),
        title: ResolvableLocalizable | None = None,
        url: str | None = None,
    ) -> AsyncIterator[Self]:
        """
        Creat a new, isolated, temporary project.

        The project will not leave any traces on the system, except when it uses
        global Betty functionality such as caches.
        """
        async with AsyncExitStack() as stack:
            if app is None:
                app = await stack.enter_async_context(App.new_isolated())
            if directory is None:
                directory = Path(await stack.enter_async_context(TemporaryDirectory()))
            async with cls(
                directory,
                ancestry=ancestry,
                app=app,
                author=author,
                clean_urls=clean_urls,
                debug=debug,
                entity_types=entity_types,
                lifetime_threshold=lifetime_threshold,
                locales=locales,
                logo=logo,
                name=name,
                plugins=plugins,
                service_plugins=service_plugins,
                support_plugins=support_plugins,
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

    @property
    def entity_types(
        self,
    ) -> KeyedCollection[MachineName, ResolvablePluginId, ProjectEntityType]:
        """
        The available entity types.
        """
        return self._entity_types

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

        This setting defaults to :py:const:`betty.project.data.DEFAULT_LIFETIME_THRESHOLD`.

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
        The  content renderer.
        """
        return RenderDispatcher(
            *[
                await self.factory.new(plugin.cls)
                async for plugin in self.plugins[RendererDefinition]
            ]
        )

    @property
    async def extensions(
        self,
    ) -> ServicePluginCollection[ExtensionDefinition, Extension]:
        """
        The enabled extensions.
        """
        return (await self.service_plugins)[ExtensionDefinition]

    @property
    def logo(self) -> Path:
        """
        The path to the logo file.
        """
        return self._logo

    @service
    async def copyright_notice(self) -> CopyrightNotice:
        """
        The overall project copyright.
        """
        return await self.factory.new(self.__copyright_notice)

    @service
    async def license(self) -> License:
        """
        The overall project license.
        """
        return await self.factory.new(self.__license)

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
                for document_provider in (await self.service_plugins)[
                    DocumentProviderDefinition
                ]
                for (key, value) in document_provider.new_document_vars().items()
            },
            **kwargs,
        )


@final
@ObjectDefinition(
    label=_("Entity type configuration"),
    samples=[
        lambda: Sample(
            ProjectEntityType(entity_type=Person),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            ProjectEntityType(entity_type=Person, generate_html_list=False),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class ProjectEntityType(Data[ObjectDefinition["ProjectEntityType"]]):
    """
    Configure a single entity type for a project.

    .. data:: betty.project:ProjectEntityType
    """

    def __init__(
        self,
        *,
        entity_type: ResolvablePluginId[EntityDefinition],
        generate_html_list: bool = True,
    ):
        self._entity_type = resolve_plugin_id(entity_type)
        self.generate_html_list = generate_html_list

    @property
    @AttrDefinition(MachineName)
    def entity_type(self) -> MachineName:
        """
        The ID of the configured entity type.
        """
        return self._entity_type

    @property
    @AttrDefinition(
        BoolDefinition(label=_("Generate list HTML page")),
        omit_load=True,
        omit_dump=lambda data: data is True,
    )
    def generate_html_list(self) -> bool:
        """
        Whether to generate listing web pages for entities of this type.
        """
        return self._generate_html_list

    @generate_html_list.setter
    def generate_html_list(self, generate_html_list: bool) -> None:
        self._generate_html_list = generate_html_list


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
    @AttrDefinition(StrDefinition(label=_("Alias")))
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
