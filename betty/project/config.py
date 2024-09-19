"""
Provide project configuration.
"""

from __future__ import annotations

from reprlib import recursive_repr
from typing import final, Generic, Self, Iterable, Any, TYPE_CHECKING, TypeVar, cast
from urllib.parse import urlparse

from typing_extensions import override

from betty import model
from betty.ancestry import Event
from betty.ancestry.event_type import EventType
from betty.ancestry.gender import Gender
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.place_type import PlaceType
from betty.ancestry.presence_role import PresenceRole
from betty.ancestry.source import Source
from betty.assertion import (
    assert_record,
    RequiredField,
    assert_setattr,
    OptionalField,
    assert_str,
    assert_bool,
    Assertion,
    assert_fields,
    assert_locale,
    assert_positive_number,
    assert_int,
    assert_path,
    assert_mapping,
)
from betty.assertion.error import AssertionFailed
from betty.classtools import repr_instance
from betty.config import Configuration
from betty.config.collections.mapping import (
    ConfigurationMapping,
    OrderedConfigurationMapping,
)
from betty.config.collections.sequence import ConfigurationSequence
from betty.copyright import Copyright
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import _, ShorthandStaticTranslations, Localizable
from betty.locale.localizable.assertion import assert_static_translations
from betty.locale.localizable.config import (
    OptionalStaticTranslationsLocalizableConfigurationAttr,
    RequiredStaticTranslationsLocalizableConfigurationAttr,
)
from betty.machine_name import assert_machine_name
from betty.model import Entity, UserFacingEntity
from betty.plugin import ShorthandPluginBase
from betty.plugin.assertion import assert_plugin
from betty.plugin.config import (
    PluginConfigurationPluginConfigurationMapping,
    PluginConfiguration,
    PluginConfigurationMapping,
)
from betty.project import extension
from betty.project.extension import Extension, ConfigurableExtension
from betty.serde.dump import (
    Dump,
    minimize,
    DumpMapping,
)
from betty.serde.format import FormatRepository
from betty.typing import Void, Voidable, void_none

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from pathlib import Path


_EntityT = TypeVar("_EntityT", bound=Entity)


#: The default age by which people are presumed dead.
DEFAULT_LIFETIME_THRESHOLD = 125


@final
class EntityReference(Configuration, Generic[_EntityT]):
    """
    Configuration that references an entity from the project's ancestry.
    """

    def __init__(
        self,
        entity_type: type[_EntityT] | None = None,
        entity_id: str | None = None,
        *,
        entity_type_is_constrained: bool = False,
    ):
        super().__init__()
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._entity_type_is_constrained = entity_type_is_constrained

    @property
    def entity_type(self) -> type[_EntityT] | None:
        """
        The referenced entity's type.
        """
        return self._entity_type

    @entity_type.setter
    def entity_type(self, entity_type: type[_EntityT]) -> None:
        if self._entity_type_is_constrained:
            raise AttributeError(
                f"The entity type cannot be set, as it is already constrained to {self._entity_type}."
            )
        self._entity_type = entity_type

    @property
    def entity_id(self) -> str | None:
        """
        The referenced entity's ID.
        """
        return self._entity_id

    @entity_id.setter
    def entity_id(self, entity_id: str) -> None:
        self._entity_id = entity_id

    @entity_id.deleter
    def entity_id(self) -> None:
        self._entity_id = None

    @property
    def entity_type_is_constrained(self) -> bool:
        """
        Whether the entity type may be changed.
        """
        return self._entity_type_is_constrained

    @override
    def update(self, other: Self) -> None:
        self._entity_type = other._entity_type
        self._entity_type_is_constrained = other._entity_type_is_constrained
        self._entity_id = other._entity_id

    @override
    def load(
        self,
        dump: Dump,
    ) -> None:
        if isinstance(dump, dict) or not self.entity_type_is_constrained:
            assert_record(
                RequiredField(
                    "entity_type",
                    assert_plugin(model.ENTITY_TYPE_REPOSITORY)
                    | assert_setattr(self, "entity_type"),
                ),
                OptionalField(
                    "entity",
                    assert_str() | assert_setattr(self, "entity_id"),
                ),
            )(dump)
        else:
            assert_str()(dump)
            assert_setattr(self, "entity_id")(dump)

    @override
    def dump(self) -> Voidable[DumpMapping[Dump] | str]:
        if self.entity_type_is_constrained:
            return void_none(self.entity_id)

        entity_type = self.entity_type
        if entity_type is None or self.entity_id is None:
            return Void

        return minimize(
            {
                "entity_type": entity_type.plugin_id(),
                "entity": self._entity_id,
            }
        )


