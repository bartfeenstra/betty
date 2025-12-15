"""
Provide project configuration.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from typing import TYPE_CHECKING, Any, Self, cast, final
from urllib.parse import urlparse

from babel import Locale
from typing_extensions import override

from betty.ancestry.event_type import EventType, EventTypeDefinition
from betty.ancestry.gender import Gender, GenderDefinition
from betty.ancestry.place_type import PlaceType, PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRole, PresenceRoleDefinition
from betty.assertion import (
    Field,
    OptionalField,
    RequiredField,
    assert_bool,
    assert_int,
    assert_locale,
    assert_none,
    assert_or,
    assert_path,
    assert_positive_number,
    assert_record,
    assert_str,
)
from betty.config import Configuration
from betty.config.collections.mapping import OrderedConfigurationMapping
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.data import Key
from betty.exception import (
    HumanFacingException,
    HumanFacingExceptionGroup,
    reraise_within_context,
)
from betty.license import License, LicenseDefinition
from betty.license.licenses import AllRightsReserved
from betty.locale import DEFAULT_LOCALE, LocaleLike, ensure_locale, to_language_tag
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.attr import (
    OptionalLocalizableAttr,
    RequiredLocalizableAttr,
)
from betty.locale.localizable.config import dump_localizable
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName, assert_machine_name
from betty.model import EntityDefinition
from betty.plugin.config import (
    CountableHumanFacingPluginDefinitionConfiguration,
    HumanFacingPluginDefinitionConfiguration,
    PluginDefinitionConfigurationMapping,
    PluginIdentifierKeyConfigurationMapping,
    PluginInstanceConfiguration,
    PluginInstanceConfigurationMapping,
)
from betty.plugin.config.ordered import OrderedPluginDefinitionConfiguration
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.factory import CallbackProjectDependentFactory

if TYPE_CHECKING:
    from pathlib import Path

    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.plugin.repository import PluginRepository
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping
    from betty.service.level.factory import AnyFactoryTarget

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
    """

    def enable(self, *extensions: ResolvableId[ExtensionDefinition]) -> None:
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
        entity_type: ResolvableId[EntityDefinition],
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
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        record = assert_record(
            RequiredField("entity_type", assert_machine_name()),
            OptionalField("generate_html_list", assert_bool()),
        )(dump)
        return cls(
            record["entity_type"],
            generate_html_list=record.get("generate_html_list", False),
        )

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "entity_type": self.id,
            "generate_html_list": self.generate_html_list,
        }

    async def validate(
        self, entity_type_repository: PluginRepository[EntityDefinition], /
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
    def _get_key(self, configuration: EntityTypeConfiguration, /) -> MachineName:
        return configuration.id

    @override
    @classmethod
    def _load_key(cls, item_dump: Dump, key_dump: str, /) -> Dump:
        assert isinstance(item_dump, Mapping)
        item_dump["entity_type"] = key_dump
        return item_dump

    @override
    def _dump_key(self, item_dump: Dump, /) -> tuple[Dump, str]:
        assert isinstance(item_dump, Mapping)
        return item_dump, cast(str, item_dump.pop("entity_type"))

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> EntityTypeConfiguration:
        return EntityTypeConfiguration.load(dump)

    async def validate(
        self, entity_type_repository: PluginRepository[EntityDefinition], /
    ) -> None:
        """
        Validate the configuration.
        """
        with HumanFacingExceptionGroup() as errors:
            for configuration in self.values():
                with errors.absorb(Key(configuration.id)):
                    await configuration.validate(entity_type_repository)


@final
class LocaleConfiguration(Configuration):
    """
    Configure a single project locale.
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
    def load(cls, dump: Dump, /) -> Self:
        record = assert_record(
            RequiredField("locale", assert_locale()),
            OptionalField("alias", assert_str()),
        )(dump)
        return cls(record["locale"], alias=record.get("alias", None))

    @override
    def dump(self) -> Dump:
        dump: Dump = {
            "locale": to_language_tag(self.locale),
        }
        if self._alias is not None:
            dump["alias"] = self._alias
        return dump


@final
class LocaleConfigurationMapping(
    OrderedConfigurationMapping[Locale, LocaleLike, LocaleConfiguration]
):
    """
    Configure a project's locales.
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
    def _load_item(cls, dump: Dump, /) -> LocaleConfiguration:
        return LocaleConfiguration.load(dump)

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


class CopyrightNoticePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.copyright_notice.CopyrightNoticeDefinition`.
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
    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        return [
            *super().fields(),
            RequiredField("summary", assert_load_localizable),
            RequiredField("text", assert_load_localizable),
        ]

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            **super().dump(),
            "summary": dump_localizable(self.summary),
            "text": dump_localizable(self.text),
        }


class CopyrightNoticePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        CopyrightNoticeDefinition, CopyrightNoticePluginConfiguration
    ]
):
    """
    A configuration mapping for copyright notices.
    """

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> CopyrightNoticePluginConfiguration:
        return CopyrightNoticePluginConfiguration.load(dump)

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


class LicensePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.license.LicenseDefinition`.
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
    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        return [
            *super().fields(),
            RequiredField("summary", assert_load_localizable),
            RequiredField("text", assert_load_localizable),
        ]

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            **super().dump(),
            "summary": dump_localizable(self.summary),
            "text": dump_localizable(self.text),
        }


class LicensePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[LicenseDefinition, LicensePluginConfiguration]
):
    """
    A configuration mapping for licenses.
    """

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> LicensePluginConfiguration:
        return LicensePluginConfiguration.load(dump)

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


class EventTypePluginConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration,
    OrderedPluginDefinitionConfiguration,
):
    """
    Configure a :py:class:`betty.ancestry.event_type.EventTypeDefinition`.
    """


class EventTypePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        EventTypeDefinition, EventTypePluginConfiguration
    ]
):
    """
    A configuration mapping for event types.
    """

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> EventTypePluginConfiguration:
        return EventTypePluginConfiguration.load(dump)

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


class PlaceTypePluginConfiguration(CountableHumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.place_type.PlaceTypeDefinition`.
    """


class PlaceTypePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        PlaceTypeDefinition, PlaceTypePluginConfiguration
    ]
):
    """
    A configuration mapping for place types.
    """

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> PlaceTypePluginConfiguration:
        return PlaceTypePluginConfiguration.load(dump)

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


class PresenceRolePluginConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration
):
    """
    Configure a :py:class:`betty.ancestry.presence_role.PresenceRoleDefinition`.
    """


class PresenceRolePluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[
        PresenceRoleDefinition, PresenceRolePluginConfiguration
    ]
):
    """
    A configuration mapping for presence roles.
    """

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> PresenceRolePluginConfiguration:
        return PresenceRolePluginConfiguration.load(dump)

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


class GenderPluginConfiguration(CountableHumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.gender.GenderDefinition`.
    """


class GenderPluginConfigurationMapping(
    PluginDefinitionConfigurationMapping[GenderDefinition, GenderPluginConfiguration]
):
    """
    A configuration mapping for genders.
    """

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> GenderPluginConfiguration:
        return GenderPluginConfiguration.load(dump)

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


@final
class ProjectConfiguration(Configuration):
    """
    Provide the configuration for a :py:class:`betty.project.Project`.
    """

    title = RequiredLocalizableAttr("title")
    author = OptionalLocalizableAttr("author")

    def __init__(
        self,
        *,
        url: str = "https://example.com",
        clean_urls: bool = False,
        title: LocalizableLike = "Betty",
        author: LocalizableLike | None = None,
        entity_types: EntityTypeConfigurationMapping | None = None,
        event_types: EventTypePluginConfigurationMapping | None = None,
        place_types: PlaceTypePluginConfigurationMapping | None = None,
        presence_roles: PresenceRolePluginConfigurationMapping | None = None,
        copyright_notice: PluginInstanceConfiguration[
            CopyrightNoticeDefinition, CopyrightNotice
        ]
        | None = None,
        copyright_notices: CopyrightNoticePluginConfigurationMapping | None = None,
        license: PluginInstanceConfiguration[LicenseDefinition, License] | None = None,  # noqa A002
        licenses: LicensePluginConfigurationMapping | None = None,
        genders: GenderPluginConfigurationMapping | None = None,
        extensions: ExtensionInstanceConfigurationMapping | None = None,
        debug: bool = False,
        locales: LocaleConfigurationMapping | None = None,
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        name: MachineName | None = None,
        logo: Path | None = None,
    ):
        from betty.copyright_notice.copyright_notices import ProjectAuthor

        super().__init__()
        self._name = name
        self._computed_name: str | None = None
        self._url = url
        self._clean_urls = clean_urls
        self.title = title
        self.author = author
        self._entity_types = (
            EntityTypeConfigurationMapping() if entity_types is None else entity_types
        )
        self.copyright_notice = copyright_notice or PluginInstanceConfiguration[
            CopyrightNoticeDefinition, CopyrightNotice
        ](ProjectAuthor)
        self._copyright_notices = (
            CopyrightNoticePluginConfigurationMapping()
            if copyright_notices is None
            else copyright_notices
        )
        self.license = license or PluginInstanceConfiguration[
            LicenseDefinition, License
        ](AllRightsReserved)
        self._licenses = (
            LicensePluginConfigurationMapping() if licenses is None else licenses
        )
        self._event_types = (
            EventTypePluginConfigurationMapping()
            if event_types is None
            else event_types
        )
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
        self._locales = LocaleConfigurationMapping() if locales is None else locales
        self._lifetime_threshold = lifetime_threshold
        self._logo = logo

    @override
    @property
    def validator(self) -> AnyFactoryTarget[None]:
        async def _validate(project: Project) -> None:
            with reraise_within_context(Key("entity_types")):
                await self.entity_types.validate(
                    await project.plugins(EntityDefinition)
                )

        return CallbackProjectDependentFactory(_validate)

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
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("name", assert_or(assert_str(), assert_none())),
                RequiredField("url", assert_str()),
                OptionalField("title", assert_load_localizable),
                OptionalField("author", assert_load_localizable),
                OptionalField("logo", assert_or(assert_path(), assert_none())),
                OptionalField("clean_urls", assert_bool()),
                OptionalField("debug", assert_bool()),
                OptionalField("lifetime_threshold", assert_int()),
                OptionalField("locales", LocaleConfigurationMapping.load),
                OptionalField("extensions", ExtensionInstanceConfigurationMapping.load),
                OptionalField("entity_types", EntityTypeConfigurationMapping.load),
                OptionalField("copyright_notice", PluginInstanceConfiguration.load),
                OptionalField(
                    "copyright_notices", CopyrightNoticePluginConfigurationMapping.load
                ),
                OptionalField("license", PluginInstanceConfiguration.load),
                OptionalField("licenses", LicensePluginConfigurationMapping.load),
                OptionalField("event_types", EventTypePluginConfigurationMapping.load),
                OptionalField("genders", GenderPluginConfigurationMapping.load),
                OptionalField("place_types", PlaceTypePluginConfigurationMapping.load),
                OptionalField(
                    "presence_roles", PresenceRolePluginConfigurationMapping.load
                ),
            )(dump)
        )

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
