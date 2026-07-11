"""
Data types describing persons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_citations import HasCitations
from betty.associations.has_file_references import HasFileReferences
from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.associations.to_many import ToMany, ToManyAssociates
from betty.entities.person_name import PersonName
from betty.entities.presence import Presence
from betty.entity import EntityDefinition
from betty.functools import unique
from betty.gender import GenderDefinition
from betty.genders.unknown import UnknownGender
from betty.json_schemas.plugin_id import new_plugin_id_schema
from betty.linked_data import LinkedData
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy
from betty.typing import Voidable, VoidableType

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from betty.entities.citation import Citation
    from betty.entities.file_reference import FileReference
    from betty.entities.link import Link
    from betty.entities.note import Note
    from betty.gender import Gender
    from betty.localizable import Localizable
    from betty.machine_name import ResolvableMachineName
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidType


@final
@EntityDefinition(
    "person",
    label=_("Person"),
    label_plural=_("People"),
    label_countable=ngettext("{count} person", "{count} people"),
)
class Person(HasFileReferences, HasCitations, HasNotes, HasLinks):
    """
    .. plugin:: entity:person.
    """

    parents = ToMany[Self, "Person"](
        "betty.entities.person:Person",
        "children",
        label=_("Parents"),
    )
    """
    The person's parents.
    """

    children = ToMany[Self, "Person"](
        "betty.entities.person:Person",
        "parents",
        label=_("Children"),
    )
    """
    The person's children.
    """

    presences = ToMany[Self, Presence](
        Presence,
        "person",
        label=_("Presences"),
        description=_("This person's presences at events"),
    )
    """
    The person's presences at events.
    """

    names = ToMany[Self, PersonName](PersonName, "person", label=_("Names"))
    """
    The person's names.

    The first name is considered the :py:attr:`person label <betty.entities.person.Person.label>`.
    """

    def __init__(
        self,
        id: ResolvableMachineName | None = None,  # noqa: A002
        *,
        files: ToManyAssociates[Self, FileReference] = (),
        citations: ToManyAssociates[Self, Citation] = (),
        links: ToManyAssociates[Self, Link] = (),
        notes: ToManyAssociates[Self, Note] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
        parents: ToManyAssociates[Self, Person] = (),
        children: ToManyAssociates[Self, Person] = (),
        presences: ToManyAssociates[Self, Presence] = (),
        names: ToManyAssociates[Self, PersonName] = (),
        gender: Gender | None = None,
    ):
        super().__init__(
            id=id,
            files=files,
            citations=citations,
            links=links,
            notes=notes,
            privacy=privacy,
        )
        self.children = children
        self.parents = parents
        self.presences = presences
        self.names = names
        self.gender = gender or UnknownGender()
        """
        The person's gender.
        """

    @property
    def ancestors(self) -> Iterator[Person]:
        """
        All ancestors.
        """
        for parent in self.parents:
            yield parent
            yield from parent.ancestors

    @property
    def siblings(self) -> Iterator[Person]:
        """
        All siblings.
        """
        yield from unique(
            sibling
            for parent in self.parents
            for sibling in parent.children
            if sibling != self
        )

    @property
    def descendants(self) -> Iterator[Person]:
        """
        All descendants.
        """
        for child in self.children:
            yield child
            yield from child.descendants

    @override
    @property
    def label(self) -> Localizable:
        for name in self.names:
            if name.public:
                return name.label
        return super().label

    @override
    @classmethod
    async def linked_data_schema_properties(
        cls, project: Project, /
    ) -> Mapping[str, VoidableType[PortableMapping]]:
        return {
            "gender": Voidable(
                new_plugin_id_schema(
                    GenderDefinition.type(),
                    [x async for x in project.plugins[GenderDefinition]],
                )
            ),
        }

    @override
    async def dump_linked_data_properties(
        self, project: Project, /
    ) -> Mapping[str, LinkedData | VoidType]:
        dump = {}
        if self.public:
            dump["gender"] = LinkedData(self.gender.plugin().id)
        return dump