@final
class EntityReferenceSequence(
    Generic[_EntityT], ConfigurationSequence[EntityReference[_EntityT]]
):
    """
    Configuration for a sequence of references to entities from the project's ancestry.
    """

    def __init__(
        self,
        entity_references: Iterable[EntityReference[_EntityT]] | None = None,
        *,
        entity_type_constraint: type[_EntityT] | None = None,
    ):
        self._entity_type_constraint = entity_type_constraint
        super().__init__(entity_references)

    @override
    def load_item(self, dump: Dump) -> EntityReference[_EntityT]:
        configuration = EntityReference[_EntityT](
            # Use a dummy entity type for now to satisfy the initializer.
            # It will be overridden when loading the dump.
            Entity  # type: ignore[arg-type]
            if self._entity_type_constraint is None
            else self._entity_type_constraint,
            entity_type_is_constrained=self._entity_type_constraint is not None,
        )
        configuration.load(dump)
        return configuration

    @override
    def _pre_add(self, configuration: EntityReference[_EntityT]) -> None:
        super()._pre_add(configuration)

        entity_type_constraint = self._entity_type_constraint
        entity_reference_entity_type = configuration._entity_type

        if entity_type_constraint is None:
            configuration._entity_type_is_constrained = False
            return

        configuration._entity_type_is_constrained = True

        if (
            entity_reference_entity_type == entity_type_constraint
            and configuration.entity_type_is_constrained
        ):
            return

        expected_entity_type_label = entity_type_constraint.plugin_label()

        if entity_reference_entity_type is None:
            raise AssertionFailed(
                _(
                    "The entity reference must be for an entity of type {expected_entity_type_label}, but instead does not specify an entity type at all."
                ).format(
                    expected_entity_type_label=expected_entity_type_label,
                )
            )

        actual_entity_type_label = entity_type_constraint.plugin_label()

        raise AssertionFailed(
            _(
                "The entity reference must be for an entity of type {expected_entity_type_label}, but instead is for an entity of type {actual_entity_type_label}."
            ).format(
                expected_entity_type_label=expected_entity_type_label,
                actual_entity_type_label=actual_entity_type_label,
            )
        )


