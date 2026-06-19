"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Self, final, override

from betty.attrs.owner import CollectionOwnerAttr, OwnerAttr
from betty.attrs.path import new_path_attr
from betty.collection.mapping import MutableResolvedMapping
from betty.collection.mapping.adapter import MutableResolvedMappingAdapter
from betty.data import Data
from betty.datas.aggregate.collection.mapping import MappingDefinition
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.str import StrDefinition
from betty.event_type import EventType, EventTypeDefinition, EventTypeManufacturer
from betty.exception import HumanFacingException
from betty.factory import DataManufacturable, Manufacturable
from betty.gramps import (
    DEFAULT_EVENT_TYPE_MAPPING,
    DEFAULT_PLACE_TYPE_MAPPING,
    DEFAULT_ROLE_MAPPING,
    GrampsLoader,
)
from betty.jobs.load_gramps_ancestry import LoadGrampsAncestry
from betty.load import Loader, LoaderDefinition
from betty.locale.localizable.gettext import _
from betty.pathlib import resolve_path
from betty.place_type import PlaceType, PlaceTypeDefinition, PlaceTypeManufacturer
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, ResolvablePluginManufacturer
from betty.project import Project
from betty.prop import HasProps
from betty.role import Role, RoleDefinition, RoleManufacturer
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from betty.attr import Attr as Attr
    from betty.attrs.common import CommonAttr
    from betty.entity.collection.pool import EntityPool
    from betty.job.scheduler import Scheduler
    from betty.locale.localizable import ResolvableLocalizable
    from betty.pathlib import StrPath
    from betty.service_level import ServiceLevel
    from betty.user import User


def _new_plugin_mapping_attr[PluginDefinitionT: PluginClsDefinition, PluginT: Plugin](
    manufacturer: type[PluginManufacturer[PluginDefinitionT, PluginT]],
    gramps_label: ResolvableLocalizable,
    default: Mapping[str, ResolvablePluginManufacturer[PluginDefinitionT, PluginT]],
) -> CommonAttr[
    HasProps,
    MutableMapping[str, PluginManufacturer[PluginDefinitionT, PluginT]],
    Mapping[str, ResolvablePluginManufacturer[PluginDefinitionT, PluginT]],
]:
    return CollectionOwnerAttr[
        HasProps,
        MutableMapping[str, PluginManufacturer[PluginDefinitionT, PluginT]],
        Mapping[str, ResolvablePluginManufacturer[PluginDefinitionT, PluginT]],
        MappingDefinition,
    ](
        MappingDefinition(
            cls=MutableResolvedMapping,
            factory=lambda: MutableResolvedMappingAdapter[
                str,
                str,
                PluginManufacturer[PluginDefinitionT, PluginT],
                ResolvablePluginManufacturer[PluginDefinitionT, PluginT],
            ](
                {},
                value_resolver=manufacturer.resolve,
            ),
            key=StrDefinition(label=gramps_label),
            value=manufacturer,
            label=manufacturer.data().plugin_type.type().label_plural,
        ),
        omit_load=True,
    ).default(
        lambda: {key: manufacturer.resolve(value) for key, value in default.items()}
    )


