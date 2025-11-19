"""
Provide project configuration.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, cast, final
from urllib.parse import urlparse

from typing_extensions import override

from betty.ancestry.event_type import EventType, EventTypeDefinition
from betty.ancestry.gender import Gender, GenderDefinition
from betty.ancestry.place_type import PlaceType, PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRole, PresenceRoleDefinition
from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_bool,
    assert_fields,
    assert_int,
    assert_locale,
    assert_mapping,
    assert_none,
    assert_or,
    assert_path,
    assert_positive_number,
    assert_record,
    assert_setattr,
    assert_str,
)
from betty.config import Configuration
from betty.config.collections.mapping import OrderedConfigurationMapping
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.data import Key
from betty.exception import HumanFacingException, HumanFacingExceptionGroup
from betty.license import License, LicenseDefinition
from betty.license.licenses import AllRightsReserved
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import Localizable, ShorthandStaticTranslations, _
from betty.locale.localizable.assertion import assert_static_translations
from betty.locale.localizable.config import (
    OptionalStaticTranslationsConfigurationAttr,
    RequiredStaticTranslationsConfigurationAttr,
)
from betty.machine_name import MachineName, assert_machine_name
from betty.model import Entity, EntityDefinition
from betty.plugin import plugins, resolve_id
from betty.plugin.config import (
    HumanFacingPluginDefinitionConfiguration,
    PluginDefinitionConfigurationMapping,
    PluginIdentifierKeyConfigurationMapping,
    PluginInstanceConfiguration,
    PluginInstanceConfigurationMapping,
)
from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration
from betty.project.extension import Extension, ExtensionDefinition
from betty.serde.format import FormatDefinition, format_for

if TYPE_CHECKING:
    from pathlib import Path

    from betty.plugin import PluginIdentifier, PluginRepository
    from betty.serde.dump import Dump, DumpMapping

#: The default age by which people are presumed dead.
#: This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
#: the oldest verified person to ever have lived.
DEFAULT_LIFETIME_THRESHOLD = 123


@final
class ExtensionInstanceConfigurationMapping(
    PluginInstanceConfigurationMapping[ExtensionDefinition, Extension]
):
    """
    Configure a project's enabled extensions.
    """

    def enable(
        self, *extensions: PluginIdentifier[ExtensionDefinition, Extension]
    ) -> None:
        """
        Enable the given extensions.
        """
        for extension in extensions:
            extension = resolve_id(extension)
            if extension not in self._configurations:
                self.append(PluginInstanceConfiguration(extension))


@final
class EntityTypeConfiguration(Configuration):
    """
    Configure a single entity type for a project.
    """

    def __init__(
        self,
        entity_type: PluginIdentifier[EntityDefinition, Entity],
        *,
        generate_html_list: bool = False,
    ):
        super().__init__()
        self._id = resolve_id(entity_type)
        self.generate_html_list = generate_html_list

    @property
    def id(self) -> MachineName:
        """
        The ID of the configured entity type.
        """
        return self._id

    @property
    def generate_html_list(self) -> bool:
        """
        Whether to generate listing web pages for entities of this type.
        """
        return self._generate_html_list

    @generate_html_list.setter
    def generate_html_list(self, generate_html_list: bool) -> None:
        self._generate_html_list = generate_html_list

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField[Any, type[Entity]](
                "id", assert_machine_name() | assert_setattr(self, "_id")
            ),
            OptionalField(
                "generate_html_list",
                assert_bool() | assert_setattr(self, "generate_html_list"),
            ),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "id": self.id,
            "generate_html_list": self.generate_html_list,
        }

    async def validate(
        self, entity_type_repository: PluginRepository[EntityDefinition]
    ) -> None:
        """
        Validate the configuration.
        """
        entity_type = entity_type_repository[self.id]
        if self.generate_html_list and not entity_type.public_facing:
            raise HumanFacingException(
                _(
                    "Cannot generate pages for {entity_type}, because it is not a public-facing entity type."
                ).format(entity_type=entity_type.label)
            )


@final
class EntityTypeConfigurationMapping(
    PluginIdentifierKeyConfigurationMapping[EntityDefinition, EntityTypeConfiguration]
):
    """
    Configure the entity types for a project.
    """

    @override
    def _get_key(self, configuration: EntityTypeConfiguration) -> MachineName:
        return configuration.id

    @override
    def _load_key(self, item_dump: Dump, key_dump: str) -> Dump:
        assert isinstance(item_dump, Mapping)
        item_dump["id"] = key_dump
        return item_dump

    @override
    def _dump_key(self, item_dump: Dump) -> tuple[Dump, str]:
        assert isinstance(item_dump, Mapping)
        return item_dump, cast(str, item_dump.pop("id"))

    @override
    def _load_item(self, dump: Dump) -> EntityTypeConfiguration:
        # Use a dummy entity type for now to satisfy the initializer.
        # It will be overridden when loading the dump.
        configuration = EntityTypeConfiguration("-")
        configuration.load(dump)
        return configuration

    async def validate(
        self, entity_type_repository: PluginRepository[EntityDefinition]
    ) -> None:
        """
        Validate the configuration.
        """
        with HumanFacingExceptionGroup().assert_valid() as errors:
            for configuration in self.values():
                with errors.catch(Key(configuration.id)):
                    await configuration.validate(entity_type_repository)


@final
class LocaleConfiguration(Configuration):
    """
    Configure a single project locale.
    """

    def __init__(
        self,
        locale: str,
        *,
        alias: str | None = None,
    ):
        super().__init__()
        self._locale = locale
        if alias is not None and "/" in alias:
            raise HumanFacingException(_("Locale aliases must not contain slashes."))
        self._alias = alias

    @property
    def locale(self) -> str:
        """
        An `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
        """
        return self._locale

    @property
    def alias(self) -> str:
        """
        A shorthand alias to use instead of the full language tag, such as when rendering URLs.
        """
        if self._alias is None:
            return self.locale
        return self._alias

    @alias.setter
    def alias(self, alias: str | None) -> None:
        self._alias = alias

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("locale", assert_locale() | assert_setattr(self, "_locale")),
            OptionalField(
                "alias",
                assert_or(assert_str() | assert_setattr(self, "alias"), assert_none()),
            ),
        )(dump)

    @override
    def dump(self) -> Dump:
        return {"locale": self.locale, "alias": self._alias}


@final
class LocaleConfigurationMapping(OrderedConfigurationMapping[str, LocaleConfiguration]):
    """
    Configure a project's locales.
    """

    def __init__(self, configurations: Iterable[LocaleConfiguration] | None = None, /):
        super().__init__(configurations)
        self._ensure_locale()

    @override
    def _post_remove(self, configuration: LocaleConfiguration) -> None:
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
    def _load_item(self, dump: Dump) -> LocaleConfiguration:
        item = LocaleConfiguration(UNDETERMINED_LOCALE)
        item.load(dump)
        return item

    @override
    def _get_key(self, configuration: LocaleConfiguration) -> str:
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


class CopyrightNoticeDefinitionConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.copyright_notice.CopyrightNoticeDefinition`.
    """

    summary = RequiredStaticTranslationsConfigurationAttr("summary")
    text = RequiredStaticTranslationsConfigurationAttr("text")

    def __init__(
        self,
        *,
        summary: ShorthandStaticTranslations,
        text: ShorthandStaticTranslations,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.summary = summary
        self.text = text

    @override
    def load(self, dump: Dump) -> None:
        mapping = assert_mapping()(dump)
        assert_fields(
            RequiredField(
                "summary",
                assert_static_translations() | assert_setattr(self, "summary"),
            ),
            RequiredField(
                "text",
                assert_static_translations() | assert_setattr(self, "text"),
            ),
        )(mapping)
        mapping.pop("summary", None)
        mapping.pop("text", None)
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            **super().dump(),
            "summary": self.summary.dump(),
            "text": self.text.dump(),
        }


class CopyrightNoticeDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        CopyrightNoticeDefinition, CopyrightNoticeDefinitionConfiguration
    ]
):
    """
    A configuration mapping for copyright notices.
    """

    @override
    def _load_item(self, dump: Dump) -> CopyrightNoticeDefinitionConfiguration:
        item = CopyrightNoticeDefinitionConfiguration(
            id="-", label="", summary="", text=""
        )
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: CopyrightNoticeDefinitionConfiguration
    ) -> CopyrightNoticeDefinition:
        class _ProjectConfigurationCopyrightNotice(CopyrightNotice):
            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return CopyrightNoticeDefinition(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
            cls=_ProjectConfigurationCopyrightNotice,
        )


class LicenseDefinitionConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.license.LicenseDefinition`.
    """

    summary = RequiredStaticTranslationsConfigurationAttr("summary")
    text = RequiredStaticTranslationsConfigurationAttr("text")

    def __init__(
        self,
        *,
        summary: ShorthandStaticTranslations,
        text: ShorthandStaticTranslations,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.summary = summary
        self.text = text

    @override
    def load(self, dump: Dump) -> None:
        mapping = assert_mapping()(dump)
        assert_fields(
            RequiredField(
                "summary",
                assert_static_translations() | assert_setattr(self, "summary"),
            ),
            RequiredField(
                "text",
                assert_static_translations() | assert_setattr(self, "text"),
            ),
        )(mapping)
        mapping.pop("summary", None)
        mapping.pop("text", None)
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            **super().dump(),
            "summary": self.summary.dump(),
            "text": self.text.dump(),
        }


class LicenseDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        LicenseDefinition, LicenseDefinitionConfiguration
    ]
):
    """
    A configuration mapping for licenses.
    """

    @override
    def _load_item(self, dump: Dump) -> LicenseDefinitionConfiguration:
        item = LicenseDefinitionConfiguration(id="-", label="", summary="", text="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: LicenseDefinitionConfiguration
    ) -> LicenseDefinition:
        class _ProjectConfigurationLicense(License):
            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return LicenseDefinition(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
            cls=_ProjectConfigurationLicense,
        )


class EventTypeDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration, OrderedPluginDefinitionConfiguration
):
    """
    Configure a :py:class:`betty.ancestry.event_type.EventTypeDefinition`.
    """


class EventTypeDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        EventTypeDefinition, EventTypeDefinitionConfiguration
    ]
):
    """
    A configuration mapping for event types.
    """

    @override
    def _load_item(self, dump: Dump) -> EventTypeDefinitionConfiguration:
        item = EventTypeDefinitionConfiguration(id="-", label="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: EventTypeDefinitionConfiguration
    ) -> EventTypeDefinition:
        return EventTypeDefinition(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
            cls=EventType,
        )


class PlaceTypeDefinitionConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.place_type.PlaceTypeDefinition`.
    """


class PlaceTypeDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        PlaceTypeDefinition, PlaceTypeDefinitionConfiguration
    ]
):
    """
    A configuration mapping for place types.
    """

    @override
    def _load_item(self, dump: Dump) -> PlaceTypeDefinitionConfiguration:
        item = PlaceTypeDefinitionConfiguration(id="-", label="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: PlaceTypeDefinitionConfiguration
    ) -> PlaceTypeDefinition:
        return PlaceTypeDefinition(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
            cls=PlaceType,
        )


class PresenceRoleDefinitionConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.presence_role.PresenceRoleDefinition`.
    """


class PresenceRoleDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        PresenceRoleDefinition, PresenceRoleDefinitionConfiguration
    ]
):
    """
    A configuration mapping for presence roles.
    """

    @override
    def _load_item(self, dump: Dump) -> PresenceRoleDefinitionConfiguration:
        item = PresenceRoleDefinitionConfiguration(id="-", label="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: PresenceRoleDefinitionConfiguration
    ) -> PresenceRoleDefinition:
        return PresenceRoleDefinition(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
            cls=PresenceRole,
        )


class GenderDefinitionConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.gender.GenderDefinition`.
    """


class GenderDefinitionConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        GenderDefinition, GenderDefinitionConfiguration
    ]
):
    """
    A configuration mapping for genders.
    """

    @override
    def _load_item(self, dump: Dump) -> GenderDefinitionConfiguration:
        item = GenderDefinitionConfiguration(id="-", label="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: GenderDefinitionConfiguration
    ) -> GenderDefinition:
        return GenderDefinition(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
            cls=Gender,
        )


@final
class ProjectConfiguration(Configuration):
    """
    Provide the configuration for a :py:class:`betty.project.Project`.
    """

    title = OptionalStaticTranslationsConfigurationAttr("title")
    author = OptionalStaticTranslationsConfigurationAttr("author")

    def __init__(
        self,
        configuration_file_path: Path,
        *,
        url: str = "https://example.com",
        clean_urls: bool = False,
        title: ShorthandStaticTranslations = "Betty",
        author: ShorthandStaticTranslations | None = None,
        entity_types: Iterable[EntityTypeConfiguration] | None = None,
        event_types: Iterable[EventTypeDefinitionConfiguration] | None = None,
        place_types: Iterable[PlaceTypeDefinitionConfiguration] | None = None,
        presence_roles: Iterable[PresenceRoleDefinitionConfiguration] | None = None,
        copyright_notice: PluginInstanceConfiguration[
            CopyrightNoticeDefinition, CopyrightNotice
        ]
        | None = None,
        copyright_notices: Iterable[CopyrightNoticeDefinitionConfiguration]
        | None = None,
        license: PluginInstanceConfiguration[LicenseDefinition, License] | None = None,  # noqa A002
        licenses: Iterable[LicenseDefinitionConfiguration] | None = None,
        genders: Iterable[GenderDefinitionConfiguration] | None = None,
        extensions: Iterable[
            PluginInstanceConfiguration[ExtensionDefinition, Extension]
        ]
        | None = None,
        debug: bool = False,
        locales: Iterable[LocaleConfiguration] | None = None,
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        name: MachineName | None = None,
        logo: Path | None = None,
    ):
        from betty.copyright_notice.copyright_notices import ProjectAuthor

        super().__init__()
        self._configuration_file_path = configuration_file_path
        self._name = name
        self._computed_name: str | None = None
        self._url = url
        self._clean_urls = clean_urls
        self.title = title
        if author:
            self.author = author
        self._entity_types = EntityTypeConfigurationMapping(entity_types or ())
        self.copyright_notice = copyright_notice or PluginInstanceConfiguration[
            CopyrightNoticeDefinition, CopyrightNotice
        ](ProjectAuthor)
        self._copyright_notices = CopyrightNoticeDefinitionConfigurationMapping()
        if copyright_notices is not None:
            self._copyright_notices.append(*copyright_notices)
        self.license = license or PluginInstanceConfiguration[
            LicenseDefinition, License
        ](AllRightsReserved)
        self._licenses = LicenseDefinitionConfigurationMapping()
        if licenses is not None:
            self._licenses.append(*licenses)
        self._event_types = EventTypeDefinitionConfigurationMapping()
        if event_types is not None:
            self._event_types.append(*event_types)
        self._place_types = PlaceTypeDefinitionConfigurationMapping()
        if place_types is not None:
            self._place_types.append(*place_types)
        self._presence_roles = PresenceRoleDefinitionConfigurationMapping()
        if presence_roles is not None:
            self._presence_roles.append(*presence_roles)
        self._genders = GenderDefinitionConfigurationMapping()
        if genders is not None:
            self._genders.append(*genders)
        self._extensions = ExtensionInstanceConfigurationMapping(extensions or ())
        self._debug = debug
        self._locales = LocaleConfigurationMapping(locales or ())
        self._lifetime_threshold = lifetime_threshold
        self._logo = logo

    @property
    def configuration_file_path(self) -> Path:
        """
        The path to the configuration's file.
        """
        return self._configuration_file_path

    async def set_configuration_file_path(self, configuration_file_path: Path) -> None:
        """
        Set the path to the configuration's file.
        """
        self.assert_mutable()
        if configuration_file_path == self._configuration_file_path:
            return
        format_for(
            list(await plugins(FormatDefinition)), configuration_file_path.suffix
        )
        self._configuration_file_path = configuration_file_path

    @property
    def name(self) -> MachineName | None:
        """
        The project's machine name.
        """
        return self._name

    @name.setter
    def name(self, name: MachineName) -> None:
        self.assert_mutable()
        self._name = assert_machine_name()(name)

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

    def localize_www_directory_path(self, locale: str) -> Path:
        """
        Get the WWW directory path for a locale.
        """
        if self.locales.multilingual:
            return self.www_directory_path / self.locales[locale].alias
        return self.www_directory_path

    @property
    def url(self) -> str:
        """
        The project's public URL.
        """
        return self._url

    @url.setter
    def url(self, url: str) -> None:
        self.assert_mutable()
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
    def clean_urls(self) -> bool:
        """
        Whether to generate clean URLs such as ``/person/first-person`` instead of ``/person/first-person/index.html``.

        Generated artifacts will require web server that supports this.
        """
        return self._clean_urls

    @clean_urls.setter
    def clean_urls(self, clean_urls: bool) -> None:
        self.assert_mutable()
        self._clean_urls = clean_urls

    @property
    def locales(self) -> LocaleConfigurationMapping:
        """
        The available locales.
        """
        return self._locales

    @property
    def entity_types(self) -> EntityTypeConfigurationMapping:
        """
        The available entity types.
        """
        return self._entity_types

    @property
    def extensions(self) -> ExtensionInstanceConfigurationMapping:
        """
        Then extensions running within this application.
        """
        return self._extensions

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

    @debug.setter
    def debug(self, debug: bool) -> None:
        self.assert_mutable()
        self._debug = debug

    @property
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
        self.assert_mutable()
        assert_positive_number()(lifetime_threshold)
        self._lifetime_threshold = lifetime_threshold

    @property
    def logo(self) -> Path | None:
        """
        The path to the logo.
        """
        return self._logo

    @logo.setter
    def logo(self, logo: Path | None) -> None:
        self.assert_mutable()
        self._logo = logo

    @property
    def copyright_notices(
        self,
    ) -> CopyrightNoticeDefinitionConfigurationMapping:
        """
        The :py:class:`betty.copyright_notice.CopyrightNotice` plugins created by this project.
        """
        return self._copyright_notices

    @property
    def licenses(self) -> LicenseDefinitionConfigurationMapping:
        """
        The :py:class:`betty.license.License` plugins created by this project.
        """
        return self._licenses

    @property
    def event_types(self) -> EventTypeDefinitionConfigurationMapping:
        """
        The event type plugins created by this project.
        """
        return self._event_types

    @property
    def place_types(self) -> PlaceTypeDefinitionConfigurationMapping:
        """
        The place type plugins created by this project.
        """
        return self._place_types

    @property
    def presence_roles(self) -> PresenceRoleDefinitionConfigurationMapping:
        """
        The presence role plugins created by this project.
        """
        return self._presence_roles

    @property
    def genders(self) -> GenderDefinitionConfigurationMapping:
        """
        The gender plugins created by this project.
        """
        return self._genders

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        assert_record(
            OptionalField(
                "name",
                assert_or(assert_str() | assert_setattr(self, "name"), assert_none()),
            ),
            RequiredField("url", assert_str() | assert_setattr(self, "url")),
            OptionalField("title", self.title.load),
            OptionalField("author", self.author.load),
            OptionalField(
                "logo",
                assert_or(assert_path() | assert_setattr(self, "logo"), assert_none()),
            ),
            OptionalField(
                "clean_urls",
                assert_bool() | assert_setattr(self, "clean_urls"),
            ),
            OptionalField("debug", assert_bool() | assert_setattr(self, "debug")),
            OptionalField(
                "lifetime_threshold",
                assert_int() | assert_setattr(self, "lifetime_threshold"),
            ),
            OptionalField("locales", self.locales.load),
            OptionalField("extensions", self.extensions.load),
            OptionalField("entity_types", self.entity_types.load),
            OptionalField("copyright_notice", self.copyright_notice.load),
            OptionalField("copyright_notices", self.copyright_notices.load),
            OptionalField("license", self.license.load),
            OptionalField("licenses", self.licenses.load),
            OptionalField("event_types", self.event_types.load),
            OptionalField("genders", self.genders.load),
            OptionalField("place_types", self.place_types.load),
            OptionalField("presence_roles", self.presence_roles.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump: DumpMapping[Dump] = {
            "name": self.name,
            "url": self.url,
            "title": self.title.dump(),
            "clean_urls": self.clean_urls,
            "author": self.author.dump(),
            "logo": str(self._logo) if self._logo else None,
            "debug": self.debug,
            "lifetime_threshold": self.lifetime_threshold,
            "locales": self.locales.dump(),
            "extensions": self.extensions.dump(),
            "entity_types": self.entity_types.dump(),
            "copyright_notice": self.copyright_notice.dump(),
            "copyright_notices": self.copyright_notices.dump(),
            "license": self.license.dump(),
            "licenses": self.licenses.dump(),
            "event_types": self.event_types.dump(),
            "genders": self.genders.dump(),
            "place_types": self.place_types.dump(),
            "presence_roles": self.presence_roles.dump(),
        }
        return dump
