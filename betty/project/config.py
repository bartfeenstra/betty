"""
Provide project configuration.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from pathlib import Path
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
    assert_number,
    assert_or,
    assert_path,
    assert_record,
    assert_str,
)
from betty.config import Configuration, Sample, get_full_sample
from betty.config.collections.mapping import OrderedConfigurationMapping
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.data.indicator.selector import Key
from betty.exception import (
    HumanFacingException,
    HumanFacingExceptionGroup,
    reraise_with_indicator,
)
from betty.license import License, LicenseDefinition
from betty.locale import DEFAULT_LOCALE, LocaleLike, ensure_locale, to_language_tag
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.attr import (
    OptionalLocalizableAttr,
    RequiredLocalizableAttr,
)
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.serde import dump_localizable
from betty.locale.localizable.static import CountableStaticTranslations
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
    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.plugin.repository import PluginRepository
    from betty.portable import PortableData, PortableMapping
    from betty.project import Project
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
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.project.extension.raspberry_mint import RaspberryMint
        from betty.project.extension.raspberry_mint.config import (
            RaspberryMintConfiguration,
        )

        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([PluginInstanceConfiguration(RaspberryMint)]), label="Expanded"
        )
        yield Sample(
            cls(
                [
                    PluginInstanceConfiguration(
                        RaspberryMint,
                        get_full_sample(RaspberryMintConfiguration).configuration,
                    )
                ]
            ),
            label="Full",
            full=True,
        )


@final
class EntityTypeConfiguration(Configuration):
    """
    Configure a single entity type for a project.

    .. configuration:: betty.project.config:EntityTypeConfiguration
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
    def load(cls, portable: PortableData, /) -> Self:
        record = assert_record(
            RequiredField("entity_type", assert_machine_name()),
            OptionalField("generate_html_list", assert_bool),
        )(portable)
        return cls(
            record["entity_type"],
            generate_html_list=record.get("generate_html_list", False),
        )

    @override
    def dump(self) -> PortableMapping:
        return {
            "entity_type": self.id,
            "generate_html_list": self.generate_html_list,
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.id, self.generate_html_list) == (
            other.id,
            other.generate_html_list,
        )

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

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.ancestry.person import Person

        yield Sample(EntityTypeConfiguration(Person), label="Minimal", minimal=True)
        yield Sample(
            EntityTypeConfiguration(Person, generate_html_list=True),
            label="Full",
            full=True,
        )


@final
class EntityTypeConfigurationMapping(
    PluginIdentifierKeyConfigurationMapping[EntityDefinition, EntityTypeConfiguration]
):
    """
    Configure the entity types for a project.

    .. configuration:: betty.project.config:EntityTypeConfigurationMapping
    """

    @override
    def _get_key(self, configuration: EntityTypeConfiguration, /) -> MachineName:
        return configuration.id

    @override
    @classmethod
    def _load_key(
        cls, portable_item: PortableData, portable_key: str, /
    ) -> PortableData:
        assert isinstance(portable_item, Mapping)
        portable_item["entity_type"] = portable_key
        return portable_item

    @override
    def _dump_key(self, portable_item: PortableData, /) -> tuple[PortableData, str]:
        assert isinstance(portable_item, Mapping)
        return portable_item, cast(str, portable_item.pop("entity_type"))

    @override
    @classmethod
    def _item_cls(cls) -> type[EntityTypeConfiguration]:
        return EntityTypeConfiguration

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

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(EntityTypeConfiguration).configuration]),
            label="Full",
            full=True,
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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(Locale("nl", "NL")), label="Minimal", minimal=True)
        yield Sample(cls(Locale("nl", "NL"), alias="nl"), label="Full", full=True)


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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(LocaleConfiguration).configuration]),
            label="Full",
            full=True,
        )


class CopyrightNoticePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.copyright_notice.CopyrightNoticeDefinition`.

    .. configuration:: betty.project.config:CopyrightNoticePluginConfiguration
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
    def dump(self) -> PortableMapping:
        return {
            **super().dump(),
            "summary": dump_localizable(self.summary),
            "text": dump_localizable(self.text),
        }

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
            cls(
                id="my-first-copyright-notice",
                label="My First Copyright Notice",
                summary="My First Copyright Notice is my first copyright notice",
                text="My First Copyright Notice is my first copyright notice, all rights are reserved.",
            ),
            label="Default",
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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(CopyrightNoticePluginConfiguration).configuration]),
            label="Full",
            full=True,
        )


class LicensePluginConfiguration(HumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.license.LicenseDefinition`.

    .. configuration:: betty.project.config:LicensePluginConfiguration
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
    def dump(self) -> PortableMapping:
        return {
            **super().dump(),
            "summary": dump_localizable(self.summary),
            "text": dump_localizable(self.text),
        }

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
            cls(
                id="my-first-license",
                label="My First License",
                summary="My First License is my first license",
                text="My First License is my first license, and allows you o...",
            ),
            label="Default",
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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(LicensePluginConfiguration).configuration]),
            label="Full",
            full=True,
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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(EventTypePluginConfiguration).configuration]),
            label="Full",
            full=True,
        )