@final
class ExtensionConfiguration(Configuration):
    """
    Configure a single extension for a project.
    """

    def __init__(
        self,
        extension_type: type[Extension],
        *,
        enabled: bool = True,
        extension_configuration: Configuration | None = None,
    ):
        super().__init__()
        self._extension_type = extension_type
        self._enabled = enabled
        if extension_configuration is None and issubclass(
            extension_type, ConfigurableExtension
        ):
            extension_configuration = extension_type.default_configuration()
        self._set_extension_configuration(extension_configuration)

    @property
    def extension_type(self) -> type[Extension]:
        """
        The extension type.
        """
        return self._extension_type

    @property
    def enabled(self) -> bool:
        """
        Whether the extension is enabled.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def extension_configuration(self) -> Configuration | None:
        """
        Get the extension's own configuration.
        """
        return self._extension_configuration

    def _set_extension_configuration(
        self, extension_configuration: Configuration | None
    ) -> None:
        self._extension_configuration = extension_configuration

    @override
    def update(self, other: Self) -> None:
        self._extension_type = other._extension_type
        self._enabled = other._enabled
        self._set_extension_configuration(other._extension_configuration)

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField(
                "extension",
                assert_plugin(extension.EXTENSION_REPOSITORY)
                | assert_setattr(self, "_extension_type"),
            ),
            OptionalField("enabled", assert_bool() | assert_setattr(self, "enabled")),
            OptionalField(
                "configuration",
                self._assert_load_extension_configuration(self.extension_type),
            ),
        )(dump)

    def _assert_load_extension_configuration(
        self, extension_type: type[Extension]
    ) -> Assertion[Any, Configuration]:
        def _assertion(value: Any) -> Configuration:
            extension_configuration = self._extension_configuration
            if isinstance(extension_configuration, Configuration):
                extension_configuration.load(value)
                return extension_configuration
            raise AssertionFailed(
                _("{extension_type} is not configurable.").format(
                    extension_type=extension_type.plugin_id()
                )
            )

        return _assertion

    @override
    def dump(self) -> DumpMapping[Dump]:
        return minimize(
            {
                "extension": self.extension_type.plugin_id(),
                "enabled": self.enabled,
                "configuration": (
                    self.extension_configuration.dump()
                    if issubclass(self.extension_type, ConfigurableExtension)
                    and self.extension_configuration
                    else Void
                ),
            }
        )


@final
class ExtensionConfigurationMapping(
    ConfigurationMapping[type[Extension], ExtensionConfiguration]
):
    """
    Configure a project's extensions.
    """

    @override
    def _void_minimized_item_dump(self) -> bool:
        return True

    def __init__(
        self,
        configurations: Iterable[ExtensionConfiguration] | None = None,
    ):
        super().__init__(configurations)

    @override
    def load_item(self, dump: Dump) -> ExtensionConfiguration:
        fields_dump = assert_fields(
            RequiredField("extension", assert_plugin(extension.EXTENSION_REPOSITORY))
        )(dump)
        configuration = ExtensionConfiguration(fields_dump["extension"])
        configuration.load(dump)
        return configuration

    @override
    def _get_key(self, configuration: ExtensionConfiguration) -> type[Extension]:
        return configuration.extension_type

    @override
    def _load_key(self, item_dump: DumpMapping[Dump], key_dump: str) -> None:
        item_dump["extension"] = key_dump

    @override
    def _dump_key(self, item_dump: DumpMapping[Dump]) -> str:
        return cast(str, item_dump.pop("extension"))

    def enable(self, *extension_types: type[Extension]) -> None:
        """
        Enable the given extensions.
        """
        for extension_type in extension_types:
            try:
                self._configurations[extension_type].enabled = True
            except KeyError:
                self.append(ExtensionConfiguration(extension_type))


@final
class EntityTypeConfiguration(Configuration):
    """
    Configure a single entity type for a project.
    """

    def __init__(
        self,
        entity_type: type[Entity],
        *,
        generate_html_list: bool | None = None,
    ):
        super().__init__()
        self._entity_type = entity_type
        self.generate_html_list = generate_html_list  # type: ignore[assignment]

    @property
    def entity_type(self) -> type[Entity]:
        """
        The configured entity type.
        """
        return self._entity_type

    @property
    def generate_html_list(self) -> bool:
        """
        Whether to generate listing web pages for entities of this type.
        """
        return self._generate_html_list or False

    @generate_html_list.setter
    def generate_html_list(self, generate_html_list: bool | None) -> None:
        if generate_html_list and not issubclass(self._entity_type, UserFacingEntity):
            raise AssertionFailed(
                _(
                    "Cannot generate pages for {entity_type}, because it is not a user-facing entity type."
                ).format(entity_type=self._entity_type.plugin_label())
            )
        self._generate_html_list = generate_html_list

    @override
    def update(self, other: Self) -> None:
        self._entity_type = other._entity_type
        self._generate_html_list = other._generate_html_list

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField[Any, type[Entity]](
                "entity_type",
                assert_str()
                | assert_plugin(model.ENTITY_TYPE_REPOSITORY)
                | assert_setattr(self, "_entity_type"),
            ),
            OptionalField(
                "generate_html_list",
                assert_bool() | assert_setattr(self, "generate_html_list"),
            ),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return minimize(
            {
                "entity_type": self._entity_type.plugin_id(),
                "generate_html_list": (
                    Void
                    if self._generate_html_list is None
                    else self._generate_html_list
                ),
            }
        )


@final
class EntityTypeConfigurationMapping(
    ConfigurationMapping[type[Entity], EntityTypeConfiguration]
):
    """
    Configure the entity types for a project.
    """

    @override
    def _void_minimized_item_dump(self) -> bool:
        return True

    @override
    def _get_key(self, configuration: EntityTypeConfiguration) -> type[Entity]:
        return configuration.entity_type

    @override
    def _load_key(self, item_dump: DumpMapping[Dump], key_dump: str) -> None:
        assert_plugin(model.ENTITY_TYPE_REPOSITORY)(key_dump)
        item_dump["entity_type"] = key_dump

    @override
    def _dump_key(self, item_dump: DumpMapping[Dump]) -> str:
        return cast(str, item_dump.pop("entity_type"))

    @override
    def load_item(self, dump: Dump) -> EntityTypeConfiguration:
        # Use a dummy entity type for now to satisfy the initializer.
        # It will be overridden when loading the dump.
        configuration = EntityTypeConfiguration(
            Entity  # type: ignore[type-abstract]
        )
        configuration.load(dump)
        return configuration


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
    def update(self, other: Self) -> None:
        self._locale = other._locale
        self._alias = other._alias

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("locale", assert_locale() | assert_setattr(self, "_locale")),
            OptionalField("alias", assert_str() | assert_setattr(self, "alias")),
        )(dump)

    @override
    def dump(self) -> Voidable[Dump]:
        return minimize({"locale": self.locale, "alias": void_none(self._alias)})


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
    def update(self, other: Self) -> None:
        # Prevent the events from being dispatched.
        self._configurations.clear()
        self.append(*other.values())

    @override
    def replace(self, *configurations: LocaleConfiguration) -> None:
        # Prevent the events from being dispatched.
        self._configurations.clear()
        self.append(*configurations)
        self._ensure_locale()

    @override
    def load_item(self, dump: Dump) -> LocaleConfiguration:
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


class CopyrightConfiguration(PluginConfiguration):
    """
    Configuration to define :py:class:`betty.copyright.Copyright` plugins.
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
    def update(self, other: Self) -> None:
        super().update(self)
        self.summary.update(other.summary)
        self.text.update(other.text)

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
        return minimize(
            {**super().dump(), "summary": self.summary.dump(), "text": self.text.dump()}
        )


