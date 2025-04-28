"""
Data types describing persons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.gender.genders import Unknown as UnknownGender
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks, Link
from betty.functools import unique
from betty.json.linked_data import JsonLdObject, dump_context
from betty.locale.localizable import Localizable, _, ngettext
from betty.model import (
    Entity,
    ToManySchema,
    UserFacingEntity,
    persistent_id,
)
from betty.model.association import BidirectionalToMany, ToManyAssociates
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, MutableSequence

    from betty.ancestry.citation import Citation
    from betty.ancestry.file_reference import FileReference
    from betty.ancestry.gender import Gender
    from betty.ancestry.note import Note
    from betty.ancestry.person_name import PersonName
    from betty.ancestry.presence import Presence
    from betty.mutability import Mutable
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
class Person(
    ShorthandPluginBase,
    HasFileReferences,
    HasCitations,
    HasNotes,
    HasLinks,
    HasPrivacy,
    UserFacingEntity,
    Entity,
):
    """
    A person.
    """

    _plugin_id = "person"
    _plugin_label = _("Person")

    parents = BidirectionalToMany["Person", "Person"](
        "betty.ancestry.person:Person",
        "parents",
        "betty.ancestry.person:Person",
        "children",
        title="Parents",
    )
    children = BidirectionalToMany["Person", "Person"](
        "betty.ancestry.person:Person",
        "children",
        "betty.ancestry.person:Person",
        "parents",
        title="Children",
    )
    presences = BidirectionalToMany["Person", "Presence"](
        "betty.ancestry.person:Person",
        "presences",
        "betty.ancestry.presence:Presence",
        "person",
        title="Presences",
        description="This person's presences at events",
        linked_data_embedded=True,
    )
    names = BidirectionalToMany["Person", "PersonName"](
        "betty.ancestry.person:Person",
        "names",
        "betty.ancestry.person_name:PersonName",
        "person",
        title="Names",
        linked_data_embedded=True,
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        file_references: ToManyAssociates[FileReference] | None = None,
        citations: ToManyAssociates[Citation] | None = None,
        links: MutableSequence[Link] | None = None,
        notes: ToManyAssociates[Note] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
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
            public=public,
            private=private,
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

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("People")

    @override
    @classmethod
    def plugin_label_count(cls, count: int) -> Localizable:
        return ngettext("{count} person", "{count} people", count).format(
            count=str(count)
        )

    @override
    def get_mutable_instances(self) -> Iterable[Mutable]:
        return (
            *super().get_mutable_instances(),
            self.gender,
        )

    @property
    def gender(self) -> Gender:
        """
        The person's gender.
        """
        return self._gender

    @gender.setter
    def gender(self, gender: Gender) -> None:
        self.assert_mutable()
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
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        url_generator = await project.url_generator
        dump_context(
            dump,
            names="https://schema.org/name",
            parents="https://schema.org/parent",
            children="https://schema.org/child",
            siblings="https://schema.org/sibling",
        )
        dump["@type"] = "https://schema.org/Person"
        dump["siblings"] = [
            url_generator.generate(
                f"betty-static:///person/{quote(sibling.id)}/index.json"
            )
            for sibling in self.siblings
            if persistent_id(sibling)
        ]
        if self.public:
            dump["gender"] = self.gender.plugin_id()
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "gender", await project.gender_repository.plugin_id_schema, False
        )
        schema.add_property("siblings", ToManySchema(title="Siblings"))
        return schema
