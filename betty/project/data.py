"""
Project data.
"""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import TYPE_CHECKING, final

from betty.assertion import assert_number, assert_url
from betty.collection.keyed.adapter import MutableKeyedCollectionAdapter
from betty.collection.sequence.adapter import MutableResolvedSequenceAdapter
from betty.copyright_notice import (
    CopyrightNotice,
    CopyrightNoticeDefinition,
    CopyrightNoticeManufacturer,
)
from betty.copyright_notice.data import CopyrightNoticeDefinitionConfiguration
from betty.data import Data, Sample
from betty.data.aggregate.collection.keyed import KeyedCollectionDefinition
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.bool import BoolDefinition
from betty.data.int import IntDefinition
from betty.data.str import StrDefinition
from betty.dirs import BUILTIN_ASSET_DIRECTORY
from betty.entity import EntityDefinition
from betty.event_type import EventTypeDefinition
from betty.event_type.data import EventTypeDefinitionConfiguration
from betty.extension import Extension, ExtensionManufacturer
from betty.gender import GenderDefinition
from betty.gender.data import GenderDefinitionConfiguration
from betty.indicator.selector import Attr
from betty.license import License, LicenseDefinition, LicenseManufacturer
from betty.license.data import LicenseDefinitionConfiguration
from betty.load import (
    Enricher,
    EnricherDefinition,
    EnricherManufacturer,
    Loader,
    LoaderDefinition,
    LoaderManufacturer,
)
from betty.locale import DEFAULT_LOCALE, ResolvableLocale, resolve_locale
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName, ResolvableMachineName
from betty.pathlib.data import FilePathDefinition
from betty.place_type import PlaceTypeDefinition
from betty.place_type.data import PlaceTypeDefinitionConfiguration
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.project import DEFAULT_LIFETIME_THRESHOLD, ExtensionDefinition, ProjectLocale
from betty.properties.collection.keyed import KeyedCollectionProperty
from betty.properties.collection.sequence import SequenceProperty
from betty.properties.localizable import LocalizableProperty
from betty.properties.machine_name import MachineNameProperty
from betty.properties.plugin_definition_configurations import (
    PluginDefinitionConfigurationsProperty,
)
from betty.property import Optional, Property
from betty.role import RoleDefinition
from betty.role.data import RoleDefinitionConfiguration
from betty.sample import Size

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.locale.localizable import ResolvableLocalizable
    from betty.pathlib import StrPath
    from betty.plugin.factory import (
        ResolvablePluginManufacturer,
        ResolvablePluginManufacturerSequence,
    )


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
                copyright_notice=CopyrightNoticeManufacturer
                .data()
                .samples.get(Size.FULL)
                .subject,
                copyright_notices=[
                    CopyrightNoticeDefinitionConfiguration
                    .data()
                    .samples.get(Size.FULL)
                    .subject
                ],
                debug=True,
                generate_entity_list_html=["person", "place"],
                event_types=[
                    EventTypeDefinitionConfiguration
                    .data()
                    .samples.get(Size.FULL)
                    .subject
                ],
                genders=[
                    GenderDefinitionConfiguration.data().samples.get(Size.FULL).subject
                ],
                logo=BUILTIN_ASSET_DIRECTORY
                / "public"
                / "static"
                / "betty-512x512.png",
                license=LicenseManufacturer.data().samples.get(Size.FULL).subject,
                licenses=[
                    LicenseDefinitionConfiguration.data().samples.get(Size.FULL).subject
                ],
                lifetime_threshold=123,
                locales=[ProjectLocale.data().samples.get(Size.FULL).subject],
                name="betty-ancestry",
                place_types=[
                    PlaceTypeDefinitionConfiguration
                    .data()
                    .samples.get(Size.FULL)
                    .subject
                ],
                roles=[
                    RoleDefinitionConfiguration.data().samples.get(Size.FULL).subject
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

    .. data:: betty.project.data:ProjectConfiguration
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
    Whether to generate clean URLs.
    """

    copyright_notice = Optional(
        Property(
            CopyrightNoticeManufacturer,
            omit_load=True,
            omit_dump=lambda data: (
                data == ProjectConfiguration._default_copyright_notice()
            ),
            default=lambda: ProjectConfiguration._default_copyright_notice(),  # noqa: PLW0108
            resolver=CopyrightNoticeManufacturer.resolve,
        )
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
    """

    enrichers = KeyedCollectionProperty(
        KeyedCollectionDefinition(
            value=EnricherManufacturer,
            label=EnricherDefinition.type().label_plural,
            key=Attr("plugin_id"),
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

    event_types = PluginDefinitionConfigurationsProperty(
        EventTypeDefinition, EventTypeDefinitionConfiguration
    )
    """
    The :py:class:`betty.event_type.EventType` plugins created by this project.
    """

    extensions = KeyedCollectionProperty(
        KeyedCollectionDefinition(
            value=ExtensionManufacturer,
            label=ExtensionDefinition.type().label_plural,
            key=Attr("plugin_id"),
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
        SequenceProperty(
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

    genders = PluginDefinitionConfigurationsProperty(
        GenderDefinition, GenderDefinitionConfiguration
    )
    """
    The :py:class:`betty.gender.Gender` plugins created by this project.
    """

    license = Optional(
        Property(
            LicenseManufacturer,
            omit_load=True,
            omit_dump=lambda data: data == ProjectConfiguration._default_license(),
            default=lambda: ProjectConfiguration._default_license(),  # noqa: PLW0108
            resolver=LicenseManufacturer.resolve,
        )
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
    """

    loaders = KeyedCollectionProperty(
        KeyedCollectionDefinition(
            value=LoaderManufacturer,
            label=LoaderDefinition.type().label_plural,
            key=Attr("plugin_id"),
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

    locales = KeyedCollectionProperty(
        KeyedCollectionDefinition(
            value=ProjectLocale,
            label=_("Locales"),
            key=Attr("locale"),
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

    logo = Optional(Property(FilePathDefinition(), label=_("Logo")))
    """
    The project logo.
    """

    name = Optional(MachineNameProperty())
    """
    The project's machine name.
    """

    place_types = PluginDefinitionConfigurationsProperty(
        PlaceTypeDefinition, PlaceTypeDefinitionConfiguration
    )
    """
    The :py:class:`betty.place_type.PlaceType` plugins created by this project.
    """

    roles = PluginDefinitionConfigurationsProperty(
        RoleDefinition, RoleDefinitionConfiguration
    )
    """
    The :py:class:`betty.role.Role` plugins created by this project.
    """

    title = LocalizableProperty(label=_("Title"))
    """
    The human-readable project title.
    """

    url = Property(
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
        copyright_notices: Iterable[CopyrightNoticeDefinitionConfiguration] = (),
        debug: bool = False,
        enrichers: ResolvablePluginManufacturerSequence[
            EnricherDefinition, Enricher
        ] = (),
        event_types: Iterable[EventTypeDefinitionConfiguration] = (),
        extensions: ResolvablePluginManufacturerSequence[
            ExtensionDefinition, Extension
        ] = (),
        generate_entity_list_html: Iterable[ResolvablePluginId[EntityDefinition]]
        | None = None,
        genders: Iterable[GenderDefinitionConfiguration] = (),
        license: ResolvablePluginManufacturer[LicenseDefinition, License] | None = None,  # noqa: A002
        licenses: Iterable[LicenseDefinitionConfiguration] = (),
        lifetime_threshold: int = DEFAULT_LIFETIME_THRESHOLD,
        loaders: ResolvablePluginManufacturerSequence[LoaderDefinition, Loader] = (),
        locales: Iterable[ResolvableLocale | ProjectLocale] = (),
        logo: StrPath | None = None,
        name: ResolvableMachineName | None = None,
        place_types: Iterable[PlaceTypeDefinitionConfiguration] = (),
        roles: Iterable[RoleDefinitionConfiguration] = (),
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