class CopyrightConfigurationMapping(
    PluginConfigurationMapping[Copyright, CopyrightConfiguration]
):
    """
    A configuration mapping for copyrights.
    """

    @override
    def _create_plugin(self, configuration: CopyrightConfiguration) -> type[Copyright]:
        class _ProjectConfigurationCopyright(ShorthandPluginBase, Copyright):
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

        return _ProjectConfigurationCopyright

    @override
    def load_item(self, dump: Dump) -> CopyrightConfiguration:
        item = CopyrightConfiguration("-", "", summary="", text="")
        item.load(dump)
        return item

    @classmethod
    def _create_default_item(cls, configuration_key: str) -> CopyrightConfiguration:
        return CopyrightConfiguration(configuration_key, {}, summary="", text="")


class EventTypeConfigurationMapping(
    PluginConfigurationPluginConfigurationMapping[EventType]
):
    """
    A configuration mapping for event types.
    """

    @override
    def _create_plugin(self, configuration: PluginConfiguration) -> type[EventType]:
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
    def _create_plugin(self, configuration: PluginConfiguration) -> type[PlaceType]:
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
    def _create_plugin(self, configuration: PluginConfiguration) -> type[PresenceRole]:
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
    def _create_plugin(self, configuration: PluginConfiguration) -> type[Gender]:
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
    #: The ID of the project-wide :py:class:`betty.copyright.Copyright` plugin to use.
    copyright: MachineName

    def __init__(
        self,
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
        copyright: MachineName | None = None,  # noqa A002
        copyrights: Iterable[CopyrightConfiguration] | None = None,
        genders: Iterable[PluginConfiguration] | None = None,
        extensions: Iterable[ExtensionConfiguration] | None = None,
        debug: bool = False,
        locales: Iterable[LocaleConfiguration] | None = None,
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        name: MachineName | None = None,
        logo: Path | None = None,
    ):
        from betty.copyright.copyrights import ProjectAuthor

        super().__init__()
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
                EntityTypeConfiguration(
                    entity_type=Person,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=Event,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=Place,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=Source,
                    generate_html_list=True,
                ),
            ]
        )
        self.copyright = copyright or ProjectAuthor.plugin_id()
        self._copyrights = CopyrightConfigurationMapping()
        if copyrights is not None:
            self._copyrights.append(*copyrights)
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
        self._extensions = ExtensionConfigurationMapping(extensions or ())
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

    @configuration_file_path.setter
    def configuration_file_path(self, configuration_file_path: Path) -> None:
        if configuration_file_path == self._configuration_file_path:
            return
        formats = FormatRepository()
        formats.format_for(configuration_file_path.suffix)
        self._configuration_file_path = configuration_file_path

    @property
    def name(self) -> MachineName | None:
        """
        The project's machine name.
        """
        return self._name

    @name.setter
    def name(self, name: MachineName) -> None:
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
    def extensions(self) -> ExtensionConfigurationMapping:
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
        self._logo = logo

    @property
    def copyrights(
        self,
    ) -> PluginConfigurationMapping[Copyright, CopyrightConfiguration]:
        """
        The :py:class:`betty.copyright.Copyright` plugins created by this project.
        """
        return self._copyrights

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
    def update(self, other: Self) -> None:
        self._url = other._url
        self.title.update(other.title)
        self.author.update(other.author)
        self.logo = other.logo
        self._clean_urls = other._clean_urls
        self._debug = other._debug
        self._lifetime_threshold = other._lifetime_threshold
        self._locales.update(other._locales)
        self._extensions.update(other._extensions)
        self._entity_types.update(other._entity_types)
        self._copyrights.update(other._copyrights)
        self._event_types.update(other._event_types)
        self._genders.update(other._genders)
        self._place_types.update(other._place_types)
        self._presence_roles.update(other._presence_roles)

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField("name", assert_str() | assert_setattr(self, "name")),
            RequiredField("url", assert_str() | assert_setattr(self, "url")),
            OptionalField("title", self.title.load),
            OptionalField("author", self.author.load),
            OptionalField("logo", assert_path() | assert_setattr(self, "logo")),
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
            OptionalField(
                "copyright", assert_machine_name() | assert_setattr(self, "copyright")
            ),
            OptionalField("copyrights", self.copyrights.load),
            OptionalField("event_types", self.event_types.load),
            OptionalField("genders", self.genders.load),
            OptionalField("place_types", self.place_types.load),
            OptionalField("presence_roles", self.presence_roles.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return minimize(
            {
                "name": void_none(self.name),
                "url": self.url,
                "title": self.title.dump(),
                "clean_urls": void_none(self.clean_urls),
                "author": self.author.dump(),
                "logo": str(self._logo) if self._logo else Void,
                "debug": void_none(self.debug),
                "lifetime_threshold": void_none(self.lifetime_threshold),
                "locales": self.locales.dump(),
                "extensions": self.extensions.dump(),
                "entity_types": self.entity_types.dump(),
                "copyright": self.copyright if self.copyright else Void,
                "copyrights": self.copyrights.dump(),
                "event_types": self.event_types.dump(),
                "genders": self.genders.dump(),
                "place_types": self.place_types.dump(),
                "presence_roles": self.presence_roles.dump(),
            }
        )
