"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.config.factory import ConfigurationDependentSelfFactory
from betty.locale.localizable.gettext import _
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.extension.gramps.config import GrampsConfiguration
from betty.project.extension.gramps.jobs import LoadAncestry
from betty.project.factory import (
    CallbackProjectDependentFactory,
    ProjectDependentSelfFactory,
)
from betty.project.load import Loader
from betty.typing import private

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project, ProjectContext
    from betty.service.level.factory import AnyFactoryTarget


@final
@ExtensionDefinition(
    "gramps",
    label="Gramps",
    description=_("Load Gramps family trees."),
)
class Gramps(
    Loader,
    ConfigurationDependentSelfFactory[GrampsConfiguration],
    ProjectDependentSelfFactory,
    Extension,
):
    """
    .. plugin:: extension:gramps.

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
    whose value is the ID of the :py:class:`gender plugin <betty.ancestry.gender.GenderDefinition>` you want to use.

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

    Presence roles
    --------------

    Betty supports the following Gramps presence roles without any additional configuration:

    .. list-table:: Presence roles
       :align: left
       :header-rows: 1

       * - Gramps role
         - Betty presence role
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

    @private
    def __init__(
        self, *, project: Project, configuration: GrampsConfiguration | None = None
    ):
        super().__init__(
            configuration=GrampsConfiguration()
            if configuration is None
            else configuration,
            project=project,
        )

    @override
    @classmethod
    def configuration_cls(cls) -> type[GrampsConfiguration]:
        return GrampsConfiguration

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: GrampsConfiguration
    ) -> AnyFactoryTarget[Self]:
        return CallbackProjectDependentFactory(
            lambda project: cls(configuration=configuration, project=project)
        )

    @override
    async def load(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(LoadAncestry())