@final
@ObjectDefinition(
    label=_("Family tree"),
    samples=[
        lambda: Sample(
            FamilyTree(name="my-gramps-family-tree"), label="Minimal", size=Size.MINIMAL
        )
    ],
)
class FamilyTree(Data, HasProps):
    """
    A Gramps family tree.

    .. data:: betty.loaders.gramps:FamilyTree
    """

    event_types = _new_plugin_mapping_attr(
        EventTypeManufacturer, _("Gramps event type"), DEFAULT_EVENT_TYPE_MAPPING
    )
    """
    How to map event types.
    """

    file = new_path_attr(label=_("File")).optional
    """
    The path to a Gramps family tree file.
    """

    name = OwnerAttr(StrDefinition(label=_("Name"))).optional
    """
    The family tree's name in Gramps.
    """

    place_types = _new_plugin_mapping_attr(
        PlaceTypeManufacturer, _("Gramps place type"), DEFAULT_PLACE_TYPE_MAPPING
    )
    """
    How to map place types.
    """

    roles = _new_plugin_mapping_attr(
        RoleManufacturer, _("Gramps role"), DEFAULT_ROLE_MAPPING
    )
    """
    How to map presence roles.
    """

    def __init__(
        self,
        file: StrPath | None = None,
        name: str | None = None,
        event_types: Mapping[
            str, ResolvablePluginManufacturer[EventTypeDefinition, EventType]
        ]
        | None = None,
        place_types: Mapping[
            str, ResolvablePluginManufacturer[PlaceTypeDefinition, PlaceType]
        ]
        | None = None,
        roles: Mapping[str, ResolvablePluginManufacturer[RoleDefinition, Role]]
        | None = None,
    ):
        super().__init__()
        if file is not None:
            self.file = resolve_path(file)
        self.name = name
        self.source  # noqa: B018
        if event_types is not None:
            self.event_types.update(event_types)  # ty:ignore[no-matching-overload]
        if place_types is not None:
            self.place_types.update(place_types)  # ty:ignore[no-matching-overload]
        if roles is not None:
            self.roles.update(roles)  # ty:ignore[no-matching-overload]

    @property
    def source(self) -> Path | str:
        """
        The family tree's source.

        This is either the name of a family tree in Gramps, or the path to a Gramps family tree file.
        """
        if self.file is not None:
            return self.file
        if self.name is not None:
            return self.name
        raise HumanFacingException(
            _('Family tree configuration must either have a "file" or a "name"')
        )


