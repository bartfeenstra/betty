"""
Data types to describe people's names.
"""

from __future__ import annotations

from typing import final, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.has_citations import HasCitations
from betty.ancestry.locale import HasLocale
from betty.privacy import HasPrivacy, Privacy, merge_privacies
from betty.json.linked_data import dump_context
from betty.json.schema import Object, String
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import _, Localizable
from betty.model import Entity
from betty.model.association import BidirectionalToOne, ToOneResolver
from betty.plugin import ShorthandPluginBase
from betty.repr import repr_instance

if TYPE_CHECKING:
    from betty.project import Project
    from betty.serde.dump import DumpMapping, Dump
    from betty.ancestry.person import Person


@final
class PersonName(ShorthandPluginBase, HasLocale, HasCitations, HasPrivacy, Entity):
    """
    A name for a :py:class:`betty.ancestry.person.Person`.
    """

    _plugin_id = "person-name"
    _plugin_label = _("Person name")

    #: The person whose name this is.
    person = BidirectionalToOne["PersonName", "Person"](
        "betty.ancestry.person_name:PersonName",
        "person",
        "betty.ancestry.person:Person",
        "names",
    )

    def __init__(
        self,
        *,
        person: Person | ToOneResolver[Person],
        id: str | None = None,  # noqa A002
        individual: str | None = None,
        affiliation: str | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        locale: str = UNDETERMINED_LOCALE,
    ):
        if not individual and not affiliation:
            raise ValueError(
                "The individual and affiliation names must not both be empty."
            )
        super().__init__(
            id,
            privacy=privacy,
            public=public,
            private=private,
            locale=locale,
        )
        self._individual = individual
        self._affiliation = affiliation
        # Set the person association last, because the association requires comparisons, and self.__eq__() uses the
        # individual and affiliation names.
        self.person = person

    @override
    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.person:
            return merge_privacies(privacy, self.person.privacy)
        return privacy

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self, id=self.id, individual=self.individual, affiliation=self.affiliation
        )

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Person names")

    @property
    def individual(self) -> str | None:
        """
        The name's individual component.

        Also known as:

        - first name
        - given name
        """
        return self._individual

    @property
    def affiliation(self) -> str | None:
        """
        The name's affiliation, or family component.

        Also known as:

        - last name
        - surname
        """
        return self._affiliation

    @override
    @property
    def label(self) -> Localizable:
        return _("{individual_name} {affiliation_name}").format(
            individual_name="…" if not self.individual else self.individual,
            affiliation_name="…" if not self.affiliation else self.affiliation,
        )

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.public:
            if self.individual is not None:
                dump_context(dump, individual="https://schema.org/givenName")
                dump["individual"] = self.individual
            if self.affiliation is not None:
                dump_context(dump, affiliation="https://schema.org/familyName")
                dump["affiliation"] = self.affiliation
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "individual",
            String(
                title="Individual name",
                description="The part of the name unique to this individual, such as a first name.",
            ),
            False,
        )
        schema.add_property(
            "affiliation",
            String(
                title="Affiliation name",
                description="The part of the name shared with others, such as a surname.",
            ),
            False,
        )
        return schema
