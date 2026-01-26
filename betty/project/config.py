"""
Provide project configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final
from urllib.parse import urlparse

from babel import Locale
from typing_extensions import override

from betty.ancestry.event_type import EventType, EventTypeDefinition
from betty.ancestry.gender import Gender, GenderDefinition
from betty.ancestry.person import Person
from betty.ancestry.place_type import PlaceType, PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRole, PresenceRoleDefinition
from betty.assertion import (
    Field,
    OptionalField,
    RequiredField,
    assert_locale,
    assert_number,
    assert_record,
    assert_str,
)
from betty.collections import KeyedCollection
from betty.config import Configuration
from betty.config.collections.mapping import OrderedConfigurationMapping
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.data import Data, DataDefinition, OptionalDefinition, Sample
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.object import AttrDefinition, ObjectDefinition
from betty.data.aggregate.record.object.property import Optional
from betty.data.bool import BoolDefinition
from betty.data.indicator.selector import Attr
from betty.data.int import IntDefinition
from betty.data.sample import Samples, Size
from betty.data.str import StrDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.exception import HumanFacingException
from betty.license import License, LicenseDefinition
from betty.locale import DEFAULT_LOCALE, LocaleLike, ensure_locale, to_language_tag
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.portable import dump_localizable
from betty.locale.localizable.property import LocalizableProperty
from betty.locale.localizable.static import CountableStaticTranslations
from betty.machine_name import MachineName, MachineNameDefinition, assert_machine_name
from betty.model import EntityDefinition
from betty.pathlib import FilePathDefinition
from betty.plugin.config import (
    CountableHumanFacingPluginDefinitionConfiguration,
    HumanFacingPluginDefinitionConfiguration,
    PluginDefinitionConfigurationMapping,
    PluginInstanceConfiguration,
    PluginInstanceConfigurationMapping,
)
from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration
from betty.plugin.data import PluginIdDefinition
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.project.extension import Extension, ExtensionDefinition
from betty.service.hydrate import Hydratable

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from pathlib import Path

    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.portable import PortableData, PortableMapping
    from betty.service.level import ServiceLevel

DEFAULT_LIFETIME_THRESHOLD = 123
"""
The default age by which people are presumed dead.