@final
@ObjectDefinition(
    label=_("Gramps configuration"),
    samples=[
        lambda: Sample(GrampsData(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            GrampsData(executable="gramps.exe"),
            label="A custom Gramps executable",
        ),
        lambda: Sample(
            GrampsData(family_trees=[FamilyTree(file="./gramps.gpkg")]),
            label="Load a family tree from a file",
        ),
        lambda: Sample(
            GrampsData(family_trees=[FamilyTree(name="my-family-tree")]),
            label="Load a family tree by its name directly from Gramps",
        ),
        lambda: Sample(
            GrampsData(
                family_trees=[
                    FamilyTree(
                        name="my-family-tree",
                        event_types={"GrampsEventType": "betty-event-type"},
                    ),
                ]
            ),
            label="Map a Gramps event type to a Betty event type",
        ),
        lambda: Sample(
            GrampsData(
                family_trees=[
                    FamilyTree(
                        name="my-family-tree",
                        place_types={"GrampsPlaceType": "betty-place-type"},
                    ),
                ]
            ),
            label="Map a Gramps place type to a Betty place type",
        ),
        lambda: Sample(
            GrampsData(
                family_trees=[
                    FamilyTree(
                        name="my-family-tree",
                        event_types={"GrampsRole": "betty-role"},
                    ),
                ]
            ),
            label="Map a Gramps role to a Betty role",
        ),
    ],
)
class GrampsData(Data, HasProps):
    """
    Configuration for the :py:class:`betty.loaders.gramps.Gramps` extension.

    .. data:: betty.loaders.gramps:GrampsData
    """

    family_trees = CollectionOwnerAttr(
        SequenceDefinition(cls=list, value=FamilyTree, label=_("Family trees")),
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    """
    The Gramps family trees to load.
    """

    executable = new_path_attr(label=_("Executable")).optional
    """
    The path to a specific Gramps executable.

    Leave ``None`` to use Gramps from the PATH.
    """

    def __init__(
        self,
        *,
        family_trees: Iterable[FamilyTree] = (),
        executable: StrPath | None = None,
    ):
        super().__init__()
        self.family_trees = family_trees
        self.executable = None if executable is None else resolve_path(executable)


@final
@LoaderDefinition(
    "gramps",
    label="Gramps",
    description=_("Load Gramps family trees."),
)
class Gramps(DataManufacturable[GrampsData], Manufacturable, Loader):
    """
    .. plugin:: loader:gramps.

    Attributes
    ----------
    Gramps allows arbitrary attributes to be added to some of its data types. Betty can parse these to load additional
    information. Each of Betty's Gramps attributes follows the same structure: ``betty:...`` (to load the attribute for any
    Betty project) or ``betty-MyProject:..`` (to load an attribute for the Betty project with machine name ``MyProject``),
    where ``...`` is the name that identifies the attribute's meaning. For the 'privacy` attribute, the Gramps attribute's full
    name would be ``betty:privacy`` or ``betty-MyProject:privacy``.

    Privacy
    ^^^^^^^

    Gramps has limited built-in support for people's privacy. To fully control privacy for people, as well as events, files,
    sources, and citations, add a ``betty:privacy`` attribute to any of these types, with a value of ``private`` to explicitly
    declare the data always private or ``public`` to declare the data always public. Any other value will leave the privacy
    undecided, as well as person records marked public using Gramps' built-in privacy selector. In such cases, the
    ``privatizer`` extension may decide if the data is public or private.

    Gender
    ^^^^^^
    To set a person's gender to a gender that is available in Betty, but not in Gramps, add a ``betty:gender`` attribute,
    whose value is the ID of the :py:class:`gender plugin <betty.gender.GenderDefinition>` you want to use.

    Event names
    ^^^^^^^^^^^
    Event names can be set using ``betty:name``. Values are :ref:`static translations <gramps-attributes-static-translations>`.

    Links
    ^^^^^

    Gramps has limited built-in support to add links to entities. For those Gramps entities that support attributes,
    you may add links using those:

    .. list-table:: Link attributes
       :header-rows: 1

       * - Name
         - Required/optional
         - Description
       * - ``betty:link-LINKNAME:url``
         - **required**
         - The URL the link targets. This may contain :ref:`static translations <gramps-attributes-static-translations>`.
       * - ``betty:link-LINKNAME:description``
         - optional
         - A human-friendly longer link description. This may contain :ref:`static translations <gramps-attributes-static-translations>`.
       * - ``betty:link-LINKNAME:label``
         - optional
         - A human-friendly short link label. This may contain :ref:`static translations <gramps-attributes-static-translations>`.
       * - ``betty:link-LINKNAME:media_type``
         - optional
         - An `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
       * - ``betty:link-LINKNAME:relationship``
         - optional
         - An `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.

    Where ``LINKNAME`` may be any value of your choosing, but must be unique per link. For example, where ``LINKNAME`` is ``cheese``:

    .. list-table::

       * - ``betty:link-cheese:url``
         - ``https://en.wikipedia.org/wiki/Cheese``
       * - ``betty:link-cheese:label``
         - ``Learn about cheese``
       * - ``betty:link-cheese:description``
         - ``Read the Wikipedia article about cheese``

    .. _gramps-attributes-static-translations:

    Static translations
    ^^^^^^^^^^^^^^^^^^^
    Static translations are not attributes on their own per se, but they are used by other attributes, such as links.

    If another attribute defines itself as containing static translations, that means you may add multiple variants of the
    attribute, each with a translation for a different locale.

    For example, given a translatable attribute called ``betty:my-text``, you may add an actual attribute ``betty:my-text``
    with any translation for a locale which Betty will consider *undetermined*. You may also add any number of
    ``betty:my-text:LOCALE`` attributes, where ``LOCALE`` is an `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language
    tag, and the value is the translation for that specific locale/language.

    Dates
    -----

    For unknown date parts, set those to all zeroes and Betty will ignore them. For instance, ``0000-12-31`` will be parsed as
    "December 31", and ``1970-01-00`` as "January, 1970".

    Event types
    -----------

    Betty supports the following Gramps event types without any additional configuration:

    .. list-table:: Event types
       :align: left
       :header-rows: 1

       * - Gramps event type
         - Betty event type
       * - ``Adopted``
         - ``adoption``
       * - ``Adult Christening``
         - ``baptism``
       * - ``Baptism``
         - ``baptism``
       * - ``Bar Mitzvah``
         - ``bar-mitzvah``
       * - ``Bat Mitzvah``
         - ``bat-mitzvah``
       * - ``Birth``
         - ``birth``
       * - ``Burial``
         - ``burial``
       * - ``Christening``
         - ``baptism``
       * - ``Confirmation``
         - ``confirmation``
       * - ``Cremation``
         - ``cremation``
       * - ``Death``
         - ``death``
       * - ``Divorce``
         - ``divorce``
       * - ``Divorce Filing``
         - ``divorce-announcement``
       * - ``Emigration``
         - ``emigration``
       * - ``Engagement``
         - ``engagement``
       * - ``Immigration``
         - ``immigration``
       * - ``Marriage``
         - ``marriage``
       * - ``Marriage Banns``
         - ``marriage-announcement``
       * - ``Occupation``
         - ``occupation``
       * - ``Residence``
         - ``residence``
       * - ``Retirement``
         - ``retirement``
       * - ``Will``
         - ``will``

    Genders
    -------

    Betty maps Gramps genders as follows:

    .. list-table:: Genders
       :align: left
       :header-rows: 1

       * - Gramps gender
         - Betty gender
       * - ``F``
         - ``woman``
       * - ``M``
         - ``man``
       * - ``U``
         - ``unknown``
       * - ``X``
         - ``non-binary``

    Place types
    -----------

    Betty supports the following Gramps place types without any additional configuration:

    .. list-table:: Place types
       :align: left
       :header-rows: 1

       * - Gramps place type
         - Betty place type
       * - ``Borough``
         - ``borough``
       * - ``Building``
         - ``building``
       * - ``City``
         - ``city``
       * - ``Country``
         - ``country``
       * - ``County``
         - ``county``
       * - ``Department``
         - ``department``
       * - ``District``
         - ``district``
       * - ``Farm``
         - ``farm``
       * - ``Hamlet``
         - ``hamlet``
       * - ``Locality``
         - ``locality``
       * - ``Municipality``
         - ``municipality``
       * - ``Neighborhood``
         - ``neighborhood``
       * - ``Number``
         - ``number``
       * - ``Parish``
         - ``parish``
       * - ``Province``
         - ``province``
       * - ``Region``
         - ``region``
       * - ``State``
         - ``state``
       * - ``Street``
         - ``street``
       * - ``Town``
         - ``town``
       * - ``Unknown``
         - ``Unknown``
       * - ``Village``
         - ``village``

    Roles
    -----

    Betty supports the following Gramps roles without any additional configuration:

    .. list-table:: Roles
       :align: left
       :header-rows: 1

       * - Gramps role
         - Betty role
       * - ``Aide``
         - ``attendee``
       * - ``Bride``
         - ``subject``
       * - ``Celebrant``
         - ``celebrant``
       * - ``Clergy``
         - ``celebrant``
       * - ``Family``
         - ``subject``
       * - ``Groom``
         - ``subject``
       * - ``Informant``
         - ``informant``
       * - ``Primary``
         - ``subject``
       * - ``Unknown``
         - ``unknown``
       * - ``Witness``
         - ``witness``

    Order & priority
    ----------------

    The order of lists of data, or the priority of individual bits of data, can be automatically determined by Betty in
    multiple different ways, such as by matching dates, or locales. When not enough details are available, or in case of
    ambiguity, the original order is preserved. If only a single item must be retrieved from the list, this will be the
    first item, optionally after sorting.

    For example, if a place has multiple names (which may be historical or translations), Betty may try to
    filter names by the given locale and date, and then indiscriminately pick the first one of the remaining names to
    display as the canonical name.

    Tips:

    - If you want one item to have priority over another, it should come before the other in a list (e.g. be higher up).
    - Items with more specific or complete data, such as locales or dates, should come before items with less specific or
      complete data. However, items without dates at all are considered current and not historical.
    - Unofficial names or nicknames, should generally be put at the end of lists.

    """

    def __init__(
        self,
        *,
        ancestry: EntityPool,
        services: ServiceLevel,
        user: User,
        attribute_prefix_key: str | None = None,
        executable: StrPath | None = None,
        family_trees: Iterable[FamilyTree] = (),
    ):
        super().__init__()
        self._services = services
        self._ancestry = ancestry
        self._attribute_prefix_key = attribute_prefix_key
        self._executable = executable
        self._family_trees = tuple(family_trees)
        self._user = user

    @override
    @classmethod
    def new_data_cls(cls) -> type[GrampsData]:
        return GrampsData

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: GrampsData | None = None, /) -> Self:
        return cls(
            ancestry=project.ancestry,
            executable=None if data is None else data.executable,
            family_trees=() if data is None else data.family_trees,
            services=project,
            user=project.upstream.user,
        )

    @override
    async def load(self, scheduler: Scheduler, /) -> None:
        for family_tree in self._family_trees:
            await scheduler.add(
                LoadGrampsAncestry(
                    loader=GrampsLoader(
                        self._ancestry,
                        services=self._services,
                        attribute_prefix_key=self._attribute_prefix_key,
                        user=self._user,
                        event_type_mapping=family_tree.event_types,
                        place_type_mapping=family_tree.place_types,
                        role_mapping=family_tree.roles,
                        executable=self._executable,
                    ),
                    source=family_tree.source,
                )
            )
