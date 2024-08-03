from __future__ import annotations

from copy import copy
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, TYPE_CHECKING

import pytest
from betty.app import App
from betty.json.schema import Schema
from betty.locale.date import Date, DateRange
from betty.locale.localizable import static
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.ancestry import (
    Person,
    Event,
    Place,
    File,
    Note,
    Presence,
    PlaceName,
    PersonName,
    Enclosure,
    Described,
    Dated,
    HasPrivacy,
    HasMediaType,
    Link,
    HasLinks,
    HasNotes,
    HasFileReferences,
    Source,
    Citation,
    HasCitations,
    Ancestry,
    is_private,
    is_public,
    Privacy,
    merge_privacies,
    FileReference,
)
from betty.model.association import OneToOne
from betty.ancestry.event_type import Birth, UnknownEventType
from betty.ancestry.presence_role import Subject
from betty.project import LocaleConfiguration, Project
from betty.test_utils.model import DummyEntity, EntityTestBase
from geopy import Point
from typing_extensions import override

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump
    from betty.json.linked_data import LinkedDataDumpable


async def assert_dumps_linked_data(
    dumpable: LinkedDataDumpable, schema_definition: str | None = None
) -> DumpMapping[Dump]:
    async with App.new_temporary() as app, app, Project.new_temporary(app) as project:
        project.configuration.locales["en-US"].alias = "en"
        project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        async with project:
            actual = await dumpable.dump_linked_data(project)
            # Allow for a copy to be made in case the actual data does not contain $schema by design.
            actual_to_be_validated = actual
            if schema_definition:
                actual_to_be_validated = copy(actual)
                actual_to_be_validated["$schema"] = (
                    project.static_url_generator.generate(
                        f"schema.json#/definitions/{schema_definition}",
                        absolute=True,
                    )
                )
            schema = Schema(project)
            await schema.validate(actual_to_be_validated)
            return actual


class TestHasPrivacy:
    @pytest.mark.parametrize(
        ("privacy", "public", "private"),
        [
            (Privacy.PUBLIC, True, True),
            (Privacy.PUBLIC, False, True),
            (Privacy.PUBLIC, True, False),
            (Privacy.PUBLIC, False, False),
            (Privacy.PUBLIC, True, None),
            (Privacy.PUBLIC, False, None),
            (Privacy.PUBLIC, None, True),
            (Privacy.PUBLIC, None, False),
            (None, True, True),
            (None, True, False),
            (None, False, True),
            (None, False, False),
        ],
    )
    async def test___init___with_value_error(
        self, privacy: Privacy | None, public: bool | None, private: bool | None
    ) -> None:
        with pytest.raises(ValueError):  # noqa PT011
            HasPrivacy(privacy=privacy, public=public, private=private)

    @pytest.mark.parametrize(
        "privacy",
        [
            Privacy.UNDETERMINED,
            Privacy.PUBLIC,
            Privacy.PRIVATE,
        ],
    )
    async def test_get_privacy(self, privacy: Privacy) -> None:
        sut = HasPrivacy(privacy=privacy)
        assert sut.privacy is privacy
        assert sut.own_privacy is privacy

    async def test_set_privacy(self) -> None:
        sut = HasPrivacy()
        privacy = Privacy.PUBLIC
        sut.privacy = privacy
        assert sut.privacy is privacy
        assert sut.own_privacy is privacy

    async def test_del_privacy(self) -> None:
        sut = HasPrivacy()
        sut.privacy = Privacy.PUBLIC
        del sut.privacy
        assert sut.privacy is Privacy.UNDETERMINED
        assert sut.own_privacy is Privacy.UNDETERMINED

    @pytest.mark.parametrize(
        ("expected", "privacy"),
        [
            (True, Privacy.UNDETERMINED),
            (True, Privacy.PUBLIC),
            (False, Privacy.PRIVATE),
        ],
    )
    async def test_get_public(self, expected: bool, privacy: Privacy) -> None:
        sut = HasPrivacy(privacy=privacy)
        assert expected is sut.public

    async def test_set_public(self) -> None:
        sut = HasPrivacy()
        sut.public = True
        assert sut.public
        assert sut.privacy is Privacy.PUBLIC

    @pytest.mark.parametrize(
        ("expected", "privacy"),
        [
            (False, Privacy.UNDETERMINED),
            (False, Privacy.PUBLIC),
            (True, Privacy.PRIVATE),
        ],
    )
    async def test_get_private(self, expected: bool, privacy: Privacy) -> None:
        sut = HasPrivacy(privacy=privacy)
        assert expected is sut.private

    async def test_set_private(self) -> None:
        sut = HasPrivacy()
        sut.private = True
        assert sut.private
        assert sut.privacy is Privacy.PRIVATE


class TestIsPrivate:
    @pytest.mark.parametrize(
        ("expected", "target"),
        [
            (True, HasPrivacy(privacy=Privacy.PRIVATE)),
            (False, HasPrivacy(privacy=Privacy.PUBLIC)),
            (False, HasPrivacy(privacy=Privacy.UNDETERMINED)),
            (False, object()),
        ],
    )
    async def test(self, expected: bool, target: Any) -> None:
        assert expected == is_private(target)


