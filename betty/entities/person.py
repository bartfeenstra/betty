"""
Data types describing persons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entity import EntityDefinition
from betty.entity.association import BidirectionalToManySingleType, ToManyAssociates
from betty.entity.has_citations import HasCitations
from betty.entity.has_file_references import HasFileReferences
from betty.entity.has_links import HasLinks
from betty.entity.has_notes import HasNotes
from betty.functools import unique
from betty.gender import GenderDefinition
from betty.genders.unknown import Unknown as UnknownGender
from betty.json_schemas.entity_association import ToManySchema
from betty.json_schemas.plugin_id import PluginIdSchema
from betty.linked_data import JsonLdObject, dump_context
from betty.locale.localizable.gettext import _, ngettext
from betty.media_types.json_ld import JSON_LD
from betty.privacy import Privacy

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.entities.citation import Citation
    from betty.entities.file_reference import FileReference
    from betty.entities.link import Link
    from betty.entities.note import Note
    from betty.entities.person_name import PersonName
    from betty.entities.presence import Presence
    from betty.gender import Gender
    from betty.locale.localizable import Localizable
    from betty.machine_name import ResolvableMachineName
    from betty.portable import PortableMapping
    from betty.project import Project


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

    parents = BidirectionalToManySingleType["Person", "Person"](
        "betty.entities.person:Person",
        "children",
        label=_("Parents"),
    )
    """
    The person's parents.
    """

    children = BidirectionalToManySingleType["Person", "Person"](
        "betty.entities.person:Person",
        "parents",
        label=_("Children"),
    )
    """
    The person's children.
    """

    presences = BidirectionalToManySingleType["Person", "Presence"](
        "betty.entities.presence:Presence",
        "person",
        label=_("Presences"),
        description=_("This person's presences at events"),
    )
    """
    The person's presences at events.
    """

    names = BidirectionalToManySingleType["Person", "PersonName"](
        "betty.entities.person_name:PersonName",
        "person",
        label=_("Names"),
    )
    """
    The person's names.
    """

    def __init__(
        self,
        id: ResolvableMachineName | None = None,  # noqa: A002
        *,
        files: ToManyAssociates[FileReference] = (),
        citations: ToManyAssociates[Citation] = (),
        links: ToManyAssociates[Link] = (),
        notes: ToManyAssociates[Note] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
        parents: ToManyAssociates[Person] = (),
        children: ToManyAssociates[Person] = (),
        presences: ToManyAssociates[Presence] = (),
        names: ToManyAssociates[PersonName] = (),
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
            url_generator.generate(sibling, media_type=JSON_LD)
            for sibling in self.siblings
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
