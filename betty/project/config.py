"""
Provide project configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final
from urllib.parse import urlparse

from babel import Locale
from typing_extensions import override

from betty.ancestry.event_type import EventType, EventTypeDefinition
from betty.ancestry.gender import Gender, GenderDefinition
from betty.ancestry.person import Person
from betty.ancestry.place_type import PlaceType, PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRole, PresenceRoleDefinition
from betty.assertion import assert_number
from betty.collections import KeyedCollection
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.data import Data, Sample
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.aggregate.record.object import AttrDefinition, ObjectDefinition
from betty.data.aggregate.record.object.property import (
    KeyedCollectionProperty,
    Optional,
    Property,
)
from betty.data.bool import BoolDefinition
from betty.data.indicator.selector import Attr
from betty.data.int import IntDefinition
from betty.data.sample import Size
from betty.data.str import StrDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.exception import HumanFacingException
from betty.license import License, LicenseDefinition
from betty.locale import (
    DEFAULT_LOCALE,
    ResolvableLocale,
    resolve_locale,
    to_language_tag,
)
from betty.locale.data import LocaleDefinition
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import LocalizableProperty
from betty.locale.localizable.static import CountableStaticTranslations
from betty.machine_name import MachineName, MachineNameDefinition, assert_machine_name
from betty.model import EntityDefinition
from betty.pathlib import FilePathDefinition
from betty.plugin.config import (
    CountableHumanFacingPluginDefinitionConfiguration,
    HumanFacingPluginDefinitionConfiguration,
    PluginConfiguration,
    ResolvablePluginConfigurationSequence,
    resolve_plugin_configuration,
    resolve_plugin_configuration_sequence,
)
from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration
from betty.plugin.config.property import PluginDefinitionConfigurationsProperty
from betty.plugin.data import PluginConfigurationDefinition, PluginIdDefinition
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.project import Extension, ExtensionDefinition
from betty.service.hydrate import Hydratable

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.service.level import ServiceLevel

DEFAULT_LIFETIME_THRESHOLD = 123
"""
The default age by which people are presumed dead.