class PlaceTypePluginConfiguration(CountableHumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.place_type.PlaceTypeDefinition`.

    .. configuration:: betty.project.config:PlaceTypePluginConfiguration
    """

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(PlaceTypePluginConfiguration).configuration]),
            label="Full",
            full=True,
        )


class PresenceRolePluginConfiguration(
    CountableHumanFacingPluginDefinitionConfiguration
):
    """
    Configure a :py:class:`betty.ancestry.presence_role.PresenceRoleDefinition`.
    """

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(PresenceRolePluginConfiguration).configuration]),
            label="Full",
            full=True,
        )


class GenderPluginConfiguration(CountableHumanFacingPluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.ancestry.gender.GenderDefinition`.

    .. configuration:: betty.project.config:GenderPluginConfiguration
    """

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
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
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(GenderPluginConfiguration).configuration]),
            label="Full",
            full=True,
        )


@final
class ProjectConfiguration(Configuration):
    """
    Configuration for a :py:class:`betty.project.Project`.

    .. configuration:: betty.project.config:ProjectConfiguration

    ``url``
    -------
    :sup:`required`

    The absolute, public URL at which the site will be published.

    ``debug``
    ---------
    :sup:`optional`

    ``true`` to output more detailed logs and disable optimizations that make debugging harder. Defaults to ``false``.

    ``clean_urls``
    --------------
    :sup:`optional`

    A boolean indicating whether to use clean URLs, e.g. ``/path`` instead of ``/path/index.html``. Defaults to ``false``.

    ``title``
    ---------
    :sup:`optional`

    The project's human-readable title. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``name``
    --------
    :sup:`optional`

    The project's machine name.

    ``author``
    ----------
    :sup:`optional`

    The project's author and copyright holder. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``logo``
    --------
    :sup:`optional`

    The path to your site's logo file. Defaults to the Betty logo.

    ``lifetime_threshold``
    ----------------------
    :sup:`optional`

    The number of years people are expected to live at most, e.g. after which they're presumed to have died.
    :py:const:`Defaults to 123 years <betty.project.config.DEFAULT_LIFETIME_THRESHOLD>`.

    ``locales``
    -----------
    :sup:`optional`

    If no locales are specified, Betty defaults to US English (``en-US``).

    Read more about :doc:`translations </usage/translation>`.

    An array of locales, each of which is an object with the following keys:

    ``locales[].locale``
    ^^^^^^^^^^^^^^^^^^^^
    :sup:`required`

    An `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.

    ``locales[].alias``
    ^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    A shorthand alias to use instead of the full language tag, such as when rendering URLs.

    ``entity_types``
    ----------------
    :sup:`optional`

    Keys are entity type (plugin) IDs, and values are objects containing the following keys:

    ``entity_types{}.generate_html_list``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    Whether to generate the HTML page to list entities of this type. Defaults to ``false``.

    ``event_types``
    ---------------
    :sup:`optional`

    Keys are event type (plugin) IDs, and values are objects containing the following keys:

    ``event_types{}.label``
    ^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`required`

    The event type's human-readable label. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``event_types{}.description``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The event type's human-readable long description. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``event_types{}.comes_before``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    A collection of the IDs of other event types that this one comes before.

    ``event_types{}.comes_after``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    A collection of the IDs of other event types that this one comes after.

    ``genders``
    -----------
    :sup:`optional`

    Keys are gender (plugin) IDs, and values are objects containing the following keys:

    ``genders{}.label``
    ^^^^^^^^^^^^^^^^^^^
    :sup:`required`

    The gender's human-readable label. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``genders{}.description``
    ^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The gender's human-readable long description. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``place_types``
    ---------------
    :sup:`optional`

    Keys are place type (plugin) IDs, and values are objects containing the following keys:

    ``place_types{}.label``
    ^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`required`

    The place type's human-readable label. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``place_types{}.description``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The place type's human-readable long description. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``presence_roles``
    ------------------
    :sup:`optional`

    Keys are presence role (plugin) IDs, and values are objects containing the following keys:

    ``presence_roles{}.label``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`required`

    The presence role's human-readable label. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``presence_roles{}.description``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    The presence role's human-readable long description. This can be a string or :py:class:`multiple translations <betty.locale.localizable.static.StaticTranslations>`.

    ``extensions``
    --------------
    :sup:`optional`

    The :py:class:`extensions <betty.project.extension.ExtensionDefinition>` to enable. Keys are extension names, and values
    are objects containing the following keys, both of which may be omitted to quickly enable an extension using its default
    configuration:

    ``extensions{}.enabled``
    ^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    A boolean indicating whether the extension is enabled. Defaults to ``true``.

    ``extensions{}.configuration``
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    An object containing the extension's own configuration, if it provides any configuration options.
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
    title = RequiredLocalizableAttr("title")
    author = OptionalLocalizableAttr("author")

    def __init__(
        self,
        *,
        title: LocalizableLike,
        url: str,
        clean_urls: bool = False,
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
        super().__init__()
        self._name = name
        self._url = url
        self._clean_urls = clean_urls
        self.title = title
        self.author = author
        self._entity_types = (
            EntityTypeConfigurationMapping() if entity_types is None else entity_types
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

    def _default_copyright_notice(
        self,
    ) -> PluginInstanceConfiguration[CopyrightNoticeDefinition, CopyrightNotice]:
        from betty.copyright_notice.copyright_notices import ProjectAuthor

        return PluginInstanceConfiguration[CopyrightNoticeDefinition, CopyrightNotice](
            ProjectAuthor
        )

    def _default_license(
        self,
    ) -> PluginInstanceConfiguration[LicenseDefinition, License]:
        from betty.license.licenses import AllRightsReserved

        return PluginInstanceConfiguration[LicenseDefinition, License](
            AllRightsReserved
        )

    def _default_locales(self) -> LocaleConfigurationMapping:
        return LocaleConfigurationMapping()

    @override
    @property
    def validator(self) -> AnyFactoryTarget[None]:
        async def _validate(project: Project) -> None:
            with reraise_with_indicator(Key("entity_types")):
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
        self._name = assert_machine_name()(name)

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
        assert_number(minimum=1)(lifetime_threshold)
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
    def load(cls, portable: PortableData, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("name", assert_or(assert_str(), assert_none)),
                RequiredField("url", assert_str()),
                RequiredField("title", assert_load_localizable),
                OptionalField("author", assert_load_localizable),
                OptionalField("logo", assert_or(assert_path(), assert_none)),
                OptionalField("clean_urls", assert_bool),
                OptionalField("debug", assert_bool),
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
            )(portable)
        )

    @override
    def dump(self) -> PortableMapping:
        portable: PortableMapping = {
            "title": dump_localizable(self.title),
            "url": self.url,
        }
        if self.author is not None:
            portable["author"] = dump_localizable(self.author)
        if self.clean_urls:
            portable["clean_urls"] = self.clean_urls
        if self.copyright_notice != self._default_copyright_notice():
            portable["copyright_notice"] = self.copyright_notice.dump()
        if self.copyright_notices:
            portable["copyright_notices"] = self.copyright_notices.dump()
        if self.debug:
            portable["debug"] = self.debug
        if self.entity_types:
            portable["entity_types"] = self.entity_types.dump()
        if self.event_types:
            portable["event_types"] = self.event_types.dump()
        if self.extensions:
            portable["extensions"] = self.extensions.dump()
        if self.genders:
            portable["genders"] = self.genders.dump()
        if self.license != self._default_license():
            portable["license"] = self.license.dump()
        if self.licenses:
            portable["licenses"] = self.licenses.dump()
        if self.lifetime_threshold != DEFAULT_LIFETIME_THRESHOLD:
            portable["lifetime_threshold"] = self.lifetime_threshold
        if self.locales != self._default_locales():
            portable["locales"] = self.locales.dump()
        if self.logo:
            portable["logo"] = str(self.logo)
        if self.name is not None:
            portable["name"] = self.name
        if self.place_types:
            portable["place_types"] = self.place_types.dump()
        if self.presence_roles:
            portable["presence_roles"] = self.presence_roles.dump()
        return portable

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.title,
            self.url,
            self.author,
            self.clean_urls,
            self.copyright_notice,
            self.copyright_notices,
            self.debug,
            self.entity_types,
            self.event_types,
            self.extensions,
            self.genders,
            self.license,
            self.licenses,
            self.lifetime_threshold,
            self.locales,
            self.logo,
            self.name,
            self.place_types,
            self.presence_roles,
        ) == (
            other.title,
            other.url,
            other.author,
            other.clean_urls,
            other.copyright_notice,
            other.copyright_notices,
            other.debug,
            other.entity_types,
            other.event_types,
            other.extensions,
            other.genders,
            other.license,
            other.licenses,
            other.lifetime_threshold,
            other.locales,
            other.logo,
            other.name,
            other.place_types,
            other.presence_roles,
        )

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
            cls(title="Betty", url="https://example.com"), label="Minimal", minimal=True
        )
        yield Sample(
            cls(
                url="https://ancestry.example.com/betty",
                debug=True,
                clean_urls=True,
                title="Betty's ancestry",
                name="betty-ancestry",
                author="Bart Feenstra",
                logo=Path("my-ancestry-logo.png"),
                lifetime_threshold=123,
                locales=get_full_sample(LocaleConfigurationMapping).configuration,
                entity_types=get_full_sample(
                    EntityTypeConfigurationMapping
                ).configuration,
                event_types=get_full_sample(
                    EventTypePluginConfigurationMapping
                ).configuration,
                extensions=get_full_sample(
                    ExtensionInstanceConfigurationMapping
                ).configuration,
                genders=get_full_sample(GenderPluginConfigurationMapping).configuration,
                place_types=get_full_sample(
                    PlaceTypePluginConfigurationMapping
                ).configuration,
                presence_roles=get_full_sample(
                    PresenceRolePluginConfigurationMapping
                ).configuration,
            ),
            label="Full",
            full=True,
        )