class TestIsPublic:
    @pytest.mark.parametrize(
        ("expected", "target"),
        [
            (False, HasPrivacy(privacy=Privacy.PRIVATE)),
            (True, HasPrivacy(privacy=Privacy.PUBLIC)),
            (True, HasPrivacy(privacy=Privacy.UNDETERMINED)),
            (True, object()),
        ],
    )
    async def test(self, expected: bool, target: Any) -> None:
        assert expected == is_public(target)


class TestMergePrivacies:
    @pytest.mark.parametrize(
        ("expected", "privacies"),
        [
            (Privacy.PUBLIC, (Privacy.PUBLIC,)),
            (Privacy.UNDETERMINED, (Privacy.UNDETERMINED,)),
            (Privacy.PRIVATE, (Privacy.PRIVATE,)),
            (Privacy.UNDETERMINED, (Privacy.PUBLIC, Privacy.UNDETERMINED)),
            (Privacy.PRIVATE, (Privacy.PUBLIC, Privacy.PRIVATE)),
            (Privacy.PRIVATE, (Privacy.UNDETERMINED, Privacy.PRIVATE)),
            (Privacy.PRIVATE, (Privacy.PUBLIC, Privacy.UNDETERMINED, Privacy.PRIVATE)),
        ],
    )
    async def test(self, expected: Privacy, privacies: tuple[Privacy]) -> None:
        assert expected == merge_privacies(*privacies)


class TestDated:
    async def test_date(self) -> None:
        class _Dated(Dated):
            pass

        sut = _Dated()
        assert sut.date is None


class TestNote(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Note]:
        return Note

    async def test_id(self) -> None:
        note_id = "N1"
        sut = Note(
            id=note_id,
            text="Betty wrote this.",
        )
        assert note_id == sut.id

    async def test_text(self) -> None:
        text = "Betty wrote this."
        sut = Note(
            id="N1",
            text=text,
        )
        assert text == sut.text

    async def test_dump_linked_data_should_dump_full(self) -> None:
        note = Note(
            id="the_note",
            text="The Note",
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/note",
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": False,
            "text": "The Note",
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/note/the_note/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/note/the_note/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/note/the_note/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(note)
        assert expected == actual

    async def test_dump_linked_data_should_dump_private(self) -> None:
        note = Note(
            id="the_note",
            text="The Note",
            private=True,
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/note",
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": True,
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/note/the_note/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
            ],
        }
        actual = await assert_dumps_linked_data(note)
        assert expected == actual


class HasNotesTestEntity(HasNotes, DummyEntity):
    pass


class TestHasNotes:
    async def test_notes(self) -> None:
        sut = HasNotesTestEntity()
        assert list(sut.notes) == []


class TestDescribed:
    async def test_description(self) -> None:
        class _Described(Described):
            pass

        sut = _Described()
        assert not sut.description


class TestHasMediaType:
    async def test_media_type(self) -> None:
        class _HasMediaType(HasMediaType):
            pass

        sut = _HasMediaType()
        assert sut.media_type is None


