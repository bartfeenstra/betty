"""
Data types describing persons.
"""

from __future__ import annotations

from typing import final, Iterable, MutableSequence, Iterator, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.gender.genders import Unknown as UnknownGender
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.person_name import PersonName
from betty.ancestry.presence_role import PresenceRoleSchema
from betty.privacy import HasPrivacy, Privacy
from betty.functools import Uniquifier
from betty.json.linked_data import dump_context, JsonLdObject
from betty.json.schema import Object, Array, Enum
from betty.locale.localizable import _, Localizable
from betty.model import (
    UserFacingEntity,
    Entity,
    GeneratedEntityId,
    EntityReferenceCollectionSchema,
    EntityReferenceSchema,
)
from betty.model.association import ToManyResolver, BidirectionalToMany
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.ancestry.note import Note
    from betty.ancestry.file_reference import FileReference
    from betty.ancestry.citation import Citation
    from betty.ancestry.presence import Presence
    from betty.ancestry.gender import Gender
    from betty.project import Project
    from betty.serde.dump import DumpMapping, Dump


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
    )
    children = BidirectionalToMany["Person", "Person"](
        "betty.ancestry.person:Person",
        "children",
        "betty.ancestry.person:Person",
        "parents",
    )
    presences = BidirectionalToMany["Person", "Presence"](
        "betty.ancestry.person:Person",
        "presences",
        "betty.ancestry.presence:Presence",
        "person",
    )
    names = BidirectionalToMany["Person", "PersonName"](
        "betty.ancestry.person:Person",
        "names",
        "betty.ancestry.person_name:PersonName",
        "person",
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        file_references: Iterable[FileReference]
        | ToManyResolver[FileReference]
        | None = None,
        citations: Iterable["Citation"] | ToManyResolver["Citation"] | None = None,
        links: MutableSequence[Link] | None = None,
        notes: Iterable[Note] | ToManyResolver[Note] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        parents: Iterable[Person] | ToManyResolver[Person] | None = None,
        children: Iterable[Person] | ToManyResolver[Person] | None = None,
        presences: Iterable["Presence"] | ToManyResolver["Presence"] | None = None,
        names: Iterable["PersonName"] | ToManyResolver["PersonName"] | None = None,
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
        self.gender = gender or UnknownGender()

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("People")

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
        yield from Uniquifier(
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
        dump_context(
            dump,
            names="https://schema.org/name",
            parents="https://schema.org/parent",
            children="https://schema.org/child",
            siblings="https://schema.org/sibling",
        )
        dump["@type"] = "https://schema.org/Person"
        dump["parents"] = [
            project.static_url_generator.generate(
                f"/person/{quote(parent.id)}/index.json"
            )
            for parent in self.parents
            if not isinstance(parent.id, GeneratedEntityId)
        ]
        dump["children"] = [
            project.static_url_generator.generate(
                f"/person/{quote(child.id)}/index.json"
            )
            for child in self.children
            if not isinstance(child.id, GeneratedEntityId)
        ]
        dump["siblings"] = [
            project.static_url_generator.generate(
                f"/person/{quote(sibling.id)}/index.json"
            )
            for sibling in self.siblings
            if not isinstance(sibling.id, GeneratedEntityId)
        ]
        dump["presences"] = [
            self._dump_person_presence(presence, project)
            for presence in self.presences
            if not isinstance(presence.event.id, GeneratedEntityId)
        ]
        if self.public:
            dump["names"] = [
                await name.dump_linked_data(project)
                for name in self.names
                if name.public
            ]
            dump["gender"] = self.gender.plugin_id()
        else:
            dump["names"] = []
        return dump

    def _dump_person_presence(
        self, presence: "Presence", project: Project
    ) -> DumpMapping[Dump]:
        assert presence.event
        dump: DumpMapping[Dump] = {
            "event": project.static_url_generator.generate(
                f"/event/{quote(presence.event.id)}/index.json"
            ),
        }
        dump_context(dump, event="https://schema.org/performerIn")
        if presence.public:
            dump["role"] = presence.role.plugin_id()
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "names",
            Array(await PersonName.linked_data_schema(project), title="Names"),
        )
        schema.add_property(
            "gender",
            Enum(
                *[gender.plugin_id() async for gender in project.genders],
                title="Gender",
            ),
            property_required=False,
        )
        schema.add_property("parents", EntityReferenceCollectionSchema(Person))
        schema.add_property("children", EntityReferenceCollectionSchema(Person))
        schema.add_property("siblings", EntityReferenceCollectionSchema(Person))
        schema.add_property(
            "presences", Array(_PersonPresenceSchema(), title="Presences")
        )
        return schema


class _PersonPresenceSchema(JsonLdObject):
    """
    A schema for the :py:class:`betty.ancestry.presence.Presence` associations on a :py:class:`betty.ancestry.person.Person`.
    """

    def __init__(self):
        from betty.ancestry.event import Event

        super().__init__(title="Presence (person)")
        self.add_property("role", PresenceRoleSchema(), False)
        self.add_property("event", EntityReferenceSchema(Event))
