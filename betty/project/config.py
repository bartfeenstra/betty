"""
Provide project configuration.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, cast, final
from urllib.parse import urlparse

from typing_extensions import override

from betty.ancestry.event_type import EventType, EventTypePlugin
from betty.ancestry.gender import Gender, GenderPlugin
from betty.ancestry.place_type import PlaceType, PlaceTypePlugin
from betty.ancestry.presence_role import PresenceRole, PresenceRolePlugin
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
from betty.copyright_notice import CopyrightNotice, CopyrightNoticePlugin
from betty.data import Key
from betty.exception import HumanFacingException, HumanFacingExceptionGroup
from betty.license import License, LicensePlugin
from betty.license.licenses import AllRightsReserved
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import (
    Localizable,
    LocalizableLike,
    OptionalLocalizableAttr,
    RequiredLocalizableAttr,
    _,
    ensure_localizable,
)
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.config import dump_localizable
from betty.machine_name import MachineName, assert_machine_name
from betty.model import Entity, EntityPlugin
from betty.plugin.config import (
    HumanFacingPluginDefinitionConfiguration,
    PluginDefinitionConfigurationMapping,
    PluginIdentifierKeyConfigurationMapping,
    PluginInstanceConfiguration,
    PluginInstanceConfigurationMapping,
)
from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration
from betty.plugin.repository.provider.service import plugins
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.project.extension import Extension, ExtensionPlugin
from betty.serde.format import FormatPlugin, format_for

if TYPE_CHECKING:
    from pathlib import Path

    from betty.plugin.repository import PluginRepository
    from betty.serde.dump import Dump, DumpMapping

DEFAULT_LIFETIME_THRESHOLD = 123
"""
The default age by which people are presumed dead.

This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
the oldest verified person to ever have lived.
"""


@final
class ExtensionInstanceConfigurationMapping(
    PluginInstanceConfigurationMapping[ExtensionPlugin, Extension]
):
    """
    Configure a project's enabled extensions.
    """

    def enable(self, *extensions: ResolvableId[ExtensionPlugin, Extension]) -> None:
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
        entity_type: ResolvableId[EntityPlugin, Entity],
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
    def load(self, dump: Dump, /) -> None:
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
        self, entity_type_repository: PluginRepository[EntityPlugin], /
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
    PluginIdentifierKeyConfigurationMapping[EntityPlugin, EntityTypeConfiguration]
):
    """
    Configure the entity types for a project.
    """

    @override
    def _get_key(self, configuration: EntityTypeConfiguration, /) -> MachineName:
        return configuration.id

    @override
    def _load_key(self, item_dump: Dump, key_dump: str, /) -> Dump:
        assert isinstance(item_dump, Mapping)
        item_dump["id"] = key_dump
        return item_dump

    @override
    def _dump_key(self, item_dump: Dump, /) -> tuple[Dump, str]:
        assert isinstance(item_dump, Mapping)
        return item_dump, cast(str, item_dump.pop("id"))

    @override
    def _load_item(self, dump: Dump, /) -> EntityTypeConfiguration:
        # Use a dummy entity type for now to satisfy the initializer.
        # It will be overridden when loading the dump.
        configuration = EntityTypeConfiguration("-")
        configuration.load(dump)
        return configuration

    async def validate(
        self, entity_type_repository: PluginRepository[EntityPlugin], /
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
    def load(self, dump: Dump, /) -> None:
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
    def _load_item(self, dump: Dump, /) -> LocaleConfiguration:
        item = LocaleConfiguration(UNDETERMINED_LOCALE)
        item.load(dump)
        return item

    @override
    def _get_key(self, configuration: LocaleConfiguration, /) -> str:
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


class CopyrightNoticePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.copyright_notice.CopyrightNoticePlugin`.
    """

    summary = RequiredLocalizableAttr("summary")
    text = RequiredLocalizableAttr("text")

    def __init__(
        self, *, summary: LocalizableLike, text: LocalizableLike, **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.summary = ensure_localizable(summary)
        self.text = ensure_localizable(text)

    @override
    def load(self, dump: Dump, /) -> None:
        mapping = assert_mapping()(dump)
        assert_fields(
            RequiredField(
                "summary", assert_load_localizable | assert_setattr(self, "summary")
            ),
            RequiredField(
                "text", assert_load_localizable | assert_setattr(self, "text")
            ),
        )(mapping)
        mapping.pop("summary", None)
        mapping.pop("text", None)
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            **super().dump(),
            "summary": dump_localizable(self.summary),
            "text": dump_localizable(self.text),
        }


class CopyrightNoticePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        CopyrightNoticePlugin, CopyrightNoticePluginConfiguration
    ]
):
    """
    A configuration mapping for copyright notices.
    """

    @override
    def _load_item(self, dump: Dump, /) -> CopyrightNoticePluginConfiguration:
        item = CopyrightNoticePluginConfiguration(id="-", label="", summary="", text="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: CopyrightNoticePluginConfiguration, /
    ) -> CopyrightNoticePlugin:
        @CopyrightNoticePlugin(
            id=configuration.id,
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

        return _ProjectConfigurationCopyrightNotice.plugin


class LicensePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.license.LicensePlugin`.
    """

    summary = RequiredLocalizableAttr("summary")
    text = RequiredLocalizableAttr("text")

    def __init__(
        self, *, summary: LocalizableLike, text: LocalizableLike, **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.summary = ensure_localizable(summary)
        self.text = ensure_localizable(text)

    @override
    def load(self, dump: Dump, /) -> None:
        mapping = assert_mapping()(dump)
        assert_fields(
            RequiredField(
                "summary", assert_load_localizable | assert_setattr(self, "summary")
            ),
            RequiredField(
                "text", assert_load_localizable | assert_setattr(self, "text")
            ),
        )(mapping)
        mapping.pop("summary", None)
        mapping.pop("text", None)
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            **super().dump(),
            "summary": dump_localizable(self.summary),
            "text": dump_localizable(self.text),
        }


class LicensePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[LicensePlugin, LicensePluginConfiguration]
):
    """
    A configuration mapping for licenses.
    """

    @override
    def _load_item(self, dump: Dump, /) -> LicensePluginConfiguration:
        item = LicensePluginConfiguration(id="-", label="", summary="", text="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: LicensePluginConfiguration, /
    ) -> LicensePlugin:
        @LicensePlugin(
            id=configuration.id,
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

        return _ProjectConfigurationLicense.plugin


class EventTypePluginConfiguration(
    HumanFacingPluginDefinitionConfiguration, OrderedPluginDefinitionConfiguration
):
    """
    Configure a :py:class:`betty.ancestry.event_type.EventTypePlugin`.
    """


class EventTypePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[EventTypePlugin, EventTypePluginConfiguration]
):
    """
    A configuration mapping for event types.
    """

    @override
    def _load_item(self, dump: Dump, /) -> EventTypePluginConfiguration:
        item = EventTypePluginConfiguration(id="-", label="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: EventTypePluginConfiguration, /
    ) -> EventTypePlugin:
        @EventTypePlugin(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
        )
        class _ProjectConfigurationEventType(EventType):
            pass

        return _ProjectConfigurationEventType.plugin


class PlaceTypePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.place_type.PlaceTypePlugin`.
    """


class PlaceTypePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[PlaceTypePlugin, PlaceTypePluginConfiguration]
):
    """
    A configuration mapping for place types.
    """

    @override
    def _load_item(self, dump: Dump, /) -> PlaceTypePluginConfiguration:
        item = PlaceTypePluginConfiguration(id="-", label="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: PlaceTypePluginConfiguration, /
    ) -> PlaceTypePlugin:
        @PlaceTypePlugin(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
        )
        class _ProjectConfigurationPlaceType(PlaceType):
            pass

        return _ProjectConfigurationPlaceType.plugin


class PresenceRolePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.presence_role.PresenceRolePlugin`.
    """


class PresenceRolePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        PresenceRolePlugin, PresenceRolePluginConfiguration
    ]
):
    """
    A configuration mapping for presence roles.
    """

    @override
    def _load_item(self, dump: Dump, /) -> PresenceRolePluginConfiguration:
        item = PresenceRolePluginConfiguration(id="-", label="")
        item.load(dump)
        return item

    @override
    def _new_plugin(
        self, configuration: PresenceRolePluginConfiguration, /
    ) -> PresenceRolePlugin:
        @PresenceRolePlugin(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
        )
        class _ProjectConfigurationPresenceRole(PresenceRole):
            pass

        return _ProjectConfigurationPresenceRole.plugin


class GenderPluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.gender.GenderPlugin`.
    """


class GenderPluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[GenderPlugin, GenderPluginConfiguration]
):
    """
    A configuration mapping for genders.
    """

    @override
    def _load_item(self, dump: Dump, /) -> GenderPluginConfiguration:
        item = GenderPluginConfiguration(id="-", label="")
        item.load(dump)
        return item

    @override
    def _new_plugin(self, configuration: GenderPluginConfiguration, /) -> GenderPlugin:
        @GenderPlugin(
            id=configuration.id,
            label=configuration.label,
            description=configuration.description,
        )
        class _ProjectConfigurationGender(Gender):
            pass

        return _ProjectConfigurationGender.plugin


@final
class ProjectConfiguration(Configuration):
    """
    Provide the configuration for a :py:class:`betty.project.Project`.
    """

    title = RequiredLocalizableAttr("title")
    author = OptionalLocalizableAttr("author")

    def __init__(
        self,
        configuration_file_path: Path,
        *,
        url: str = "https://example.com",
        clean_urls: bool = False,
        title: LocalizableLike = "Betty",
        author: LocalizableLike | None = None,
        entity_types: Iterable[EntityTypeConfiguration] | None = None,
        event_types: Iterable[EventTypePluginConfiguration] | None = None,
        place_types: Iterable[PlaceTypePluginConfiguration] | None = None,
        presence_roles: Iterable[PresenceRolePluginConfiguration] | None = None,
        copyright_notice: PluginInstanceConfiguration[
            CopyrightNoticePlugin, CopyrightNotice
        ]
        | None = None,
        copyright_notices: Iterable[CopyrightNoticePluginConfiguration] | None = None,
        license: PluginInstanceConfiguration[LicensePlugin, License] | None = None,  # noqa A002
        licenses: Iterable[LicensePluginConfiguration] | None = None,
        genders: Iterable[GenderPluginConfiguration] | None = None,
        extensions: Iterable[PluginInstanceConfiguration[ExtensionPlugin, Extension]]
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
        self.title = ensure_localizable(title)
        if author:
            self.author = ensure_localizable(author)
        self._entity_types = EntityTypeConfigurationMapping(entity_types or ())
        self.copyright_notice = copyright_notice or PluginInstanceConfiguration[
            CopyrightNoticePlugin, CopyrightNotice
        ](ProjectAuthor)
        self._copyright_notices = CopyrightNoticePluginConfigurationMapping()
        if copyright_notices is not None:
            self._copyright_notices.append(*copyright_notices)
        self.license = license or PluginInstanceConfiguration[LicensePlugin, License](
            AllRightsReserved
        )
        self._licenses = LicensePluginConfigurationMapping()
        if licenses is not None:
            self._licenses.append(*licenses)
        self._event_types = EventTypePluginConfigurationMapping()
        if event_types is not None:
            self._event_types.append(*event_types)
        self._place_types = PlaceTypePluginConfigurationMapping()
        if place_types is not None:
            self._place_types.append(*place_types)
        self._presence_roles = PresenceRolePluginConfigurationMapping()
        if presence_roles is not None:
            self._presence_roles.append(*presence_roles)
        self._genders = GenderPluginConfigurationMapping()
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

    async def set_configuration_file_path(
        self, configuration_file_path: Path, /
    ) -> None:
        """
        Set the path to the configuration's file.
        """
        self.assert_mutable()
        if configuration_file_path == self._configuration_file_path:
            return
        format_for(list(await plugins(FormatPlugin)), configuration_file_path.suffix)
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
    ) -> CopyrightNoticePluginConfigurationMapping:
        """
        The :py:class:`betty.copyright_notice.CopyrightNotice` plugins created by this project.
        """
        return self._copyright_notices

    @property
    def licenses(self) -> LicensePluginConfigurationMapping:
        """
        The :py:class:`betty.license.License` plugins created by this project.
        """
        return self._licenses

    @property
    def event_types(self) -> EventTypePluginConfigurationMapping:
        """
        The event type plugins created by this project.
        """
        return self._event_types

    @property
    def place_types(self) -> PlaceTypePluginConfigurationMapping:
        """
        The place type plugins created by this project.
        """
        return self._place_types

    @property
    def presence_roles(self) -> PresenceRolePluginConfigurationMapping:
        """
        The presence role plugins created by this project.
        """
        return self._presence_roles

    @property
    def genders(self) -> GenderPluginConfigurationMapping:
        """
        The gender plugins created by this project.
        """
        return self._genders

    @override
    def load(self, dump: Dump, /) -> None:
        self.assert_mutable()
        assert_record(
            OptionalField(
                "name",
                assert_or(assert_str() | assert_setattr(self, "name"), assert_none()),
            ),
            RequiredField("url", assert_str() | assert_setattr(self, "url")),
            OptionalField(
                "title", assert_load_localizable | assert_setattr(self, "title")
            ),
            OptionalField(
                "author", assert_load_localizable | assert_setattr(self, "author")
            ),
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
            "title": dump_localizable(self.title),
            "clean_urls": self.clean_urls,
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
        if self.author is not None:
            dump["author"] = dump_localizable(self.author)
        return dump