This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
the oldest verified person to ever have lived.
"""


@final
class ExtensionInstanceConfigurationMapping(
    PluginInstanceConfigurationMapping[ExtensionDefinition, Extension]
):
    """
    Configure a project's enabled extensions.

    .. configuration:: betty.project.config:ExtensionInstanceConfigurationMapping
    """

    def enable(self, *extensions: ResolvableId[ExtensionDefinition]) -> None:
        """
        Enable the given extensions.
        """
        for extension in extensions:
            extension = resolve_id(extension)
            if extension not in self._configurations:
                self.append(PluginInstanceConfiguration(extension))

    @override
    @classmethod
    def samples(cls) -> Samples:
        from betty.project.extension.raspberry_mint import RaspberryMint
        from betty.project.extension.raspberry_mint.config import (
            RaspberryMintConfiguration,
        )

        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls([PluginInstanceConfiguration(RaspberryMint)]),  # ty:ignore[invalid-argument-type]
                    label="Expanded",
                ),
                lambda: Sample(
                    cls(
                        [
                            PluginInstanceConfiguration(
                                RaspberryMint,
                                RaspberryMintConfiguration.samples()
                                .get(Size.FULL)
                                .data,
                            )
                        ]  # ty:ignore[invalid-argument-type]
                    ),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


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
    async def hydrate(self, services: ServiceLevel, /) -> None:
        entity_type = (await services.plugins(EntityDefinition)).get(self._entity_type)
        if self.generate_html_list and not entity_type.public_facing:
            raise HumanFacingException(
                _(
                    "Cannot generate pages for {entity_type}, because it is not a public-facing entity type."
                ).format(entity_type=entity_type.label)
            )


@final
class LocaleConfiguration(Configuration):
    """
    Configure a single project locale.

    .. configuration:: betty.project.config:LocaleConfiguration
    """

    def __init__(
        self,
        locale: LocaleLike,
        *,
        alias: str | None = None,
    ):
        super().__init__()
        self._locale = ensure_locale(locale)
        if alias is not None and "/" in alias:
            raise HumanFacingException(_("Locale aliases must not contain slashes."))
        self._alias = alias

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self._locale, self._alias) == (other._locale, other._alias)

    @property
    def locale(self) -> Locale:
        """
        A locale.
        """
        return self._locale

    @property
    def alias(self) -> str:
        """
        A shorthand alias to use instead of the full language tag, such as when rendering URLs.
        """
        if self._alias is None:
            return to_language_tag(self.locale)
        return self._alias

    @alias.setter
    def alias(self, alias: str | None) -> None:
        self._alias = alias

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        record = assert_record(
            RequiredField("locale", assert_locale()),
            OptionalField("alias", assert_str()),
        )(portable)
        return cls(record["locale"], alias=record.get("alias", None))

    @override
    def dump(self) -> PortableData:
        portable: PortableData = {
            "locale": to_language_tag(self.locale),
        }
        if self._alias is not None:
            portable["alias"] = self._alias
        return portable

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(Locale("nl", "NL")), label="Minimal", size=Size.MINIMAL
                ),
                lambda: Sample(
                    cls(Locale("nl", "NL"), alias="nl"), label="Full", size=Size.FULL
                ),
            ]
        )


@final
class LocaleConfigurationMapping(
    OrderedConfigurationMapping[Locale, LocaleLike, LocaleConfiguration]
):
    """
    Configure a project's locales.

    .. configuration:: betty.project.config:LocaleConfigurationMapping
    """

    def __init__(self, configurations: Iterable[LocaleConfiguration] | None = None, /):
        super().__init__(configurations)
        self._ensure_locale()

    @override
    def _resolve_key(self, configuration_key: LocaleLike, /) -> Locale:
        return ensure_locale(configuration_key)

    @override
    def _post_remove(self, configuration: LocaleConfiguration, /) -> None:
        super()._post_remove(configuration)
        self._ensure_locale()

    def _ensure_locale(self) -> None:
        if len(self) == 0:
            self.append(LocaleConfiguration(DEFAULT_LOCALE))

    @override
    def replace(self, *configurations: LocaleConfiguration) -> None:
        # Prevent the events from being dispatched.
        self._configurations.clear()
        self.append(*configurations)
        self._ensure_locale()

    @override
    @classmethod
    def _item_cls(cls) -> type[LocaleConfiguration]:
        return LocaleConfiguration

    @override
    def _get_key(self, configuration: LocaleConfiguration, /) -> Locale:
        return configuration.locale

    @property
    def default(self) -> LocaleConfiguration:
        """
        The default language.
        """
        return next(self.values())

    @property
    def multilingual(self) -> bool:
        """
        Whether the configuration is multilingual.
        """
        return len(self) > 1

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls([LocaleConfiguration.samples().get(Size.FULL).data]),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


class CopyrightNoticePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.copyright_notice.CopyrightNoticeDefinition`.

    .. configuration:: betty.project.config:CopyrightNoticePluginConfiguration
    """

    summary = LocalizableProperty(label=_("Summary"))
    text = LocalizableProperty(label=_("Text"))

    def __init__(
        self, *, summary: LocalizableLike, text: LocalizableLike, **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.summary = ensure_localizable(summary)
        self.text = ensure_localizable(text)

    @override
    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        return [
            *super().fields(),
            RequiredField("summary", assert_load_localizable),
            RequiredField("text", assert_load_localizable),
        ]

    @override
    def dump(self) -> PortableMapping:
        return {
            **super().dump(),
            "summary": dump_localizable(self.summary),
            "text": dump_localizable(self.text),
        }

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(
                        id="my-first-copyright-notice",
                        label="My First Copyright Notice",
                        summary="My First Copyright Notice is my first copyright notice",
                        text="My First Copyright Notice is my first copyright notice, all rights are reserved.",
                    ),
                    label="Default",
                )
            ]
        )


class CopyrightNoticePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        CopyrightNoticeDefinition, CopyrightNoticePluginConfiguration
    ]
):
    """
    A configuration mapping for copyright notices.

    .. configuration:: betty.project.config:CopyrightNoticePluginConfigurationMapping
    """

    @override
    @classmethod
    def _item_cls(cls) -> type[CopyrightNoticePluginConfiguration]:
        return CopyrightNoticePluginConfiguration

    @override
    def _new_plugin(
        self, configuration: CopyrightNoticePluginConfiguration, /
    ) -> CopyrightNoticeDefinition:
        @CopyrightNoticeDefinition(
            configuration.id,
            label=configuration.label,
            description=configuration.description,
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

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls(
                        [
                            CopyrightNoticePluginConfiguration.samples()
                            .get(Size.FULL)
                            .data
                        ]
                    ),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


class LicensePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.license.LicenseDefinition`.

    .. configuration:: betty.project.config:LicensePluginConfiguration
    """

    summary = LocalizableProperty(label=_("Summary"))
    text = LocalizableProperty(label=_("Text"))

    def __init__(
        self, *, summary: LocalizableLike, text: LocalizableLike, **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.summary = ensure_localizable(summary)
        self.text = ensure_localizable(text)

    @override
    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        return [
            *super().fields(),
            RequiredField("summary", assert_load_localizable),
            RequiredField("text", assert_load_localizable),
        ]

    @override
    def dump(self) -> PortableMapping:
        return {
            **super().dump(),
            "summary": dump_localizable(self.summary),
            "text": dump_localizable(self.text),
        }

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(
                        id="my-first-license",
                        label="My First License",
                        summary="My First License is my first license",
                        text="My First License is my first license, and allows you o...",
                    ),
                    label="Default",
                )
            ]
        )


class LicensePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[LicenseDefinition, LicensePluginConfiguration]
):
    """
    A configuration mapping for licenses.

    .. configuration:: betty.project.config:LicensePluginConfigurationMapping
    """

    @override
    @classmethod
    def _item_cls(cls) -> type[LicensePluginConfiguration]:
        return LicensePluginConfiguration

    @override
    def _new_plugin(
        self, configuration: LicensePluginConfiguration, /
    ) -> LicenseDefinition:
        @LicenseDefinition(
            configuration.id,
            label=configuration.label,
            description=configuration.description,
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

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls([LicensePluginConfiguration.samples().get(Size.FULL).data]),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


class EventTypePluginConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration,
    OrderedPluginDefinitionConfiguration,
):
    """
    Configure a :py:class:`betty.ancestry.event_type.EventTypeDefinition`.

    .. configuration:: betty.project.config:EventTypePluginConfiguration
    """

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(
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
            ]
        )


class EventTypePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        EventTypeDefinition, EventTypePluginConfiguration
    ]
):
    """
    A configuration mapping for event types.

    .. configuration:: betty.project.config:EventTypePluginConfigurationMapping
    """

    @override
    @classmethod
    def _item_cls(cls) -> type[EventTypePluginConfiguration]:
        return EventTypePluginConfiguration

    @override
    def _new_plugin(
        self, configuration: EventTypePluginConfiguration, /
    ) -> EventTypeDefinition:
        @EventTypeDefinition(
            configuration.id,
            label=configuration.label,
            label_plural=configuration.label_plural,
            label_countable=configuration.label_countable,
            description=configuration.description,
        )
        class _ProjectConfigurationEventType(EventType):
            pass

        return _ProjectConfigurationEventType.plugin()

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls([EventTypePluginConfiguration.samples().get(Size.FULL).data]),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


class PlaceTypePluginConfiguration(CountableHumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.place_type.PlaceTypeDefinition`.

    .. configuration:: betty.project.config:PlaceTypePluginConfiguration
    """

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(
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
            ]
        )


class PlaceTypePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        PlaceTypeDefinition, PlaceTypePluginConfiguration
    ]
):
    """
    A configuration mapping for place types.

    .. configuration:: betty.project.config:PlaceTypePluginConfigurationMapping
    """

    @override
    @classmethod
    def _item_cls(cls) -> type[PlaceTypePluginConfiguration]:
        return PlaceTypePluginConfiguration

    @override
    def _new_plugin(
        self, configuration: PlaceTypePluginConfiguration, /
    ) -> PlaceTypeDefinition:
        @PlaceTypeDefinition(
            configuration.id,
            label=configuration.label,
            label_plural=configuration.label_plural,
            label_countable=configuration.label_countable,
            description=configuration.description,
        )
        class _ProjectConfigurationPlaceType(PlaceType):
            pass

        return _ProjectConfigurationPlaceType.plugin()

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls([PlaceTypePluginConfiguration.samples().get(Size.FULL).data]),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


class PresenceRolePluginConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration
):
    """
    Configure a :py:class:`betty.ancestry.presence_role.PresenceRoleDefinition`.
    """

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(
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
            ]
        )


class PresenceRolePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        PresenceRoleDefinition, PresenceRolePluginConfiguration
    ]
):
    """
    A configuration mapping for presence roles.

    .. configuration:: betty.project.config:PresenceRolePluginConfigurationMapping
    """

    @override
    @classmethod
    def _item_cls(cls) -> type[PresenceRolePluginConfiguration]:
        return PresenceRolePluginConfiguration

    @override
    def _new_plugin(
        self, configuration: PresenceRolePluginConfiguration, /
    ) -> PresenceRoleDefinition:
        @PresenceRoleDefinition(
            configuration.id,
            label=configuration.label,
            label_plural=configuration.label_plural,
            label_countable=configuration.label_countable,
            description=configuration.description,
        )
        class _ProjectConfigurationPresenceRole(PresenceRole):
            pass

        return _ProjectConfigurationPresenceRole.plugin()

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls(
                        [PresenceRolePluginConfiguration.samples().get(Size.FULL).data]
                    ),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


class GenderPluginConfiguration(CountableHumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.gender.GenderDefinition`.

    .. configuration:: betty.project.config:GenderPluginConfiguration
    """

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(
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
            ]
        )


class GenderPluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[GenderDefinition, GenderPluginConfiguration]
):
    """
    A configuration mapping for genders.

    .. configuration:: betty.project.config:GenderPluginConfigurationMapping
    """

    @override
    @classmethod
    def _item_cls(cls) -> type[GenderPluginConfiguration]:
        return GenderPluginConfiguration

    @override
    def _new_plugin(
        self, configuration: GenderPluginConfiguration, /
    ) -> GenderDefinition:
        @GenderDefinition(
            configuration.id,
            label=configuration.label,
            label_plural=configuration.label_plural,
            label_countable=configuration.label_countable,
            description=configuration.description,
        )
        class _ProjectConfigurationGender(Gender):
            pass

        return _ProjectConfigurationGender.plugin()

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls([GenderPluginConfiguration.samples().get(Size.FULL).data]),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


@final
@ObjectDefinition(
    label=_("Project configuration"),
    fields=[
        FieldDefinition(
            Attr("copyright_notice"),
            DataDefinition(
                cls=PluginInstanceConfiguration, label=_("Copyright notice")
            ),
            omit_load=True,
            omit_dump=lambda data: data
            == ProjectConfiguration._default_copyright_notice(),
        ),
        FieldDefinition(
            Attr("license"),
            DataDefinition(cls=PluginInstanceConfiguration, label=_("License")),
            omit_load=True,
            omit_dump=lambda data: data == ProjectConfiguration._default_license(),
        ),
    ],
    samples=[
        lambda: Sample(
            ProjectConfiguration(title="Betty", url="https://example.com"),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            ProjectConfiguration(
                url="https://ancestry.example.com/betty",
                debug=True,
                clean_urls=True,
                title="Betty's ancestry",
                name="betty-ancestry",
                author="Bart Feenstra",
                logo=ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png",
                lifetime_threshold=123,
                locales=LocaleConfigurationMapping.samples().get(Size.FULL).data,
                entity_types=[
                    EntityTypeConfiguration.data().samples.get(Size.FULL).data
                ],
                event_types=EventTypePluginConfigurationMapping.samples()
                .get(Size.FULL)
                .data,
                extensions=ExtensionInstanceConfigurationMapping.samples()
                .get(Size.FULL)
                .data,
                genders=GenderPluginConfigurationMapping.samples().get(Size.FULL).data,
                place_types=PlaceTypePluginConfigurationMapping.samples()
                .get(Size.FULL)
                .data,
                presence_roles=PresenceRolePluginConfigurationMapping.samples()
                .get(Size.FULL)
                .data,
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

    license: PluginInstanceConfiguration[LicenseDefinition, License]
    """
    The project-wide license.
    """
    copyright_notice: PluginInstanceConfiguration[
        CopyrightNoticeDefinition, CopyrightNotice
    ]
    """
    The project-wide copyright notice.
    """
    title = LocalizableProperty(label=_("Title"))
    author = Optional(LocalizableProperty(label=_("Author")))

    def __init__(
        self,
        *,
        title: LocalizableLike,
        url: str,
        clean_urls: bool = False,
        author: LocalizableLike | None = None,
        entity_types: Iterable[EntityTypeConfiguration | ResolvableId[EntityDefinition]]
        | None = None,
        event_types: EventTypePluginConfigurationMapping | None = None,
        place_types: PlaceTypePluginConfigurationMapping | None = None,
        presence_roles: PresenceRolePluginConfigurationMapping | None = None,
        copyright_notice: PluginInstanceConfiguration[
            CopyrightNoticeDefinition, CopyrightNotice
        ]
        | None = None,
        copyright_notices: CopyrightNoticePluginConfigurationMapping | None = None,
        license: PluginInstanceConfiguration[LicenseDefinition, License] | None = None,  # noqa: A002
        licenses: LicensePluginConfigurationMapping | None = None,
        genders: GenderPluginConfigurationMapping | None = None,
        extensions: ExtensionInstanceConfigurationMapping | None = None,
        debug: bool = False,
        locales: LocaleConfigurationMapping | None = None,
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        name: MachineName | None = None,
        logo: Path | None = None,
    ):
        super().__init__()
        self._name = name
        self._url = url
        self._clean_urls = clean_urls
        self.title = title
        self.author = author
        self._entity_types = KeyedCollection(
            () if entity_types is None else entity_types,
            key=lambda item: item.entity_type,
            value_resolver=lambda data: data
            if isinstance(data, EntityTypeConfiguration)
            else EntityTypeConfiguration(entity_type=data),
        )
        self._event_types = (
            EventTypePluginConfigurationMapping()
            if event_types is None
            else event_types
        )
        self.copyright_notice = (
            self._default_copyright_notice()
            if copyright_notice is None
            else copyright_notice
        )
        self._copyright_notices = (
            CopyrightNoticePluginConfigurationMapping()
            if copyright_notices is None
            else copyright_notices
        )
        self.license = self._default_license() if license is None else license
        self._licenses = (
            LicensePluginConfigurationMapping() if licenses is None else licenses
        )
        self._locales = self._default_locales() if locales is None else locales
        self._place_types = (
            PlaceTypePluginConfigurationMapping()
            if place_types is None
            else place_types
        )
        self._presence_roles = (
            PresenceRolePluginConfigurationMapping()
            if presence_roles is None
            else presence_roles
        )
        self._genders = (
            GenderPluginConfigurationMapping() if genders is None else genders
        )
        self._extensions = (
            ExtensionInstanceConfigurationMapping()
            if extensions is None
            else extensions
        )
        self._debug = debug
        self._lifetime_threshold = lifetime_threshold
        self._logo = logo

    @classmethod
    def _default_copyright_notice(
        cls,
    ) -> PluginInstanceConfiguration[CopyrightNoticeDefinition, CopyrightNotice]:
        from betty.copyright_notice.copyright_notices import ProjectAuthor

        return PluginInstanceConfiguration[CopyrightNoticeDefinition, CopyrightNotice](
            ProjectAuthor
        )

    @classmethod
    def _default_license(
        cls,
    ) -> PluginInstanceConfiguration[LicenseDefinition, License]:
        from betty.license.licenses import AllRightsReserved

        return PluginInstanceConfiguration[LicenseDefinition, License](
            AllRightsReserved
        )

    @classmethod
    def _default_locales(cls) -> LocaleConfigurationMapping:
        return LocaleConfigurationMapping()

    @property
    @AttrDefinition(OptionalDefinition(MachineNameDefinition()))
    def name(self) -> MachineName | None:
        """
        The project's machine name.
        """
        return self._name

    @name.setter
    def name(self, name: MachineName) -> None:
        self._name = assert_machine_name()(name)

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
    @AttrDefinition(
        BoolDefinition(
            label=_("Clean URLs"),
            description=_(
                'Whether to use clean URLs: "/path" instead of "/path/index.html".'
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )
    def clean_urls(self) -> bool:
        """
        Whether to generate clean URLs such as ``/person/first-person`` instead of ``/person/first-person/index.html``.

        Generated artifacts will require web server that supports this.
        """
        return self._clean_urls

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool) -> None:
        self._clean_urls = clean_urls

    @property
    @AttrDefinition(
        DataDefinition(cls=LocaleConfigurationMapping, label=_("Locales")),
        omit_load=True,
        omit_dump=lambda data: data == ProjectConfiguration._default_locales(),
    )
    def locales(self) -> LocaleConfigurationMapping:
        """
        The available locales.
        """
        return self._locales

    @property
    @AttrDefinition(
        KeyedCollectionDefinition(
            item=EntityTypeConfiguration.data(),  # ty:ignore[invalid-argument-type]
            label=_("Entity types"),
            key=Attr("entity_type"),  # ty:ignore[invalid-argument-type]
            ordered=False,
        ),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    def entity_types(
        self,
    ) -> KeyedCollection[
        MachineName,
        EntityTypeConfiguration,
        ResolvableId[EntityDefinition],
        EntityTypeConfiguration | ResolvableId[EntityDefinition],
    ]:
        """
        The available entity types.
        """
        return self._entity_types

    @property
    @AttrDefinition(
        DataDefinition(
            cls=ExtensionInstanceConfigurationMapping, label=_("Extensions")
        ),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    def extensions(self) -> ExtensionInstanceConfigurationMapping:
        """
        Then extensions running within this application.
        """
        return self._extensions

    @property
    @AttrDefinition(
        BoolDefinition(
            label=_("Debugging mode"),
            description=_(
                "Whether to output more detailed logs and disable optimizations that make debugging harder."
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )
    def debug(self) -> bool:
        """
        Whether to enable debugging for project jobs.

        This setting is disabled by default.

        Enabling this generally results in:

        - More verbose logging output
        - job artifacts (e.g. generated sites)
        """
        return self._debug

    @debug.setter
    def debug(self, debug: bool) -> None:
        self._debug = debug

    @property
    @AttrDefinition(
        IntDefinition(
            label=_("Lifetime threshold"),
            description=_(
                "The number of years people are expected to live at most, e.g. after which they are presumed to have died."
            ),
        ),
        omit_load=True,
        omit_dump=lambda data: data == DEFAULT_LIFETIME_THRESHOLD,
    )
    def lifetime_threshold(self) -> int:
        """
        The lifetime threshold indicates when people are considered dead.

        This setting defaults to :py:const:`betty.project.config.DEFAULT_LIFETIME_THRESHOLD`.

        The value is an integer expressing the age in years over which people are
        presumed to have died.
        """
        return self._lifetime_threshold

    @lifetime_threshold.setter
    def lifetime_threshold(self, lifetime_threshold: int) -> None:
        assert_number(minimum=1)(lifetime_threshold)
        self._lifetime_threshold = lifetime_threshold

    @property
    @AttrDefinition(OptionalDefinition(FilePathDefinition()), label=_("Logo"))
    def logo(self) -> Path | None:
        """
        The path to the logo.
        """
        return self._logo

    @logo.setter
    def logo(self, logo: Path | None) -> None:
        self._logo = logo

    @property
    @AttrDefinition(
        DataDefinition(
            cls=CopyrightNoticePluginConfigurationMapping,
            label=_("Copyright notices"),
        ),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    def copyright_notices(
        self,
    ) -> CopyrightNoticePluginConfigurationMapping:
        """
        The :py:class:`betty.copyright_notice.CopyrightNotice` plugins created by this project.
        """
        return self._copyright_notices

    @property
    @AttrDefinition(
        DataDefinition(cls=LicensePluginConfigurationMapping, label=_("Licenses")),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    def licenses(self) -> LicensePluginConfigurationMapping:
        """
        The :py:class:`betty.license.License` plugins created by this project.
        """
        return self._licenses

    @property
    @AttrDefinition(
        DataDefinition(cls=EventTypePluginConfigurationMapping, label=_("Event types")),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    def event_types(self) -> EventTypePluginConfigurationMapping:
        """
        The event type plugins created by this project.
        """
        return self._event_types

    @property
    @AttrDefinition(
        DataDefinition(cls=PlaceTypePluginConfigurationMapping, label=_("Place types")),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    def place_types(self) -> PlaceTypePluginConfigurationMapping:
        """
        The place type plugins created by this project.
        """
        return self._place_types

    @property
    @AttrDefinition(
        DataDefinition(
            cls=PresenceRolePluginConfigurationMapping, label=_("Presence roles")
        ),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    def presence_roles(self) -> PresenceRolePluginConfigurationMapping:
        """
        The presence role plugins created by this project.
        """
        return self._presence_roles

    @property
    @AttrDefinition(
        DataDefinition(cls=GenderPluginConfigurationMapping, label=_("Genders")),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    def genders(self) -> GenderPluginConfigurationMapping:
        """
        The gender plugins created by this project.
        """
        return self._genders
