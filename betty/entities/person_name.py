"""
Data types to describe people's names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_citations import HasCitations
from betty.associations.to_one import ToOne, ToOneAssociate
from betty.attrs.locale import HasLocale
from betty.attrs.owner import OwnerAttr
from betty.datas.str import StrDefinition
from betty.entity import EntityDefinition
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy
from betty.privacy.resolve import merge_privacies
from betty.typing import Voidable, VoidableType, VoidType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.associations.to_many import ToManyAssociates
    from betty.entities.citation import Citation
    from betty.entities.person import Person
    from betty.linked_data import LinkedData
    from betty.locale import ResolvableLocale
    from betty.localizable import Localizable
    from betty.machine_name import ResolvableMachineName
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
class PersonName(HasLocale, HasCitations):
    """
    .. plugin:: entity:person-name.
    """

    # @todo For fields like these, can we somehow automatically set a linked data porter that uses
    # @todo the portable data porter internally, yet wraps everything in LinkedData with a context?
    # @todo
    # @todo
    affiliation = OwnerAttr(StrDefinition(label=_("Affiliation name"))).optional
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

    individual = OwnerAttr(StrDefinition(label=_("Individual name"))).optional
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

    person = ToOne[Self, "Person"](
        "betty.entities.person:Person",
        "names",
        label=_("Person"),
    )
    """
    The person whose name this is.
    """

    def __init__(
        self,
        *,
        id: ResolvableMachineName | None = None,  # noqa: A002
        person: ToOneAssociate[Self, Person],
        individual: str | None = None,
        affiliation: str | None = None,
        privacy: Privacy = Privacy.UNDETERMINED,
        locale: ResolvableLocale | None = None,
        citations: ToManyAssociates[Self, Citation] = (),
    ):
        super().__init__(
            id=id,
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
    @classmethod
    async def linked_data_schema_properties(
        cls, project: Project, /
    ) -> Mapping[str, VoidableType[PortableMapping]]:
        return {
            "individual": Voidable({
                "description": "The part of the name unique to this individual, such as a first name.",
                "title": "Individual name",
                "type": "string",
            }),
            "affiliation": Voidable({
                "description": "The part of the name shared with others, such as a surname.",
                "title": "Affiliation name",
                "type": "string",
            }),
        }

    @override
    async def dump_linked_data_properties(
        self, project: Project, /
    ) -> Mapping[str, LinkedData | VoidType]:
        if self.private:
            return {}
        data = {}
        contexts = {}
        if self.individual is not None:
            contexts["individual"] = "https://schema.org/givenName"
            data["individual"] = self.individual
        if self.affiliation is not None:
            contexts["affiliation"] = "https://schema.org/familyName"
            data["affiliation"] = self.affiliation
        return data