This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
the oldest verified person to ever have lived.
"""


@final
@ObjectDefinition(
    label=_("Entity type configuration"),
    samples=[
        lambda: Sample(
            EntityTypeConfiguration(entity_type=Person),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            EntityTypeConfiguration(entity_type=Person, generate_html_list=False),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class EntityTypeConfiguration(
    Data[ObjectDefinition["EntityTypeConfiguration"]], Hydratable
):
    """
    Configure a single entity type for a project.

    .. data:: betty.project.config:EntityTypeConfiguration
    """

    def __init__(
        self,
        *,
        entity_type: ResolvableId[EntityDefinition],
        generate_html_list: bool = True,
    ):
        self._entity_type = resolve_id(entity_type)
        self.generate_html_list = generate_html_list

    @property
    @AttrDefinition(PluginIdDefinition(EntityDefinition))
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

    @override
    async def hydrate(self, *, services: ServiceLevel) -> None:
        entity_type = (await services.plugins(EntityDefinition)).get(self._entity_type)
        if self.generate_html_list and not entity_type.public_facing:
            raise HumanFacingException(
                _(
                    "Cannot generate pages for {entity_type}, because it is not a public-facing entity type."
                ).format(entity_type=entity_type.label)
            )


@final
@ObjectDefinition(
    label=_("Locale configuration"),
    samples=[
        lambda: Sample(
            LocaleConfiguration(Locale("nl", "NL")), label="Minimal", size=Size.MINIMAL
        ),
        lambda: Sample(
            LocaleConfiguration(Locale("nl", "NL"), alias="nl"),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class LocaleConfiguration(Data["ObjectDefinition"]):
    """
    Configure a single project locale.

    .. data:: betty.project.config:LocaleConfiguration
    """

    locale = Property(LocaleDefinition(), label=_("Locale"), resolver=resolve_locale)
    """
    The locale.
    """

    @staticmethod
    def _resolve_alias(alias: str) -> str:
        if "/" in alias:
            raise HumanFacingException(_("Locale aliases must not contain slashes."))
        return alias

    alias = Optional(Property(StrDefinition(label=_("Alias")), resolver=_resolve_alias))
    """
    A shorthand alias to use instead of the full language tag, such as when rendering URLs.
    """

    def __init__(self, /, locale: ResolvableLocale, *, alias: str | None = None):
        super().__init__()
        self.locale = locale
        self.alias = alias

    @property
    def slug(self) -> str:
        """
        The URL slug.
        """
        if self.alias is None:
            return to_language_tag(self.locale)
        return self.alias


@final
@ObjectDefinition(
    label=_("Copyright notice configuration"),
    samples=[
        lambda: Sample(
            CopyrightNoticeDefinitionConfiguration(
                id="my-first-copyright-notice",
                label="My First Copyright Notice",
                summary="My First Copyright Notice is my first copyright notice",
                text="My First Copyright Notice is my first copyright notice, all rights are reserved.",
            ),
            label="Default",
        )
    ],
)
class CopyrightNoticeDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration[CopyrightNoticeDefinition]
):
    """
    Configure a :py:class:`betty.copyright_notice.CopyrightNoticeDefinition`.

    .. data:: betty.project.config:CopyrightNoticeDefinitionConfiguration
    """

    summary = LocalizableProperty(label=_("Summary"))
    text = LocalizableProperty(label=_("Text"))

    def __init__(
        self,
        *,
        summary: ResolvableLocalizable,
        text: ResolvableLocalizable,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.summary = summary
        self.text = text

    @override
    def new_plugin(self) -> CopyrightNoticeDefinition:
        configuration = self

        @CopyrightNoticeDefinition(
            self.id,
            label=self.label,
            description=self.description,
        )
        class _ProjectConfigurationCopyrightNotice(CopyrightNotice):
            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return _ProjectConfigurationCopyrightNotice.plugin()


@final
@ObjectDefinition(
    label=_("License configuration"),
    samples=[
        lambda: Sample(
            LicenseDefinitionConfiguration(
                id="my-first-license",
                label="My First License",
                summary="My First License is my first license",
                text="My First License is my first license, and allows you o...",
            ),
            label="Default",
        )
    ],
)
class LicenseDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration[LicenseDefinition]
):
    """
    Configure a :py:class:`betty.license.LicenseDefinition`.

    .. data:: betty.project.config:LicenseDefinitionConfiguration
    """

    summary = LocalizableProperty(label=_("Summary"))
    text = LocalizableProperty(label=_("Text"))

    def __init__(
        self,
        *,
        summary: ResolvableLocalizable,
        text: ResolvableLocalizable,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.summary = summary
        self.text = text

    @override
    def new_plugin(self) -> LicenseDefinition:
        configuration = self

        @LicenseDefinition(
            self.id,
            label=self.label,
            description=self.description,
        )
        class _ProjectConfigurationLicense(License):
            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return _ProjectConfigurationLicense.plugin()


@final
@ObjectDefinition(
    label=_("Event type configuration"),
    samples=[
        lambda: Sample(
            EventTypeDefinitionConfiguration(
                id="moon-landing",
                label="Moon landing",
                label_plural="Moon landings",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} moon landing",
                            "other": "{count} moon landings",
                        }
                    }
                ),
            ),
            label="Default",
        )
    ],
)
class EventTypeDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[EventTypeDefinition],
    OrderedPluginDefinitionConfiguration[EventTypeDefinition],
):
    """
    Configure a :py:class:`betty.ancestry.event_type.EventTypeDefinition`.

    .. data:: betty.project.config:EventTypeDefinitionConfiguration
    """

    @override
    def new_plugin(self) -> EventTypeDefinition:
        @EventTypeDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
            comes_before=set(self.comes_before),
            comes_after=set(self.comes_after),
        )
        class _ProjectConfigurationEventType(EventType):
            pass

        return _ProjectConfigurationEventType.plugin()


@final
@ObjectDefinition(
    label=_("Place type configuration"),
    samples=[
        lambda: Sample(
            PlaceTypeDefinitionConfiguration(
                id="moon",
                label="Moon",
                label_plural="Moons",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} moon",
                            "other": "{count} moons",
                        }
                    }
                ),
            ),
            label="Default",
        )
    ],
)
class PlaceTypeDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[PlaceTypeDefinition]
):
    """
    Configure a :py:class:`betty.ancestry.place_type.PlaceTypeDefinition`.

    .. data:: betty.project.config:PlaceTypeDefinitionConfiguration
    """

    @override
    def new_plugin(self) -> PlaceTypeDefinition:
        @PlaceTypeDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _ProjectConfigurationPlaceType(PlaceType):
            pass

        return _ProjectConfigurationPlaceType.plugin()


@final
@ObjectDefinition(
    label=_("Presence role configuration"),
    samples=[
        lambda: Sample(
            PresenceRoleDefinitionConfiguration(
                id="astronaut",
                label="Astronaut",
                label_plural="Astronauts",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} astronaut",
                            "other": "{count} astronauts",
                        }
                    }
                ),
            ),
            label="Default",
        )
    ],
)
class PresenceRoleDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[PresenceRoleDefinition]
):
    """
    Configure a :py:class:`betty.ancestry.presence_role.PresenceRoleDefinition`.

    .. data:: betty.project.config:PresenceRoleDefinitionConfiguration
    """

    @override
    def new_plugin(self) -> PresenceRoleDefinition:
        @PresenceRoleDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _ProjectConfigurationPresenceRole(PresenceRole):
            pass

        return _ProjectConfigurationPresenceRole.plugin()


@final
@ObjectDefinition(
    label=_("Gender configuration"),
    samples=[
        lambda: Sample(
            GenderDefinitionConfiguration(
                id="genderqueer",
                label="Genderqueer",
                label_plural="Genderqueers",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} genderqueer",
                            "other": "{count} genderqueers",
                        }
                    }
                ),
            ),
            label="Default",
        )
    ],
)
class GenderDefinitionConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration[GenderDefinition]
):
    """
    Configure a :py:class:`betty.ancestry.gender.GenderDefinition`.

    .. data:: betty.project.config:GenderDefinitionConfiguration
    """

    @override
    def new_plugin(self) -> GenderDefinition:
        @GenderDefinition(
            self.id,
            label=self.label,
            label_plural=self.label_plural,
            label_countable=self.label_countable,
            description=self.description,
        )
        class _ProjectConfigurationGender(Gender):
            pass

        return _ProjectConfigurationGender.plugin()


@final
@ObjectDefinition(
    label=_("Project configuration"),
    samples=[
        lambda: Sample(
            ProjectConfiguration(title="Betty", url="https://example.com"),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            ProjectConfiguration(
                author="Bart Feenstra",
                clean_urls=True,
                copyright_notice=ProjectConfiguration.copyright_notice.attr.data.samples.get(
                    Size.FULL
                ).data,
                copyright_notices=[
                    CopyrightNoticeDefinitionConfiguration.data()
                    .samples.get(Size.FULL)
                    .data
                ],
                debug=True,
                entity_types=[
                    EntityTypeConfiguration.data().samples.get(Size.FULL).data
                ],
                event_types=[
                    EventTypeDefinitionConfiguration.data().samples.get(Size.FULL).data
                ],
                genders=[
                    GenderDefinitionConfiguration.data().samples.get(Size.FULL).data
                ],
                logo=ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png",
                license=ProjectConfiguration.license.attr.data.samples.get(
                    Size.FULL
                ).data,
                licenses=[
                    LicenseDefinitionConfiguration.data().samples.get(Size.FULL).data
                ],
                lifetime_threshold=123,
                locales=[LocaleConfiguration.data().samples.get(Size.FULL).data],
                name="betty-ancestry",
                place_types=[
                    PlaceTypeDefinitionConfiguration.data().samples.get(Size.FULL).data
                ],
                presence_roles=[
                    PresenceRoleDefinitionConfiguration.data()
                    .samples.get(Size.FULL)
                    .data
                ],
                title="Betty's ancestry",
                url="https://ancestry.example.com/betty",
            ),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class ProjectConfiguration(Data):
    """
    Configuration for a :py:class:`betty.project.Project`.

    .. data:: betty.project.config:ProjectConfiguration
    """

    author = Optional(LocalizableProperty(label=_("Author")))
    """
    The project's author.
    """

    clean_urls = Property(
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
    Whether to generate clean URLs such as ``/person/first-person`` instead of ``/person/first-person/index.html``.

    Generated artifacts will require web server that supports this.
    """

    copyright_notice = Property(
        PluginConfigurationDefinition(CopyrightNoticeDefinition),
        omit_load=True,
        omit_dump=lambda data: data == ProjectConfiguration._default_copyright_notice(),
        default=lambda: ProjectConfiguration._default_copyright_notice(),
    )
    """
    The project-wide copyright notice.
    """

    copyright_notices = PluginDefinitionConfigurationsProperty(
        CopyrightNoticeDefinition, CopyrightNoticeDefinitionConfiguration
    )
    """
    The :py:class:`betty.copyright_notice.CopyrightNotice` plugins created by this project.
    """

    debug = Property(
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

    This setting is disabled by default.

    Enabling this generally results in:

    - More verbose logging output
    - job artifacts (e.g. generated sites)
    """

    entity_types = KeyedCollectionProperty(
        KeyedCollectionDefinition(
            value=EntityTypeConfiguration,
            label=_("Entity types"),
            key=Attr("entity_type"),
            ordered=False,
        ),  # ty:ignore[invalid-argument-type]
        omit_load=True,
        omit_dump=lambda data: not len(data),
        default=lambda: KeyedCollection(
            key=lambda item: item.entity_type,
            value_resolver=lambda data: data
            if isinstance(data, EntityTypeConfiguration)
            else EntityTypeConfiguration(entity_type=data),
        ),
    )
    """
    The available entity types.
    """

    event_types = PluginDefinitionConfigurationsProperty(
        EventTypeDefinition, EventTypeDefinitionConfiguration
    )
    """
    The :py:class:`betty.ancestry.event_type.EventType` plugins created by this project.
    """

    extensions = KeyedCollectionProperty(
        KeyedCollectionDefinition(
            value=PluginConfigurationDefinition(ExtensionDefinition),
            label=ExtensionDefinition.type().label_plural,
            key=Attr("id"),
            ordered=False,
        ),  # ty:ignore[invalid-argument-type]
        omit_load=True,
        omit_dump=lambda data: not len(data),
        default=lambda: KeyedCollection(
            key=lambda data: data.id,
            key_resolver=resolve_id,
            value_resolver=resolve_plugin_configuration,
        ),
    )
    """
    The extensions to enable for the project.
    """

    genders = PluginDefinitionConfigurationsProperty(
        GenderDefinition, GenderDefinitionConfiguration
    )
    """
    The :py:class:`betty.gender.Gender` plugins created by this project.
    """

    license = Property(
        PluginConfigurationDefinition(LicenseDefinition),
        omit_load=True,
        omit_dump=lambda data: data == ProjectConfiguration._default_license(),
        default=lambda: ProjectConfiguration._default_license(),
    )
    """
    The project-wide license.
    """

    licenses = PluginDefinitionConfigurationsProperty(
        LicenseDefinition, LicenseDefinitionConfiguration
    )
    """
    The :py:class:`betty.license.License` plugins created by this project.
    """

    lifetime_threshold = Property(
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

    This setting defaults to :py:const:`betty.project.config.DEFAULT_LIFETIME_THRESHOLD`.

    The value is an integer expressing the age in years over which people are
    presumed to have died.
    """

    locales = KeyedCollectionProperty(
        KeyedCollectionDefinition(
            value=LocaleConfiguration,
            label=_("Locales"),
            key=Attr("locale"),
            ordered=True,
        ),  # ty:ignore[invalid-argument-type]
        omit_load=True,
        omit_dump=lambda data: not len(data),
        default=lambda: KeyedCollection(
            [DEFAULT_LOCALE],
            key=lambda item: item.locale,
            key_resolver=resolve_locale,
            value_resolver=lambda value: value
            if isinstance(value, LocaleConfiguration)
            else LocaleConfiguration(resolve_locale(value)),
            resolver=lambda items: [DEFAULT_LOCALE] if not len(items) else items,
        ),
    )
    """
    The configured locales.
    """

    logo = Optional(Property(FilePathDefinition(), label=_("Logo")))
    """
    The project logo.
    """

    name = Optional(Property(MachineNameDefinition(), resolver=assert_machine_name()))
    """
    The project's machine name.
    """

    place_types = PluginDefinitionConfigurationsProperty(
        PlaceTypeDefinition, PlaceTypeDefinitionConfiguration
    )
    """
    The :py:class:`betty.ancestry.place_type.PlaceType` plugins created by this project.
    """

    presence_roles = PluginDefinitionConfigurationsProperty(
        PresenceRoleDefinition, PresenceRoleDefinitionConfiguration
    )
    """
    The :py:class:`betty.ancestry.presence_role.PresenceRole` plugins created by this project.
    """

    title = LocalizableProperty(label=_("Title"))
    """
    The human-readable project title.
    """

    def __init__(
        self,
        *,
        title: ResolvableLocalizable,
        url: str,
        author: ResolvableLocalizable | None = None,
        clean_urls: bool = False,
        copyright_notice: PluginConfiguration[
            CopyrightNoticeDefinition, CopyrightNotice
        ]
        | None = None,
        copyright_notices: Iterable[CopyrightNoticeDefinitionConfiguration]
        | None = None,
        debug: bool = False,
        entity_types: Iterable[EntityTypeConfiguration | ResolvableId[EntityDefinition]]
        | None = None,
        event_types: Iterable[EventTypeDefinitionConfiguration] | None = None,
        extensions: ResolvablePluginConfigurationSequence[
            ExtensionDefinition, Extension
        ]
        | None = None,
        genders: Iterable[GenderDefinitionConfiguration] | None = None,
        license: PluginConfiguration[LicenseDefinition, License] | None = None,  # noqa: A002
        licenses: Iterable[LicenseDefinitionConfiguration] | None = None,
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        locales: Iterable[ResolvableLocale | LocaleConfiguration] | None = None,
        logo: Path | None = None,
        name: MachineName | None = None,
        place_types: Iterable[PlaceTypeDefinitionConfiguration] | None = None,
        presence_roles: Iterable[PresenceRoleDefinitionConfiguration] | None = None,
    ):
        super().__init__()
        self.author = author
        self.clean_urls = clean_urls
        if copyright_notice is not None:
            self.copyright_notice = copyright_notice
        if copyright_notices is not None:
            self.copyright_notices = copyright_notices
        self.debug = debug
        if entity_types is not None:
            self.entity_types = entity_types
        if event_types is not None:
            self.event_types = event_types
        if extensions is not None:
            self.extensions.add(*resolve_plugin_configuration_sequence(extensions))  # ty:ignore[invalid-argument-type]
        if genders is not None:
            self.genders = genders
        if license is not None:
            self.license = license
        if licenses is not None:
            self.licenses = licenses
        self.lifetime_threshold = lifetime_threshold
        self.logo = logo
        if locales is not None:
            self.locales = locales
        self.name = name
        if place_types is not None:
            self.place_types = place_types
        if presence_roles is not None:
            self.presence_roles = presence_roles
        self.title = title
        self._url = url

    @classmethod
    def _default_copyright_notice(
        cls,
    ) -> PluginConfiguration[CopyrightNoticeDefinition, CopyrightNotice]:
        from betty.copyright_notice.copyright_notices import ProjectAuthor

        return PluginConfiguration[CopyrightNoticeDefinition, CopyrightNotice](
            ProjectAuthor
        )

    @classmethod
    def _default_license(
        cls,
    ) -> PluginConfiguration[LicenseDefinition, License]:
        from betty.license.licenses import AllRightsReserved

        return PluginConfiguration[LicenseDefinition, License](AllRightsReserved)

    @property
    @AttrDefinition(
        StrDefinition(
            label=_("URL"),
            description=_(
                "The absolute, public URL at which the site will be published."
            ),
        )
    )
    def url(self) -> str:
        """
        The project's public URL.
        """
        return self._url

    @url.setter
    def url(self, url: str) -> None:
        url_parts = urlparse(url)
        if not url_parts.scheme:
            raise HumanFacingException(
                _("The URL must start with a scheme such as https:// or http://.")
            )
        if not url_parts.netloc:
            raise HumanFacingException(_("The URL must include a host."))
        self._url = f"{url_parts.scheme}://{url_parts.netloc}{url_parts.path}"

    @property
    def base_url(self) -> str:
        """
        The project's public URL's base URL.

        If the public URL is ``https://example.com``, the base URL is ``https://example.com``.
        If the public URL is ``https://example.com/my-ancestry-site``, the base URL is ``https://example.com``.
        If the public URL is ``https://my-ancestry-site.example.com``, the base URL is ``https://my-ancestry-site.example.com``.
        """
        url_parts = urlparse(self.url)
        return f"{url_parts.scheme}://{url_parts.netloc}"

    @property
    def root_path(self) -> str:
        """
        The project's public URL's root path.

        If the public URL is ``https://example.com``, the root path is an empty string.
        If the public URL is ``https://example.com/my-ancestry-site``, the root path is ``/my-ancestry-site``.
        """
        return urlparse(self.url).path.rstrip("/")

    @property
    def default_locale(self) -> LocaleConfiguration:
        """
        The default locale.
        """
        return next(iter(self.locales))

    @property
    def multilingual(self) -> bool:
        """
        Whether the configuration is multilingual.
        """
        return len(self.locales) > 1
