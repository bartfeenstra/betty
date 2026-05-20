"""
Data types to describe people's names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.attrs.attr import AttrAttr
from betty.attrs.locale import HasLocale
from betty.attrs.privacy import HasPrivacy
from betty.datas.str import StrDefinition
from betty.entity import Entity, EntityDefinition
from betty.entity.association import (
    BidirectionalToOne,
    ToManyAssociates,
    ToOneAssociate,
)
from betty.entity.has_citations import HasCitations
from betty.json_schema import String
from betty.linked_data import JsonLdObject, dump_context
from betty.locale.localizable.gettext import _, ngettext
from betty.privacy import Privacy
from betty.privacy.resolve import merge_privacies

if TYPE_CHECKING:
    from betty.locale import ResolvableLocale
    from betty.locale.localizable import Localizable
    from betty.plugins.entity.citation import Citation
    from betty.plugins.entity.person import Person
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "person-name",
    label=_("Person name"),
    label_plural=_("Person names"),
    label_countable=ngettext("{count} person name", "{count} person names"),
    public_facing=False,
)
class PersonName(HasLocale, HasCitations, HasPrivacy, Entity):
    """
    .. plugin:: entity:person-name.
    """

    affiliation = AttrAttr(StrDefinition(label=_("Affiliation name"))).optional
    """
    The name's affiliation, or family component.

    Also known as:

    - last name
    - surname
    """

    @affiliation.setter
    def affiliation(self, name: str | None, /) -> str | None:
        self._assert_names(self.individual, name)
        return name

    individual = AttrAttr(StrDefinition(label=_("Individual name"))).optional
    """
    The name's individual component.

    Also known as:

    - first name
    - given name
    """

    @individual.setter
    def individual(self, name: str | None, /) -> str | None:
        self._assert_names(name, self.affiliation)
        return name

    person = BidirectionalToOne["PersonName", "Person"](
        "betty.plugins.entity.person:Person",
        "names",
        label=_("Person"),
    )
    """
    The person whose name this is.
    """

    def __init__(
        self,
        *,
        person: ToOneAssociate[Person],
        id: str | None = None,  # noqa: A002
        individual: str | None = None,
        affiliation: str | None = None,
        privacy: Privacy = Privacy.UNDETERMINED,
        locale: ResolvableLocale | None = None,
        citations: ToManyAssociates[Citation] = (),
    ):
        super().__init__(
            id,
            privacy=privacy,
            locale=locale,
            citations=citations,
        )
        if individual is not None:
            self.individual = individual
        self.affiliation = affiliation
        # Set the person association last, because the association requires comparisons, and self.__eq__() uses the
        # individual and affiliation names.
        self.person = person

    def _assert_names(self, individual: str | None, affiliation: str | None) -> None:
        if individual is None:
            individual = self.individual
        if affiliation is None:
            affiliation = self.affiliation
        if not individual and not affiliation:
            raise ValueError(
                "The individual and affiliation names must not both be empty."
            )

    @override
    def _get_effective_privacy(self) -> Privacy:
        return merge_privacies(super()._get_effective_privacy(), self.person)

    @override
    @property
    def label(self) -> Localizable:
        return _("{individual_name} {affiliation_name}").format(
            individual_name="…" if not self.individual else self.individual,
            affiliation_name="…" if not self.affiliation else self.affiliation,
        )

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        if self.public:
            if self.individual is not None:
                dump_context(portable, individual="https://schema.org/givenName")
                portable["individual"] = self.individual
            if self.affiliation is not None:
                dump_context(portable, affiliation="https://schema.org/familyName")
                portable["affiliation"] = self.affiliation
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
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
