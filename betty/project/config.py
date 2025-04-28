"""
Provide project configuration.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from reprlib import recursive_repr
from typing import TYPE_CHECKING, Any, Self, cast, final
from urllib.parse import urlparse

from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type import EventType
from betty.ancestry.gender import Gender
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.place_type import PlaceType
from betty.ancestry.presence_role import PresenceRole
from betty.ancestry.source import Source
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
from betty.assertion.error import AssertionFailed, AssertionFailedGroup, Key
from betty.config import Configuration
from betty.config.collections.mapping import (
    OrderedConfigurationMapping,
)
from betty.copyright_notice import CopyrightNotice
from betty.license import License
from betty.license.licenses import AllRightsReserved
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import Localizable, ShorthandStaticTranslations, _
from betty.locale.localizable.assertion import assert_static_translations
from betty.locale.localizable.config import (
    OptionalStaticTranslationsLocalizableConfigurationAttr,
    RequiredStaticTranslationsLocalizableConfigurationAttr,
)
from betty.machine_name import MachineName, assert_machine_name
from betty.model import Entity
from betty.plugin import (
    PluginRepository,
    ShorthandPluginBase,
)
from betty.plugin.config import (
    PluginConfiguration,
    PluginConfigurationMapping,
    PluginConfigurationPluginConfigurationMapping,
    PluginIdentifierKeyConfigurationMapping,
    PluginInstanceConfiguration,
    PluginInstanceConfigurationMapping,
)
from betty.project.extension import Extension
from betty.repr import repr_instance
from betty.serde.format import FORMAT_REPOSITORY, Format, format_for
from betty.user import UserFacing

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from betty.serde.dump import Dump, DumpMapping


#: The default age by which people are presumed dead.
#: This is based on `Jeanne Louise Calment <https://www.guinnessworldrecords.com/world-records/oldest-person/>`_ who is
#: the oldest verified person to ever have lived.
DEFAULT_LIFETIME_THRESHOLD = 123


@final
class ExtensionInstanceConfigurationMapping(
    PluginInstanceConfigurationMapping[Extension]
):
    """
    Configure a project's enabled extensions.
    """

    def enable(self, *extension_types: type[Extension] | MachineName) -> None:
        """
        Enable the given extensions.
        """
        for extension_type in extension_types:
            if extension_type not in self._configurations:
                self.append(PluginInstanceConfiguration(extension_type))


@final
class EntityTypeConfiguration(Configuration):
    """
    Configure a single entity type for a project.
    """

    def __init__(
        self,
        entity_type_id: MachineName | type[Entity],
        *,
        generate_html_list: bool = False,
    ):
        super().__init__()
        self._id = (
            entity_type_id
            if isinstance(entity_type_id, str)
            else entity_type_id.plugin_id()
        )
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

    async def validate(self, entity_type_repository: PluginRepository[Entity]) -> None:
        """
        Validate the configuration.
        """
        entity_type = await entity_type_repository.get(self.id)
        if self.generate_html_list and not issubclass(entity_type, UserFacing):
            raise AssertionFailed(
                _(
                    "Cannot generate pages for {entity_type}, because it is not a user-facing entity type."
                ).format(entity_type=entity_type.plugin_label())
            )


@final
class EntityTypeConfigurationMapping(
    PluginIdentifierKeyConfigurationMapping[Entity, EntityTypeConfiguration]
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
        configuration = EntityTypeConfiguration(Entity)
        configuration.load(dump)
        return configuration

    async def validate(self, entity_type_repository: PluginRepository[Entity]) -> None:
        """
        Validate the configuration.
        """
        with AssertionFailedGroup().assert_valid() as errors:
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
            raise AssertionFailed(_("Locale aliases must not contain slashes."))
        self._alias = alias

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, locale=self.locale, alias=self.alias)

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

    def __init__(
        self,
        configurations: Iterable[LocaleConfiguration] | None = None,
    ):
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


class CopyrightNoticeConfiguration(PluginConfiguration):
    """
    Configuration to define :py:class:`betty.copyright_notice.CopyrightNotice` plugins.
    """

    summary = RequiredStaticTranslationsLocalizableConfigurationAttr("summary")
    text = RequiredStaticTranslationsLocalizableConfigurationAttr("text")

    def __init__(
        self,
        plugin_id: MachineName,
        label: ShorthandStaticTranslations,
        *,
        summary: ShorthandStaticTranslations,
        text: ShorthandStaticTranslations,
        description: ShorthandStaticTranslations | None = None,
    ):
        super().__init__(plugin_id, label, description=description)
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
        del mapping["summary"]
        del mapping["text"]
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            **super().dump(),
            "summary": self.summary.dump(),
            "text": self.text.dump(),
        }


class CopyrightNoticeConfigurationMapping(
    PluginConfigurationMapping[CopyrightNotice, CopyrightNoticeConfiguration]
):
    """
    A configuration mapping for copyright notices.
    """

    @override
    def _new_plugin(
        self, configuration: CopyrightNoticeConfiguration
    ) -> type[CopyrightNotice]:
        class _ProjectConfigurationCopyrightNotice(
            ShorthandPluginBase, CopyrightNotice
        ):
            _plugin_id = configuration.id
            _plugin_label = configuration.label
            _plugin_description = configuration.description

            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return _ProjectConfigurationCopyrightNotice

    @override
    def _load_item(self, dump: Dump) -> CopyrightNoticeConfiguration:
        item = CopyrightNoticeConfiguration("-", "", summary="", text="")
        item.load(dump)
        return item

    @classmethod
    def _create_default_item(
        cls, configuration_key: str
    ) -> CopyrightNoticeConfiguration:
        return CopyrightNoticeConfiguration(configuration_key, {}, summary="", text="")


class LicenseConfiguration(PluginConfiguration):
    """
    Configuration to define :py:class:`betty.license.License` plugins.
    """

    summary = RequiredStaticTranslationsLocalizableConfigurationAttr("summary")
    text = RequiredStaticTranslationsLocalizableConfigurationAttr("text")

    def __init__(
        self,
        plugin_id: MachineName,
        label: ShorthandStaticTranslations,
        *,
        summary: ShorthandStaticTranslations,
        text: ShorthandStaticTranslations,
        description: ShorthandStaticTranslations | None = None,
    ):
        super().__init__(plugin_id, label, description=description)
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
        del mapping["summary"]
        del mapping["text"]
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            **super().dump(),
            "summary": self.summary.dump(),
            "text": self.text.dump(),
        }


class LicenseConfigurationMapping(
    PluginConfigurationMapping[License, LicenseConfiguration]
):
    """
    A configuration mapping for licenses.
    """

    @override
    def _new_plugin(self, configuration: LicenseConfiguration) -> type[License]:
        class _ProjectConfigurationLicense(ShorthandPluginBase, License):
            _plugin_id = configuration.id
            _plugin_label = configuration.label
            _plugin_description = configuration.description

            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return _ProjectConfigurationLicense

    @override
    def _load_item(self, dump: Dump) -> LicenseConfiguration:
        item = LicenseConfiguration("-", "", summary="", text="")
        item.load(dump)
        return item

    @classmethod
    def _create_default_item(cls, configuration_key: str) -> LicenseConfiguration:
        return LicenseConfiguration(configuration_key, {}, summary="", text="")


class EventTypeConfigurationMapping(
    PluginConfigurationPluginConfigurationMapping[EventType]
):
    """
    A configuration mapping for event types.
    """

    @override
    def _new_plugin(self, configuration: PluginConfiguration) -> type[EventType]:
        class _ProjectConfigurationEventType(ShorthandPluginBase, EventType):
            _plugin_id = configuration.id
            _plugin_label = configuration.label
            _plugin_description = configuration.description

        return _ProjectConfigurationEventType


class PlaceTypeConfigurationMapping(
    PluginConfigurationPluginConfigurationMapping[PlaceType]
):
    """
    A configuration mapping for place types.
    """

    @override
    def _new_plugin(self, configuration: PluginConfiguration) -> type[PlaceType]:
        class _ProjectConfigurationPlaceType(ShorthandPluginBase, PlaceType):
            _plugin_id = configuration.id
            _plugin_label = configuration.label
            _plugin_description = configuration.description

        return _ProjectConfigurationPlaceType


class PresenceRoleConfigurationMapping(
    PluginConfigurationPluginConfigurationMapping[PresenceRole]
):
    """
    A configuration mapping for presence roles.
    """

    @override
    def _new_plugin(self, configuration: PluginConfiguration) -> type[PresenceRole]:
        class _ProjectConfigurationPresenceRole(ShorthandPluginBase, PresenceRole):
            _plugin_id = configuration.id
            _plugin_label = configuration.label
            _plugin_description = configuration.description

        return _ProjectConfigurationPresenceRole


class GenderConfigurationMapping(PluginConfigurationPluginConfigurationMapping[Gender]):
    """
    A configuration mapping for genders.
    """

    @override
    def _new_plugin(self, configuration: PluginConfiguration) -> type[Gender]:
        class _ProjectConfigurationGender(ShorthandPluginBase, Gender):
            _plugin_id = configuration.id
            _plugin_label = configuration.label
            _plugin_description = configuration.description

        return _ProjectConfigurationGender


@final
class ProjectConfiguration(Configuration):
    """
    Provide the configuration for a :py:class:`betty.project.Project`.
    """

    title = OptionalStaticTranslationsLocalizableConfigurationAttr("title")
    author = OptionalStaticTranslationsLocalizableConfigurationAttr("author")
    #: The project-wide :py:class:`betty.copyright_notice.CopyrightNotice` plugin to use.
    copyright_notice: PluginInstanceConfiguration
    #: The project-wide :py:class:`betty.license.License` plugin to use.
    license: PluginInstanceConfiguration

    def __init__(
        self,
        configuration_file_path: Path,
        *,
        available_formats: Sequence[type[Format]],
        url: str = "https://example.com",
        clean_urls: bool = False,
        title: ShorthandStaticTranslations = "Betty",
        author: ShorthandStaticTranslations | None = None,
        entity_types: Iterable[EntityTypeConfiguration] | None = None,
        event_types: Iterable[PluginConfiguration] | None = None,
        place_types: Iterable[PluginConfiguration] | None = None,
        presence_roles: Iterable[PluginConfiguration] | None = None,
        copyright_notice: PluginInstanceConfiguration | None = None,  # noqa A002
        copyright_notices: Iterable[CopyrightNoticeConfiguration] | None = None,
        license: PluginInstanceConfiguration | None = None,  # noqa A002
        licenses: Iterable[LicenseConfiguration] | None = None,
        genders: Iterable[PluginConfiguration] | None = None,
        extensions: Iterable[PluginInstanceConfiguration] | None = None,
        debug: bool = False,
        locales: Iterable[LocaleConfiguration] | None = None,
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        name: MachineName | None = None,
        logo: Path | None = None,
    ):
        from betty.copyright_notice.copyright_notices import ProjectAuthor

        super().__init__()
        self._available_formats = available_formats
        self._configuration_file_path = configuration_file_path
        self._name = name
        self._computed_name: str | None = None
        self._url = url
        self._clean_urls = clean_urls
        self.title = title
        if author:
            self.author = author
        self._entity_types = EntityTypeConfigurationMapping(
            entity_types
            or [
                EntityTypeConfiguration(Person, generate_html_list=True),
                EntityTypeConfiguration(Event, generate_html_list=True),
                EntityTypeConfiguration(Place, generate_html_list=True),
                EntityTypeConfiguration(Source, generate_html_list=True),
            ]
        )
        self.copyright_notice = copyright_notice or PluginInstanceConfiguration(
            ProjectAuthor
        )
        self._copyright_notices = CopyrightNoticeConfigurationMapping()
        if copyright_notices is not None:
            self._copyright_notices.append(*copyright_notices)
        self.license = license or PluginInstanceConfiguration(AllRightsReserved)
        self._licenses = LicenseConfigurationMapping()
        if licenses is not None:
            self._licenses.append(*licenses)
        self._event_types = EventTypeConfigurationMapping()
        if event_types is not None:
            self._event_types.append(*event_types)
        self._place_types = PlaceTypeConfigurationMapping()
        if place_types is not None:
            self._place_types.append(*place_types)
        self._presence_roles = PresenceRoleConfigurationMapping()
        if presence_roles is not None:
            self._presence_roles.append(*presence_roles)
        self._genders = GenderConfigurationMapping()
        if genders is not None:
            self._genders.append(*genders)
        self._extensions = ExtensionInstanceConfigurationMapping(extensions or ())
        self._debug = debug
        self._locales = LocaleConfigurationMapping(locales or ())
        self._lifetime_threshold = lifetime_threshold
        self._logo = logo

    @classmethod
    async def new(
        cls,
        configuration_file_path: Path,
        *,
        url: str = "https://example.com",
        clean_urls: bool = False,
        title: ShorthandStaticTranslations = "Betty",
        author: ShorthandStaticTranslations | None = None,
        entity_types: Iterable[EntityTypeConfiguration] | None = None,
        event_types: Iterable[PluginConfiguration] | None = None,
        place_types: Iterable[PluginConfiguration] | None = None,
        presence_roles: Iterable[PluginConfiguration] | None = None,
        copyright_notice: PluginInstanceConfiguration | None = None,  # noqa A002
        copyright_notices: Iterable[CopyrightNoticeConfiguration] | None = None,
        license: PluginInstanceConfiguration | None = None,  # noqa A002
        licenses: Iterable[LicenseConfiguration] | None = None,
        genders: Iterable[PluginConfiguration] | None = None,
        extensions: Iterable[PluginInstanceConfiguration] | None = None,
        debug: bool = False,
        locales: Iterable[LocaleConfiguration] | None = None,
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        name: MachineName | None = None,
        logo: Path | None = None,
    ) -> Self:
        """
        Create a new instance.
        """
        return cls(
            configuration_file_path,
            available_formats=await FORMAT_REPOSITORY.select(),
            url=url,
            clean_urls=clean_urls,
            title=title,
            author=author,
            entity_types=entity_types,
            event_types=event_types,
            place_types=place_types,
            presence_roles=presence_roles,
            copyright_notice=copyright_notice,
            copyright_notices=copyright_notices,
            license=license,
            licenses=licenses,
            genders=genders,
            extensions=extensions,
            debug=debug,
            locales=locales,
            lifetime_threshold=lifetime_threshold,
            name=name,
            logo=logo,
        )

    @property
    def configuration_file_path(self) -> Path:
        """
        The path to the configuration's file.
        """
        return self._configuration_file_path

    @configuration_file_path.setter
    def configuration_file_path(self, configuration_file_path: Path) -> None:
        self.assert_mutable()
        if configuration_file_path == self._configuration_file_path:
            return
        format_for(self._available_formats, configuration_file_path.suffix)
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
            raise AssertionFailed(
                _("The URL must start with a scheme such as https:// or http://.")
            )
        if not url_parts.netloc:
            raise AssertionFailed(_("The URL must include a host."))
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
    ) -> PluginConfigurationMapping[CopyrightNotice, CopyrightNoticeConfiguration]:
        """
        The :py:class:`betty.copyright_notice.CopyrightNotice` plugins created by this project.
        """
        return self._copyright_notices

    @property
    def licenses(
        self,
    ) -> PluginConfigurationMapping[License, LicenseConfiguration]:
        """
        The :py:class:`betty.license.License` plugins created by this project.
        """
        return self._licenses

    @property
    def event_types(self) -> PluginConfigurationMapping[EventType, PluginConfiguration]:
        """
        The event type plugins created by this project.
        """
        return self._event_types

    @property
    def place_types(self) -> PluginConfigurationMapping[PlaceType, PluginConfiguration]:
        """
        The place type plugins created by this project.
        """
        return self._place_types

    @property
    def presence_roles(
        self,
    ) -> PluginConfigurationMapping[PresenceRole, PluginConfiguration]:
        """
        The presence role plugins created by this project.
        """
        return self._presence_roles

    @property
    def genders(
        self,
    ) -> PluginConfigurationMapping[Gender, PluginConfiguration]:
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
