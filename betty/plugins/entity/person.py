"""
Data types describing persons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override
from urllib.parse import quote

from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_links import HasLinks
from betty.ancestry.has_notes import HasNotes
from betty.functools import unique
from betty.gender import GenderDefinition
from betty.json.linked_data import JsonLdObject, dump_context
from betty.locale.localizable.gettext import _, ngettext
from betty.model import EntityDefinition, persistent_id
from betty.model.association import BidirectionalToManySingleType, ToManyAssociates
from betty.model.schema import ToManySchema
from betty.plugin.schema import PluginIdSchema
from betty.plugins.gender import Unknown as UnknownGender
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence

    from betty.gender import Gender
    from betty.locale.localizable import Localizable
    from betty.plugins.entity.citation import Citation
    from betty.plugins.entity.file_reference import FileReference
    from betty.plugins.entity.link import Link
    from betty.plugins.entity.note import Note
    from betty.plugins.entity.person_name import PersonName
    from betty.plugins.entity.presence import Presence
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "person",
    label=_("Person"),
    label_plural=_("People"),
    label_countable=ngettext("{count} person", "{count} people"),
)
class Person(HasFileReferences, HasCitations, HasNotes, HasLinks, HasPrivacy):
    """
    .. plugin:: entity:person.
    """

    parents = BidirectionalToManySingleType["Person", "Person"](
        "betty.plugins.entity.person:Person",
        "children",
        label=_("Parents"),
    )
    """
    The person's parents.
    """

    children = BidirectionalToManySingleType["Person", "Person"](
        "betty.plugins.entity.person:Person",
        "parents",
        label=_("Children"),
    )
    """
    The person's children.
    """

    presences = BidirectionalToManySingleType["Person", "Presence"](
        "betty.plugins.entity.presence:Presence",
        "person",
        label=_("Presences"),
        description=_("This person's presences at events"),
        linked_data_embedded=True,
    )
    """
    The person's presences at events.
    """

    names = BidirectionalToManySingleType["Person", "PersonName"](
        "betty.plugins.entity.person_name:PersonName",
        "person",
        label=_("Names"),
        linked_data_embedded=True,
    )
    """
    The person's names.
    """

    def __init__(
        self,
        id: str | None = None,  # noqa: A002
        *,
        file_references: ToManyAssociates[FileReference] | None = None,
        citations: ToManyAssociates[Citation] | None = None,
        links: MutableSequence[Link] | None = None,
        notes: ToManyAssociates[Note] | None = None,
        privacy: Privacy | None = None,
        parents: ToManyAssociates[Person] | None = None,
        children: ToManyAssociates[Person] | None = None,
        presences: ToManyAssociates[Presence] | None = None,
        names: ToManyAssociates[PersonName] | None = None,
        gender: Gender | None = None,
    ):
        super().__init__(
            id,
            file_references=file_references,
            citations=citations,
            links=links,
            notes=notes,
            privacy=privacy,
        )
        if children is not None:
            self.children = children
        if parents is not None:
            self.parents = parents
        if presences is not None:
            self.presences = presences
        if names is not None:
            self.names = names
        self._gender = gender or UnknownGender()

    @property
    def gender(self) -> Gender:
        """
        The person's gender.
        """
        return self._gender

    @gender.setter
    def gender(self, gender: Gender) -> None:
        self._gender = gender

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
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        url_generator = await project.url_generator
        dump_context(
            portable,
            names="https://schema.org/name",
            parents="https://schema.org/parent",
            children="https://schema.org/child",
            siblings="https://schema.org/sibling",
        )
        portable["@type"] = "https://schema.org/Person"
        portable["siblings"] = [
            url_generator.generate(
                f"betty-static:///person/{quote(sibling.id)}/index.json"
            )
            for sibling in self.siblings
            if persistent_id(sibling)
        ]
        if self.public:
            portable["gender"] = self.gender.plugin().id
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "gender",
            PluginIdSchema(
                GenderDefinition.type(),
                [x async for x in project.plugins[GenderDefinition]],
            ),
            False,
        )
        schema.add_property("siblings", ToManySchema(title="Siblings"))
        return schema