class TestLink:
    async def test_url(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert url == sut.url

    async def test_media_type(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.media_type is None

    async def test_locale(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.locale is None

    async def test_description(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert not sut.description

    async def test_relationship(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.relationship is None

    async def test_label(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.label is None

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        link = Link("https://example.com")
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/link",
            "url": "https://example.com",
        }
        actual = await assert_dumps_linked_data(link, "link")
        assert expected == actual

    async def test_dump_linked_data_should_dump_full(self) -> None:
        link = Link(
            "https://example.com",
            label="The Link",
            relationship="external",
            locale="nl-NL",
            media_type=MediaType("text/html"),
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/link",
            "url": "https://example.com",
            "relationship": "external",
            "label": "The Link",
            "locale": "nl-NL",
            "mediaType": "text/html",
        }
        actual = await assert_dumps_linked_data(link, "link")
        assert expected == actual


class TestHasLinks:
    async def test_links(self) -> None:
        class DummyHasLinks(HasLinks, DummyEntity):
            pass

        sut = DummyHasLinks()
        assert sut.links == []


class DummyHasFileReferences(HasFileReferences, DummyEntity):
    pass


class TestFile(EntityTestBase):
    @override
    def get_sut_class(self) -> type[File]:
        return File

    async def test_id(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert file_id == sut.id

    async def test_name_with_name(self, tmp_path: Path) -> None:
        name = "a-file.a-suffix"
        sut = File(
            tmp_path / "file",
            name=name,
        )
        assert sut.name == name

    async def test_private(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_media_type(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.media_type is None
        media_type = MediaType("text/plain")
        sut.media_type = media_type
        assert media_type == sut.media_type

    async def test_path_with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = "BETTY01"
            file_path = Path(f.name)
            sut = File(
                id=file_id,
                path=file_path,
            )
            assert file_path == sut.path

    async def test_path_with_str(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = "BETTY01"
            sut = File(
                id=file_id,
                path=Path(f.name),
            )
            assert Path(f.name) == sut.path

    async def test_description(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert not sut.description
        description = "Hi, my name is Betty!"
        sut.description = description
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_notes(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert list(sut.notes) == []
        notes = [Note(text=""), Note(text="")]
        sut.notes = notes
        assert notes == list(sut.notes)

    async def test_referees(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert list(sut.referees) == []

        entity_one = DummyHasFileReferences()
        entity_two = DummyHasFileReferences()
        FileReference(entity_one, sut)
        FileReference(entity_two, sut)
        assert [file_reference.referee for file_reference in sut.referees] == [
            entity_one,
            entity_two,
        ]

    async def test_citations(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert list(sut.citations) == []

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
            )
            expected: dict[str, Any] = {
                "$schema": "https://example.com/schema.json#/definitions/entity/file",
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": False,
                "entities": [],
                "citations": [],
                "notes": [],
                "links": [
                    {
                        "$schema": "https://example.com/schema.json#/definitions/link",
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                    },
                    {
                        "$schema": "https://example.com/schema.json#/definitions/link",
                        "url": "/en/file/the_file/index.html",
                        "relationship": "alternate",
                        "mediaType": "text/html",
                        "locale": "en-US",
                    },
                    {
                        "$schema": "https://example.com/schema.json#/definitions/link",
                        "url": "/nl/file/the_file/index.html",
                        "relationship": "alternate",
                        "mediaType": "text/html",
                        "locale": "nl-NL",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert expected == actual

    async def test_dump_linked_data_should_dump_full(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
                media_type=MediaType("text/plain"),
            )
            file.notes.add(
                Note(
                    id="the_note",
                    text="The Note",
                )
            )
            FileReference(Person(id="the_person"), file)
            file.citations.add(
                Citation(
                    id="the_citation",
                    source=Source(
                        id="the_source",
                        name="The Source",
                    ),
                )
            )
            expected: dict[str, Any] = {
                "$schema": "https://example.com/schema.json#/definitions/entity/file",
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": False,
                "mediaType": "text/plain",
                "entities": [
                    "/person/the_person/index.json",
                ],
                "citations": [
                    "/citation/the_citation/index.json",
                ],
                "notes": [
                    "/note/the_note/index.json",
                ],
                "links": [
                    {
                        "$schema": "https://example.com/schema.json#/definitions/link",
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                    },
                    {
                        "$schema": "https://example.com/schema.json#/definitions/link",
                        "url": "/en/file/the_file/index.html",
                        "relationship": "alternate",
                        "mediaType": "text/html",
                        "locale": "en-US",
                    },
                    {
                        "$schema": "https://example.com/schema.json#/definitions/link",
                        "url": "/nl/file/the_file/index.html",
                        "relationship": "alternate",
                        "mediaType": "text/html",
                        "locale": "nl-NL",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert expected == actual

    async def test_dump_linked_data_should_dump_private(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
                private=True,
                media_type=MediaType("text/plain"),
            )
            file.notes.add(
                Note(
                    id="the_note",
                    text="The Note",
                )
            )
            FileReference(Person(id="the_person"), file)
            file.citations.add(
                Citation(
                    id="the_citation",
                    source=Source(
                        id="the_source",
                        name="The Source",
                    ),
                )
            )
            expected: dict[str, Any] = {
                "$schema": "https://example.com/schema.json#/definitions/entity/file",
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": True,
                "entities": [
                    "/person/the_person/index.json",
                ],
                "citations": [
                    "/citation/the_citation/index.json",
                ],
                "notes": [
                    "/note/the_note/index.json",
                ],
                "links": [
                    {
                        "$schema": "https://example.com/schema.json#/definitions/link",
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert expected == actual


class TestHasFileReferences:
    async def test_file_references(self) -> None:
        sut = DummyHasFileReferences()
        assert list(sut.file_references) == []
        file_one = File(path=Path())
        file_two = File(path=Path())
        FileReference(sut, file_one)
        FileReference(sut, file_two)
        assert [file_reference.file for file_reference in sut.file_references] == [
            file_one,
            file_two,
        ]


class TestSource(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Source]:
        return Source

    async def test_id(self) -> None:
        source_id = "S1"
        sut = Source(id=source_id)
        assert source_id == sut.id

    async def test_name(self) -> None:
        name = "The Source"
        sut = Source(name=name)
        assert name == sut.name

    async def test_contained_by(self) -> None:
        contained_by_source = Source()
        sut = Source()
        assert sut.contained_by is None
        sut.contained_by = contained_by_source
        assert contained_by_source == sut.contained_by

    async def test_contains(self) -> None:
        contains_source = Source()
        sut = Source()
        assert list(sut.contains) == []
        sut.contains = [contains_source]
        assert [contains_source] == list(sut.contains)

    async def test_walk_contains_without_contains(self) -> None:
        sut = Source()
        assert list(sut.walk_contains) == []

    async def test_walk_contains_with_contains(self) -> None:
        sut = Source()
        contains = Source(contained_by=sut)
        contains_contains = Source(contained_by=contains)
        assert [contains, contains_contains] == list(sut.walk_contains)

    async def test_citations(self) -> None:
        sut = Source()
        assert list(sut.citations) == []

    async def test_author(self) -> None:
        sut = Source()
        assert sut.author is None
        author = "Me"
        sut.author = author
        assert author == sut.author

    async def test_publisher(self) -> None:
        sut = Source()
        assert sut.publisher is None
        publisher = "Me"
        sut.publisher = publisher
        assert publisher == sut.publisher

    async def test_date(self) -> None:
        sut = Source()
        assert sut.date is None

    async def test_file_references(self) -> None:
        sut = Source()
        assert list(sut.file_references) == []

    async def test_links(self) -> None:
        sut = Source()
        assert list(sut.links) == []

    async def test_private(self) -> None:
        sut = Source()
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        source = Source(
            id="the_source",
            name="The Source",
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/source",
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": "The Source",
            "contains": [],
            "citations": [],
            "notes": [],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/source/the_source/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/source/the_source/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/source/the_source/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(source)
        assert expected == actual

    async def test_dump_linked_data_should_dump_full(self) -> None:
        link = Link("https://example.com/the-source")
        link.label = "The Source Online"
        source = Source(
            id="the_source",
            name="The Source",
            author="The Author",
            publisher="The Publisher",
            date=Date(2000, 1, 1),
            contained_by=Source(
                id="the_containing_source",
                name="The Containing Source",
            ),
            contains=[
                Source(
                    id="the_contained_source",
                    name="The Contained Source",
                )
            ],
            links=[link],
        )
        Citation(
            id="the_citation",
            source=source,
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/source",
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": "The Source",
            "author": "The Author",
            "publisher": "The Publisher",
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
            "date": {
                "year": 2000,
                "month": 1,
                "day": 1,
                "iso8601": "2000-01-01",
            },
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "https://example.com/the-source",
                    "label": "The Source Online",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/source/the_source/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/source/the_source/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/source/the_source/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(source)
        assert expected == actual

    async def test_dump_linked_data_should_dump_private(self) -> None:
        link = Link("https://example.com/the-source")
        link.label = "The Source Online"
        source = Source(
            id="the_source",
            name="The Source",
            author="The Author",
            publisher="The Publisher",
            date=Date(2000, 1, 1),
            contained_by=Source(
                id="the_containing_source",
                name="The Containing Source",
            ),
            contains=[
                Source(
                    id="the_contained_source",
                    name="The Contained Source",
                )
            ],
            links=[link],
            private=True,
        )
        Citation(
            id="the_citation",
            source=source,
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/source",
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": True,
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
        }
        actual = await assert_dumps_linked_data(source)
        actual.pop("links")
        assert expected == actual

    async def test_dump_linked_data_should_dump_with_private_associations(self) -> None:
        contained_by_source = Source(
            id="the_containing_source",
            name="The Containing Source",
        )
        contains_source = Source(
            id="the_contained_source",
            name="The Contained Source",
            private=True,
        )
        source = Source(
            id="the_source",
            contained_by=contained_by_source,
            contains=[contains_source],
        )
        Citation(
            id="the_citation",
            source=source,
            private=True,
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/source",
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
        }
        actual = await assert_dumps_linked_data(source)
        actual.pop("links")
        assert expected == actual


class _HasCitations(HasCitations, DummyEntity):
    pass


class TestCitation(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Citation]:
        return Citation

    async def test_id(self) -> None:
        citation_id = "C1"
        sut = Citation(
            id=citation_id,
            source=Source(),
        )
        assert citation_id == sut.id

    async def test_facts(self) -> None:
        fact = _HasCitations()
        sut = Citation(source=Source())
        assert list(sut.facts) == []
        sut.facts = [fact]
        assert [fact] == list(sut.facts)

    async def test_source(self) -> None:
        source = Source()
        sut = Citation(source=source)
        assert source == sut.source

    async def test_location(self) -> None:
        sut = Citation(source=Source())
        assert sut.location is None
        location = static("Somewhere")
        sut.location = location
        assert location == sut.location

    async def test_date(self) -> None:
        sut = Citation(source=Source())
        assert sut.date is None

    async def test_file_references(self) -> None:
        sut = Citation(source=Source())
        assert list(sut.file_references) == []

    async def test_private(self) -> None:
        sut = Citation(source=Source())
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(name="The Source"),
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/citation",
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": False,
            "facts": [],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/citation/the_citation/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/citation/the_citation/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert expected == actual

    async def test_dump_linked_data_should_dump_full(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(
                id="the_source",
                name="The Source",
            ),
        )
        citation.facts.add(
            Event(
                id="the_event",
                event_type=Birth(),
            )
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/citation",
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": False,
            "source": "/source/the_source/index.json",
            "facts": ["/event/the_event/index.json"],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/citation/the_citation/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/citation/the_citation/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert expected == actual

    async def test_dump_linked_data_should_dump_private(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(
                id="the_source",
                name="The Source",
            ),
            private=True,
        )
        citation.facts.add(
            Event(
                id="the_event",
                event_type=Birth(),
            )
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/citation",
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": True,
            "source": "/source/the_source/index.json",
            "facts": ["/event/the_event/index.json"],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert expected == actual


class TestHasCitations:
    async def test_citations(self) -> None:
        sut = _HasCitations()
        assert list(sut.citations) == []
        citation = Citation(source=Source())
        sut.citations = [citation]
        assert [citation] == list(sut.citations)


class TestPlaceName:
    @pytest.mark.parametrize(
        ("expected", "a", "b"),
        [
            (True, PlaceName(name="Ikke"), PlaceName(name="Ikke")),
            (
                True,
                PlaceName(name="Ikke", locale="nl-NL"),
                PlaceName(
                    name="Ikke",
                    locale="nl-NL",
                ),
            ),
            (
                False,
                PlaceName(
                    name="Ikke",
                    locale="nl-NL",
                ),
                PlaceName(
                    name="Ikke",
                    locale="nl-BE",
                ),
            ),
            (
                False,
                PlaceName(name="Ikke", locale="nl-NL"),
                PlaceName(
                    name="Ik",
                    locale="nl-NL",
                ),
            ),
            (False, PlaceName(name="Ikke"), PlaceName(name="Ik")),
            (False, PlaceName(name="Ikke"), None),
            (False, PlaceName(name="Ikke"), "not-a-place-name"),
        ],
    )
    async def test___eq__(self, expected: bool, a: PlaceName, b: Any) -> None:
        assert expected == (a == b)

    async def test___str__(self) -> None:
        name = "Ikke"
        sut = PlaceName(name=name)
        assert name == str(sut)

    async def test_name(self) -> None:
        name = "Ikke"
        sut = PlaceName(name=name)
        assert name == sut.name

    async def test_locale(self) -> None:
        locale = "nl-NL"
        sut = PlaceName(
            name="Ikke",
            locale=locale,
        )
        assert locale == sut.locale

    async def test_date(self) -> None:
        date = Date()
        sut = PlaceName(
            name="Ikke",
            date=date,
        )
        assert date == sut.date


class TestEnclosure(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Enclosure]:
        return Enclosure

    async def test_encloses(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert encloses == sut.encloses

    async def test_enclosed_by(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert enclosed_by == sut.enclosed_by

    async def test_date(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert date == sut.date

    async def test_citations(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        citation = Citation(source=Source())
        assert sut.date is None
        sut.citations = [citation]
        assert [citation] == list(sut.citations)


class TestPlace(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Place]:
        return Place

    async def test_events(self) -> None:
        sut = Place(
            id="P1",
            names=[PlaceName(name="The Place")],
        )
        event = Event(
            id="1",
            event_type=Birth(),
        )
        sut.events.add(event)
        assert event in sut.events
        assert sut == event.place
        sut.events.remove(event)
        assert list(sut.events) == []
        assert event.place is None

    async def test_enclosed_by(self) -> None:
        sut = Place(
            id="P1",
            names=[PlaceName(name="The Place")],
        )
        assert list(sut.enclosed_by) == []
        enclosing_place = Place(
            id="P2",
            names=[PlaceName(name="The Other Place")],
        )
        enclosure = Enclosure(encloses=sut, enclosed_by=enclosing_place)
        assert enclosure in sut.enclosed_by
        assert sut == enclosure.encloses
        sut.enclosed_by.remove(enclosure)
        assert list(sut.enclosed_by) == []
        assert enclosure.encloses is None

    async def test_encloses(self) -> None:
        sut = Place(
            id="P1",
            names=[PlaceName(name="The Place")],
        )
        assert list(sut.encloses) == []
        enclosed_place = Place(
            id="P2",
            names=[PlaceName(name="The Other Place")],
        )
        enclosure = Enclosure(encloses=enclosed_place, enclosed_by=sut)
        assert enclosure in sut.encloses
        assert sut == enclosure.enclosed_by
        sut.encloses.remove(enclosure)
        assert list(sut.encloses) == []
        assert enclosure.enclosed_by is None

    async def test_walk_encloses_without_encloses(self) -> None:
        sut = Place(
            id="P1",
            names=[PlaceName(name="The Place")],
        )
        assert list(sut.walk_encloses) == []

    async def test_walk_encloses_with_encloses(self) -> None:
        sut = Place(
            id="P1",
            names=[PlaceName(name="The Place")],
        )
        encloses_place = Place(
            id="P2",
            names=[PlaceName(name="The Other Place")],
        )
        encloses = Enclosure(encloses_place, sut)
        encloses_encloses_place = Place(
            id="P2",
            names=[PlaceName(name="The Other Other Place")],
        )
        encloses_encloses = Enclosure(encloses_encloses_place, encloses_place)
        assert [encloses, encloses_encloses] == list(sut.walk_encloses)

    async def test_id(self) -> None:
        place_id = "C1"
        sut = Place(
            id=place_id,
            names=[PlaceName(name="one")],
        )
        assert place_id == sut.id

    async def test_links(self) -> None:
        sut = Place(
            id="P1",
            names=[PlaceName(name="The Place")],
        )
        assert list(sut.links) == []

    async def test_names(self) -> None:
        name = PlaceName(name="The Place")
        sut = Place(
            id="P1",
            names=[name],
        )
        assert [name] == list(sut.names)

    async def test_coordinates(self) -> None:
        name = PlaceName(name="The Place")
        sut = Place(
            id="P1",
            names=[name],
        )
        coordinates = Point()
        sut.coordinates = coordinates
        assert coordinates == sut.coordinates

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        place_id = "the_place"
        name = "The Place"
        place = Place(
            id=place_id,
            names=[PlaceName(name=name)],
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/place",
            "@context": {
                "names": "https://schema.org/name",
                "enclosedBy": "https://schema.org/containedInPlace",
                "encloses": "https://schema.org/containsPlace",
                "events": "https://schema.org/event",
            },
            "@id": "https://example.com/place/the_place/index.json",
            "@type": "https://schema.org/Place",
            "id": place_id,
            "names": [
                {
                    "name": name,
                },
            ],
            "enclosedBy": [],
            "encloses": [],
            "events": [],
            "notes": [],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/place/the_place/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/place/the_place/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/place/the_place/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
            "private": False,
        }
        actual = await assert_dumps_linked_data(place)
        assert expected == actual

    async def test_dump_linked_data_should_dump_full(self) -> None:
        place_id = "the_place"
        name = "The Place"
        locale = "nl-NL"
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        link = Link("https://example.com/the-place")
        link.label = "The Place Online"
        place = Place(
            id=place_id,
            names=[
                PlaceName(
                    name=name,
                    locale=locale,
                )
            ],
            events=[
                Event(
                    id="E1",
                    event_type=Birth(),
                )
            ],
            links=[link],
        )
        place.coordinates = coordinates
        Enclosure(encloses=place, enclosed_by=Place(id="the_enclosing_place"))
        Enclosure(encloses=Place(id="the_enclosed_place"), enclosed_by=place)
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/place",
            "@context": {
                "names": "https://schema.org/name",
                "enclosedBy": "https://schema.org/containedInPlace",
                "encloses": "https://schema.org/containsPlace",
                "events": "https://schema.org/event",
                "coordinates": "https://schema.org/geo",
            },
            "@id": "https://example.com/place/the_place/index.json",
            "@type": "https://schema.org/Place",
            "id": place_id,
            "names": [
                {
                    "name": name,
                    "locale": "nl-NL",
                },
            ],
            "events": [
                "/event/E1/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "https://example.com/the-place",
                    "label": "The Place Online",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/place/the_place/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/place/the_place/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/place/the_place/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
            "coordinates": {
                "@context": {
                    "latitude": "https://schema.org/latitude",
                    "longitude": "https://schema.org/longitude",
                },
                "@type": "https://schema.org/GeoCoordinates",
                "latitude": latitude,
                "longitude": longitude,
            },
            "encloses": [
                "/place/the_enclosed_place/index.json",
            ],
            "enclosedBy": [
                "/place/the_enclosing_place/index.json",
            ],
            "private": False,
        }
        actual = await assert_dumps_linked_data(place)
        assert expected == actual


class TestPresence(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Presence]:
        return Presence

    async def test_person(self) -> None:
        person = Person()
        sut = Presence(person, Subject(), Event(event_type=UnknownEventType()))
        assert person == sut.person

    async def test_event(self) -> None:
        role = Subject()
        sut = Presence(Person(), role, Event(event_type=UnknownEventType()))
        assert role == sut.role

    async def test_role(self) -> None:
        event = Event(event_type=UnknownEventType())
        sut = Presence(Person(), Subject(), event)
        assert event == sut.event

    @pytest.mark.parametrize(
        ("expected", "person_privacy", "presence_privacy", "event_privacy"),
        [
            (Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PUBLIC),
            (Privacy.PRIVATE, Privacy.PRIVATE, Privacy.PUBLIC, Privacy.PUBLIC),
            (Privacy.PRIVATE, Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PRIVATE),
        ],
    )
    async def test_privacy(
        self,
        expected: Privacy,
        person_privacy: Privacy,
        presence_privacy: Privacy,
        event_privacy: Privacy,
    ) -> None:
        person = Person(privacy=person_privacy)
        event = Event(privacy=event_privacy, event_type=UnknownEventType())
        sut = Presence(person, Subject(), event)
        sut.privacy = presence_privacy

        assert expected == sut.privacy


class TestEvent(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Event]:
        return Event

    async def test_id(self) -> None:
        event_id = "E1"
        sut = Event(
            id=event_id,
            event_type=UnknownEventType(),
        )
        assert event_id == sut.id

    async def test_place(self) -> None:
        place = Place(
            id="1",
            names=[PlaceName(name="one")],
        )
        sut = Event(event_type=UnknownEventType())
        sut.place = place
        assert place == sut.place
        assert sut in place.events
        sut.place = None
        assert sut.place is None
        assert sut not in place.events

    async def test_presences(self) -> None:
        person = Person(id="P1")
        sut = Event(event_type=UnknownEventType())
        presence = Presence(person, Subject(), sut)
        sut.presences.add(presence)
        assert [presence] == list(sut.presences)
        assert sut == presence.event
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        assert presence.event is None

    async def test_date(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert sut.date is None
        date = Date()
        sut.date = date
        assert date == sut.date

    async def test_file_references(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert list(sut.file_references) == []

    async def test_citations(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert list(sut.citations) == []

    async def test_description(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert not sut.description

    async def test_private(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert sut.privacy is Privacy.UNDETERMINED

    async def test_event_type(self) -> None:
        event_type = UnknownEventType()
        sut = Event(event_type=event_type)
        assert sut.event_type is event_type

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/event",
            "@context": {
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "private": False,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/event/the_event/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/event/the_event/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert expected == actual

    async def test_dump_linked_data_should_dump_full(self) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="the_place",
                names=[PlaceName(name="The Place")],
            ),
        )
        Presence(Person(id="the_person"), Subject(), event)
        event.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/event",
            "@context": {
                "place": "https://schema.org/location",
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "private": False,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [
                {
                    "@type": "https://schema.org/Person",
                    "role": "subject",
                    "person": "/person/the_person/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "date": {
                "start": {
                    "@context": {
                        "iso8601": "https://schema.org/startDate",
                    },
                    "year": 2000,
                    "month": 1,
                    "day": 1,
                    "iso8601": "2000-01-01",
                },
                "end": {
                    "@context": {
                        "iso8601": "https://schema.org/endDate",
                    },
                    "year": 2019,
                    "month": 12,
                    "day": 31,
                    "iso8601": "2019-12-31",
                },
            },
            "place": "/place/the_place/index.json",
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/event/the_event/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/event/the_event/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert expected == actual

    async def test_dump_linked_data_should_dump_private(self) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
            private=True,
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="the_place",
                names=[PlaceName(name="The Place")],
            ),
        )
        Presence(Person(id="the_person"), Subject(), event)
        event.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/event",
            "@context": {
                "place": "https://schema.org/location",
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "private": True,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [
                {
                    "@type": "https://schema.org/Person",
                    "person": "/person/the_person/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "place": "/place/the_place/index.json",
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert expected == actual


class TestPersonName(EntityTestBase):
    @override
    def get_sut_class(self) -> type[PersonName]:
        return PersonName

    async def test_person(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert person == sut.person
        assert [sut] == list(person.names)

    async def test_locale(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.locale is None

    async def test_citations(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert list(sut.citations) == []

    async def test_individual(self) -> None:
        person = Person(id="1")
        individual = "Janet"
        sut = PersonName(
            person=person,
            individual=individual,
            affiliation="Not a Girl",
        )
        assert individual == sut.individual

    async def test_affiliation(self) -> None:
        person = Person(id="1")
        affiliation = "Not a Girl"
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation=affiliation,
        )
        assert affiliation == sut.affiliation


class TestPerson(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Person]:
        return Person

    async def test_parents(self) -> None:
        sut = Person(id="1")
        parent = Person(id="2")
        sut.parents.add(parent)
        assert [parent] == list(sut.parents)
        assert [sut] == list(parent.children)
        sut.parents.remove(parent)
        assert list(sut.parents) == []
        assert list(parent.children) == []

    async def test_children(self) -> None:
        sut = Person(id="1")
        child = Person(id="2")
        sut.children.add(child)
        assert [child] == list(sut.children)
        assert [sut] == list(child.parents)
        sut.children.remove(child)
        assert list(sut.children) == []
        assert list(child.parents) == []

    async def test_presences(self) -> None:
        event = Event(event_type=Birth())
        sut = Person(id="1")
        presence = Presence(sut, Subject(), event)
        sut.presences.add(presence)
        assert [presence] == list(sut.presences)
        assert sut == presence.person
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        assert presence.person is None

    async def test_names(self) -> None:
        sut = Person(id="1")
        name = PersonName(
            person=sut,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert [name] == list(sut.names)
        assert sut == name.person
        sut.names.remove(name)
        assert list(sut.names) == []
        assert name.person is None

    async def test_id(self) -> None:
        person_id = "P1"
        sut = Person(id=person_id)
        assert person_id == sut.id

    async def test_file_references(self) -> None:
        sut = Person(id="1")
        assert list(sut.file_references) == []

    async def test_citations(self) -> None:
        sut = Person(id="1")
        assert list(sut.citations) == []

    async def test_links(self) -> None:
        sut = Person(id="1")
        assert list(sut.links) == []

    async def test_private(self) -> None:
        sut = Person(id="1")
        assert sut.privacy is Privacy.UNDETERMINED

    async def test_siblings_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.siblings) == []

    async def test_siblings_with_one_common_parent(self) -> None:
        sut = Person(id="1")
        sibling = Person(id="2")
        parent = Person(id="3")
        parent.children = [sut, sibling]
        assert [sibling] == list(sut.siblings)

    async def test_siblings_with_multiple_common_parents(self) -> None:
        sut = Person(id="1")
        sibling = Person(id="2")
        parent = Person(id="3")
        parent.children = [sut, sibling]
        assert [sibling] == list(sut.siblings)

    async def test_ancestors_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.ancestors) == []

    async def test_ancestors_with_parent(self) -> None:
        sut = Person(id="1")
        parent = Person(id="3")
        sut.parents.add(parent)
        grandparent = Person(id="2")
        parent.parents.add(grandparent)
        assert [parent, grandparent] == list(sut.ancestors)

    async def test_descendants_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.descendants) == []

    async def test_descendants_with_parent(self) -> None:
        sut = Person(id="1")
        child = Person(id="3")
        sut.children.add(child)
        grandchild = Person(id="2")
        child.children.add(grandchild)
        assert [child, grandchild] == list(sut.descendants)

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        person_id = "the_person"
        person = Person(id=person_id)
        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/person",
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "private": False,
            "names": [],
            "parents": [],
            "children": [],
            "siblings": [],
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert expected == actual

    async def test_dump_linked_data_should_dump_full(self) -> None:
        parent_id = "the_parent"
        parent = Person(id=parent_id)

        child_id = "the_child"
        child = Person(id=child_id)

        sibling_id = "the_sibling"
        sibling = Person(id=sibling_id)
        sibling.parents.add(parent)

        person_id = "the_person"
        person_affiliation_name = "Person"
        person_individual_name = "The"
        person = Person(
            id=person_id,
            public=True,
        )
        PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
            locale="en-US",
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link(
            "https://example.com/the-person",
            label="The Person Online",
        )
        person.links.append(link)
        person.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        Presence(
            person,
            Subject(),
            Event(
                id="the_event",
                event_type=Birth(),
            ),
        )

        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/person",
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "private": False,
            "names": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/entity/personName",
                    "@context": {
                        "individual": "https://schema.org/givenName",
                        "affiliation": "https://schema.org/familyName",
                    },
                    "individual": person_individual_name,
                    "affiliation": person_affiliation_name,
                    "locale": "en-US",
                    "citations": [],
                    "private": False,
                },
            ],
            "parents": [
                "/person/the_parent/index.json",
            ],
            "children": [
                "/person/the_child/index.json",
            ],
            "siblings": [
                "/person/the_sibling/index.json",
            ],
            "presences": [
                {
                    "@context": {
                        "event": "https://schema.org/performerIn",
                    },
                    "role": "subject",
                    "event": "/event/the_event/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "https://example.com/the-person",
                    "label": "The Person Online",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/en/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/nl/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "nl-NL",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert expected == actual

    async def test_dump_linked_data_should_dump_private(self) -> None:
        parent_id = "the_parent"
        parent = Person(id=parent_id)

        child_id = "the_child"
        child = Person(id=child_id)

        sibling_id = "the_sibling"
        sibling = Person(id=sibling_id)
        sibling.parents.add(parent)

        person_id = "the_person"
        person_affiliation_name = "Person"
        person_individual_name = "The"
        person = Person(
            id=person_id,
            private=True,
        )
        PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link("https://example.com/the-person")
        link.label = "The Person Online"
        person.links.append(link)
        person.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        Presence(
            person,
            Subject(),
            Event(
                id="the_event",
                event_type=Birth(),
            ),
        )

        expected: dict[str, Any] = {
            "$schema": "https://example.com/schema.json#/definitions/entity/person",
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "names": [],
            "parents": [
                "/person/the_parent/index.json",
            ],
            "children": [
                "/person/the_child/index.json",
            ],
            "siblings": [
                "/person/the_sibling/index.json",
            ],
            "private": True,
            "presences": [
                {
                    "@context": {
                        "event": "https://schema.org/performerIn",
                    },
                    "event": "/event/the_event/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "$schema": "https://example.com/schema.json#/definitions/link",
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert expected == actual


class _TestAncestry_OneToOne_Left(DummyEntity):
    one_right = OneToOne["_TestAncestry_OneToOne_Left", "_TestAncestry_OneToOne_Right"](
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Left",
        "one_right",
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Right",
        "one_left",
    )


class _TestAncestry_OneToOne_Right(DummyEntity):
    one_left = OneToOne["_TestAncestry_OneToOne_Right", _TestAncestry_OneToOne_Left](
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Right",
        "one_left",
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Left",
        "one_right",
    )


class TestAncestry:
    async def test_add_(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        sut.add(left)
        assert left in sut
        assert right in sut

    async def test_add_unchecked_graph(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        sut.add_unchecked_graph(left)
        assert left in sut
        assert right not in sut


class TestFileReference:
    async def test_focus(self) -> None:
        sut = FileReference()
        focus = (1, 2, 3, 4)
        sut.focus = focus
        assert sut.focus == focus

    async def test_file(self) -> None:
        file = File(Path())
        sut = FileReference(None, file)
        assert sut.file is file

    async def test_referee(self) -> None:
        referee = DummyHasFileReferences()
        sut = FileReference(referee)
        assert sut.referee is referee
