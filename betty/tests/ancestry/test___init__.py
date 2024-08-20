from __future__ import annotations

from collections.abc import MutableMapping, Mapping
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Sequence, TYPE_CHECKING

import pytest
from geopy import Point
from typing_extensions import override

from betty.ancestry import (
    Person,
    Event,
    Place,
    File,
    Note,
    Presence,
    Name,
    PersonName,
    Enclosure,
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
    LinkCollectionSchema,
    LinkSchema,
    PrivacySchema,
)
from betty.ancestry.event_type import Birth, UnknownEventType
from betty.ancestry.presence_role import Subject
from betty.app import App
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.date import Date, DateRange
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.model.association import OneToOne
from betty.project import Project
from betty.test_utils.ancestry import (
    DummyDated,
    DummyHasPrivacy,
    DummyDescribed,
    DummyHasLocale,
)
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.json.schema import SchemaTestBase
from betty.test_utils.model import DummyEntity, EntityTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping
    from betty.json.schema import Schema


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
            DummyHasPrivacy(privacy=privacy, public=public, private=private)

    @pytest.mark.parametrize(
        "privacy",
        [
            Privacy.UNDETERMINED,
            Privacy.PUBLIC,
            Privacy.PRIVATE,
        ],
    )
    async def test_get_privacy(self, privacy: Privacy) -> None:
        sut = DummyHasPrivacy(privacy=privacy)
        assert sut.privacy is privacy
        assert sut.own_privacy is privacy

    async def test_set_privacy(self) -> None:
        sut = DummyHasPrivacy()
        privacy = Privacy.PUBLIC
        sut.privacy = privacy
        assert sut.privacy is privacy
        assert sut.own_privacy is privacy

    async def test_del_privacy(self) -> None:
        sut = DummyHasPrivacy()
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
        sut = DummyHasPrivacy(privacy=privacy)
        assert expected is sut.public

    async def test_set_public(self) -> None:
        sut = DummyHasPrivacy()
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
        sut = DummyHasPrivacy(privacy=privacy)
        assert expected is sut.private

    async def test_set_private(self) -> None:
        sut = DummyHasPrivacy()
        sut.private = True
        assert sut.private
        assert sut.privacy is Privacy.PRIVATE

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "private": True,
                },
                DummyHasPrivacy(private=True),
            ),
            (
                {
                    "private": False,
                },
                DummyHasPrivacy(private=False),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasPrivacy
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class TestPrivacySchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(PrivacySchema(), [True, False], [None, 123, "abc", [], {}])]


class TestIsPrivate:
    @pytest.mark.parametrize(
        ("expected", "target"),
        [
            (True, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
            (False, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
            (False, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
            (False, object()),
        ],
    )
    async def test(self, expected: bool, target: Any) -> None:
        assert expected == is_private(target)


class TestIsPublic:
    @pytest.mark.parametrize(
        ("expected", "target"),
        [
            (False, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
            (True, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
            (True, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
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


class TestHasLocale:
    def test_locale_without___init___locale(self) -> None:
        sut = DummyHasLocale()
        assert sut.locale == UNDETERMINED_LOCALE

    def test_locale_with___init___locale(self) -> None:
        locale = "nl"
        sut = DummyHasLocale(locale=locale)
        assert sut.locale == locale

    def test_locale(self) -> None:
        locale = "nl"
        sut = DummyHasLocale()
        sut.locale = locale
        assert sut.locale == locale

    async def test_dump_linked_data(self) -> None:
        sut = DummyHasLocale()
        expected: Mapping[str, Any] = {
            "locale": UNDETERMINED_LOCALE,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected


class DummyDatedWithContextDefinitions(DummyDated):
    @override
    def dated_linked_data_contexts(self) -> tuple[str | None, str | None, str | None]:
        return "single-date", "start-date", "end-date"


class TestDated:
    async def test_date(self) -> None:
        sut = DummyDated()
        assert sut.date is None

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            # No date information.
            (
                {},
                DummyDated(),
            ),
            (
                {},
                DummyDatedWithContextDefinitions(),
            ),
            # A single date.
            (
                {
                    "date": {
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "iso8601": "1970-01-01",
                        "fuzzy": False,
                    }
                },
                DummyDated(date=Date(1970, 1, 1)),
            ),
            (
                {
                    "date": {
                        "@context": {"iso8601": "single-date"},
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "iso8601": "1970-01-01",
                        "fuzzy": False,
                    }
                },
                DummyDatedWithContextDefinitions(date=Date(1970, 1, 1)),
            ),
            # A date range with only a start date.
            (
                {
                    "date": {
                        "start": {
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "iso8601": "1970-01-01",
                            "fuzzy": False,
                        },
                        "end": None,
                    },
                },
                DummyDated(date=DateRange(Date(1970, 1, 1))),
            ),
            (
                {
                    "date": {
                        "start": {
                            "@context": {"iso8601": "start-date"},
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "iso8601": "1970-01-01",
                            "fuzzy": False,
                        },
                        "end": None,
                    },
                },
                DummyDatedWithContextDefinitions(date=DateRange(Date(1970, 1, 1))),
            ),
            # A date range with only an end date.
            (
                {
                    "date": {
                        "start": None,
                        "end": {
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "iso8601": "2000-12-31",
                            "fuzzy": False,
                        },
                    },
                },
                DummyDated(date=DateRange(None, Date(2000, 12, 31))),
            ),
            (
                {
                    "date": {
                        "start": None,
                        "end": {
                            "@context": {"iso8601": "end-date"},
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "iso8601": "2000-12-31",
                            "fuzzy": False,
                        },
                    },
                },
                DummyDatedWithContextDefinitions(
                    date=DateRange(None, Date(2000, 12, 31))
                ),
            ),
            # A date range with both a start and an end date.
            (
                {
                    "date": {
                        "start": {
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "iso8601": "1970-01-01",
                            "fuzzy": False,
                        },
                        "end": {
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "iso8601": "2000-12-31",
                            "fuzzy": False,
                        },
                    },
                },
                DummyDated(date=DateRange(Date(1970, 1, 1), Date(2000, 12, 31))),
            ),
            (
                {
                    "date": {
                        "start": {
                            "@context": {"iso8601": "start-date"},
                            "year": 1970,
                            "month": 1,
                            "day": 1,
                            "iso8601": "1970-01-01",
                            "fuzzy": False,
                        },
                        "end": {
                            "@context": {"iso8601": "end-date"},
                            "year": 2000,
                            "month": 12,
                            "day": 31,
                            "iso8601": "2000-12-31",
                            "fuzzy": False,
                        },
                    },
                },
                DummyDatedWithContextDefinitions(
                    date=DateRange(Date(1970, 1, 1), Date(2000, 12, 31))
                ),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


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
        assert sut.id == note_id

    async def test_text(self) -> None:
        text = "Betty wrote this."
        sut = Note(
            id="N1",
            text=text,
        )
        assert sut.text.localize(DEFAULT_LOCALIZER) == text

    async def test_dump_linked_data_should_dump_full(self) -> None:
        note = Note(
            id="the_note",
            text="The Note",
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": False,
            "text": {"translations": {"und": "The Note"}},
            "links": [
                {
                    "url": "/note/the_note/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/note/the_note/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(note)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        note = Note(
            id="the_note",
            text="The Note",
            private=True,
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/note/the_note/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_note",
            "private": True,
            "links": [
                {
                    "url": "/note/the_note/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
            ],
        }
        actual = await assert_dumps_linked_data(note)
        assert actual == expected


class DummyHasNotes(HasNotes, DummyEntity):
    pass


class TestHasNotes:
    async def test_notes(self) -> None:
        sut = DummyHasNotes()
        assert list(sut.notes) == []

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "notes": [],
                },
                DummyHasNotes(),
            ),
            (
                {
                    "notes": [],
                },
                DummyHasNotes(notes=[Note(text="Hello, world!")]),
            ),
            (
                {
                    "notes": ["/note/my-first-note/index.json"],
                },
                DummyHasNotes(notes=[Note(text="Hello, world!", id="my-first-note")]),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasNotes
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class TestDescribed:
    async def test_description(self) -> None:
        sut = DummyDescribed()
        assert not sut.description

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {},
                DummyDescribed(),
            ),
            (
                {
                    "@context": {"description": "https://schema.org/description"},
                    "description": {"translations": {"und": "Hello, world!"}},
                },
                DummyDescribed(description="Hello, world!"),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class DummyHasMediaType(HasMediaType, DummyEntity):
    pass


class TestHasMediaType:
    async def test_media_type(self) -> None:
        sut = DummyHasMediaType()
        assert sut.media_type is None

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {},
                DummyHasMediaType(),
            ),
            (
                {
                    "mediaType": "text/plain",
                },
                DummyHasMediaType(media_type=MediaType("text/plain")),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasNotes
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class TestLink:
    async def test_url(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.url == url

    async def test_media_type(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.media_type is None

    async def test_locale(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.locale is UNDETERMINED_LOCALE

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
        assert not sut.label

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        link = Link("https://example.com")
        expected: Mapping[str, Any] = {
            "url": "https://example.com",
            "locale": "und",
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        link = Link(
            "https://example.com",
            label="The Link",
            relationship="external",
            locale="nl-NL",
            media_type=MediaType("text/html"),
        )
        expected: Mapping[str, Any] = {
            "url": "https://example.com",
            "relationship": "external",
            "label": {"translations": {UNDETERMINED_LOCALE: "The Link"}},
            "locale": "nl-NL",
            "mediaType": "text/html",
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected


class TestLinkSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                LinkSchema(),
                _DUMMY_LINK_DUMPS,
                [True, False, None, 123, "abc", [], {}],
            )
        ]


class DummyHasLinks(HasLinks, DummyEntity):
    pass


class TestHasLinks:
    async def test_links(self) -> None:
        sut = DummyHasLinks()
        assert sut.links == []

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {"links": []},
                DummyHasLinks(),
            ),
            (
                {"links": [{"url": "https://example.com", "locale": "und"}]},
                DummyHasLinks(links=[Link("https://example.com")]),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


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
        assert sut.id == file_id

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
        assert sut.media_type == media_type

    async def test_path_with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = "BETTY01"
            file_path = Path(f.name)
            sut = File(
                id=file_id,
                path=file_path,
            )
            assert sut.path == file_path

    async def test_path_with_str(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = "BETTY01"
            sut = File(
                id=file_id,
                path=Path(f.name),
            )
            assert sut.path == Path(f.name)

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
        assert list(sut.notes) == notes

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
            expected: Mapping[str, Any] = {
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": False,
                "entities": [],
                "citations": [],
                "notes": [],
                "links": [
                    {
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                        "locale": "und",
                    },
                    {
                        "url": "/file/the_file/index.html",
                        "relationship": "alternate",
                        "mediaType": "text/html",
                        "locale": "en-US",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

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
            expected: Mapping[str, Any] = {
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
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                        "locale": "und",
                    },
                    {
                        "url": "/file/the_file/index.html",
                        "relationship": "alternate",
                        "mediaType": "text/html",
                        "locale": "en-US",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

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
            expected: Mapping[str, Any] = {
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
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                        "locale": "und",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected


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
        assert sut.id == source_id

    async def test_name(self) -> None:
        name = "The Source"
        sut = Source(name=name)
        assert sut.name.localize(DEFAULT_LOCALIZER) == name

    async def test_contained_by(self) -> None:
        contained_by_source = Source()
        sut = Source()
        assert sut.contained_by is None
        sut.contained_by = contained_by_source
        assert sut.contained_by is contained_by_source

    async def test_contains(self) -> None:
        contains_source = Source()
        sut = Source()
        assert list(sut.contains) == []
        sut.contains = [contains_source]
        assert list(sut.contains) == [contains_source]

    async def test_walk_contains_without_contains(self) -> None:
        sut = Source()
        assert list(sut.walk_contains) == []

    async def test_walk_contains_with_contains(self) -> None:
        sut = Source()
        contains = Source(contained_by=sut)
        contains_contains = Source(contained_by=contains)
        assert list(sut.walk_contains) == [contains, contains_contains]

    async def test_citations(self) -> None:
        sut = Source()
        assert list(sut.citations) == []

    async def test_author(self) -> None:
        sut = Source()
        assert not sut.author
        author = "Me"
        sut.author = author
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_publisher(self) -> None:
        sut = Source()
        assert not sut.publisher
        publisher = "Me"
        sut.publisher = publisher
        assert sut.publisher.localize(DEFAULT_LOCALIZER) == publisher

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
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": {"translations": {"und": "The Source"}},
            "contains": [],
            "citations": [],
            "notes": [],
            "links": [
                {
                    "url": "/source/the_source/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/source/the_source/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(source)
        assert actual == expected

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
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": {"translations": {"und": "The Source"}},
            "author": {"translations": {"und": "The Author"}},
            "publisher": {"translations": {"und": "The Publisher"}},
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
                "fuzzy": False,
            },
            "links": [
                {
                    "url": "https://example.com/the-source",
                    "label": {
                        "translations": {UNDETERMINED_LOCALE: "The Source Online"}
                    },
                    "locale": "und",
                },
                {
                    "url": "/source/the_source/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/source/the_source/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(source)
        assert actual == expected

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
        expected: Mapping[str, Any] = {
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
        assert isinstance(actual, MutableMapping)
        actual.pop("links")
        assert actual == expected

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
        expected: Mapping[str, Any] = {
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
        assert isinstance(actual, MutableMapping)
        actual.pop("links")
        assert actual == expected


class DummyHasCitations(HasCitations, DummyEntity):
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
        assert sut.id == citation_id

    async def test_facts(self) -> None:
        fact = DummyHasCitations()
        sut = Citation(source=Source())
        assert list(sut.facts) == []
        sut.facts = [fact]
        assert list(sut.facts) == [fact]

    async def test_source(self) -> None:
        source = Source()
        sut = Citation(source=source)
        assert sut.source is source

    async def test_location(self) -> None:
        sut = Citation(source=Source())
        assert not sut.location
        location = "Somewhere"
        sut.location = location
        assert sut.location.localize(DEFAULT_LOCALIZER) == location

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
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": False,
            "facts": [],
            "links": [
                {
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/citation/the_citation/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected

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
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": False,
            "source": "/source/the_source/index.json",
            "facts": ["/event/the_event/index.json"],
            "links": [
                {
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/citation/the_citation/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected

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
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": True,
            "source": "/source/the_source/index.json",
            "facts": ["/event/the_event/index.json"],
            "links": [
                {
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected


class TestHasCitations:
    async def test_citations(self) -> None:
        sut = DummyHasCitations()
        assert list(sut.citations) == []
        citation = Citation(source=Source())
        sut.citations = [citation]
        assert list(sut.citations) == [citation]

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {"citations": []},
                DummyHasCitations(),
            ),
            (
                {"citations": []},
                DummyHasCitations(citations=[Citation()]),
            ),
            (
                {"citations": ["/citation/my-first-citation/index.json"]},
                DummyHasCitations(citations=[Citation(id="my-first-citation")]),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class TestName:
    @pytest.mark.parametrize(
        ("expected", "a", "b"),
        [
            (True, Name("Ikke"), Name("Ikke")),
            (
                True,
                Name({"nl-NL": "Ikke"}),
                Name({"nl-NL": "Ikke"}),
            ),
            (
                False,
                Name({"nl-NL": "Ikke"}),
                Name({"nl-BE": "Ikke"}),
            ),
            (
                False,
                Name({"nl-NL": "Ikke"}),
                Name({"nl-NL": "Ik"}),
            ),
            (False, Name("Ikke"), Name("Ik")),
            (False, Name("Ikke"), None),
            (False, Name("Ikke"), "not-a-place-name"),
        ],
    )
    async def test___eq__(self, expected: bool, a: Name, b: Any) -> None:
        assert expected == (a == b)

    async def test_date(self) -> None:
        date = Date()
        sut = Name(
            "Ikke",
            date=date,
        )
        assert sut.date is date


class TestEnclosure(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Enclosure]:
        return Enclosure

    async def test_encloses(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert sut.encloses is encloses

    async def test_enclosed_by(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert sut.enclosed_by is enclosed_by

    async def test_date(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert sut.date is date

    async def test_citations(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        citation = Citation(source=Source())
        assert sut.date is None
        sut.citations = [citation]
        assert list(sut.citations) == [citation]


class TestPlace(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Place]:
        return Place

    async def test_events(self) -> None:
        sut = Place(
            id="P1",
            names=[Name("The Place")],
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
            names=[Name("The Place")],
        )
        assert list(sut.enclosed_by) == []
        enclosing_place = Place(
            id="P2",
            names=[Name("The Other Place")],
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
            names=[Name("The Place")],
        )
        assert list(sut.encloses) == []
        enclosed_place = Place(
            id="P2",
            names=[Name("The Other Place")],
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
            names=[Name("The Place")],
        )
        assert list(sut.walk_encloses) == []

    async def test_walk_encloses_with_encloses(self) -> None:
        sut = Place(
            id="P1",
            names=[Name("The Place")],
        )
        encloses_place = Place(
            id="P2",
            names=[Name("The Other Place")],
        )
        encloses = Enclosure(encloses_place, sut)
        encloses_encloses_place = Place(
            id="P2",
            names=[Name("The Other Other Place")],
        )
        encloses_encloses = Enclosure(encloses_encloses_place, encloses_place)
        assert list(sut.walk_encloses) == [encloses, encloses_encloses]

    async def test_id(self) -> None:
        place_id = "C1"
        sut = Place(
            id=place_id,
            names=[Name("one")],
        )
        assert sut.id == place_id

    async def test_links(self) -> None:
        sut = Place(
            id="P1",
            names=[Name("The Place")],
        )
        assert list(sut.links) == []

    async def test_names(self) -> None:
        name = Name("The Place")
        sut = Place(
            id="P1",
            names=[name],
        )
        assert list(sut.names) == [name]

    async def test_coordinates(self) -> None:
        name = Name("The Place")
        sut = Place(
            id="P1",
            names=[name],
        )
        coordinates = Point()
        sut.coordinates = coordinates
        assert sut.coordinates == coordinates

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        place_id = "the_place"
        place = Place(id=place_id)
        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "enclosedBy": "https://schema.org/containedInPlace",
                "encloses": "https://schema.org/containsPlace",
                "events": "https://schema.org/event",
            },
            "@id": "https://example.com/place/the_place/index.json",
            "@type": "https://schema.org/Place",
            "id": place_id,
            "names": [],
            "enclosedBy": [],
            "encloses": [],
            "events": [],
            "notes": [],
            "links": [
                {
                    "url": "/place/the_place/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/place/the_place/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
            "private": False,
        }
        actual = await assert_dumps_linked_data(place)
        assert actual == expected

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
            names=[Name({locale: name}, date=Date(1970, 1, 1))],
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
        expected: Mapping[str, Any] = {
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
                {"translations": {"nl-NL": name}},
            ],
            "events": [
                "/event/E1/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "url": "https://example.com/the-place",
                    "label": {
                        "translations": {UNDETERMINED_LOCALE: "The Place Online"}
                    },
                    "locale": "und",
                },
                {
                    "url": "/place/the_place/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/place/the_place/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
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
        assert actual == expected


class TestPresence(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Presence]:
        return Presence

    async def test_person(self) -> None:
        person = Person()
        sut = Presence(person, Subject(), Event(event_type=UnknownEventType()))
        assert sut.person == person

    async def test_event(self) -> None:
        role = Subject()
        sut = Presence(Person(), role, Event(event_type=UnknownEventType()))
        assert sut.role == role

    async def test_role(self) -> None:
        event = Event(event_type=UnknownEventType())
        sut = Presence(Person(), Subject(), event)
        assert sut.event == event

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

        assert sut.privacy == expected


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
        assert sut.id == event_id

    async def test_place(self) -> None:
        place = Place(
            id="1",
            names=[Name("one")],
        )
        sut = Event(event_type=UnknownEventType())
        sut.place = place
        assert sut.place == place
        assert sut in place.events
        sut.place = None
        assert sut.place is None
        assert sut not in place.events

    async def test_presences(self) -> None:
        person = Person(id="P1")
        sut = Event(event_type=UnknownEventType())
        presence = Presence(person, Subject(), sut)
        sut.presences.add(presence)
        assert list(sut.presences) == [presence]
        assert sut == presence.event
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        assert presence.event is None

    async def test_date(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert sut.date is None
        date = Date()
        sut.date = date
        assert sut.date == date

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
        expected: Mapping[str, Any] = {
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
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/event/the_event/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="the_place",
                names=[Name("The Place")],
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
        expected: Mapping[str, Any] = {
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
                    "fuzzy": False,
                },
                "end": {
                    "@context": {
                        "iso8601": "https://schema.org/endDate",
                    },
                    "year": 2019,
                    "month": 12,
                    "day": 31,
                    "iso8601": "2019-12-31",
                    "fuzzy": False,
                },
            },
            "place": "/place/the_place/index.json",
            "links": [
                {
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/event/the_event/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
            private=True,
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="the_place",
                names=[Name("The Place")],
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
        expected: Mapping[str, Any] = {
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
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected


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
        assert sut.person == person
        assert [sut] == list(person.names)

    async def test_locale(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.locale is UNDETERMINED_LOCALE

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
        assert sut.individual == individual

    async def test_affiliation(self) -> None:
        person = Person(id="1")
        affiliation = "Not a Girl"
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation=affiliation,
        )
        assert sut.affiliation == affiliation

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                    },
                    "individual": "Jane",
                    "locale": UNDETERMINED_LOCALE,
                    "private": False,
                    "citations": [],
                },
                PersonName(individual="Jane"),
            ),
            (
                {
                    "@context": {
                        "affiliation": "https://schema.org/familyName",
                    },
                    "affiliation": "Dough",
                    "locale": UNDETERMINED_LOCALE,
                    "private": False,
                    "citations": [],
                },
                PersonName(affiliation="Dough"),
            ),
            (
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                        "affiliation": "https://schema.org/familyName",
                    },
                    "individual": "Jane",
                    "affiliation": "Dough",
                    "locale": "nl-NL",
                    "private": False,
                    "citations": [],
                },
                PersonName(individual="Jane", affiliation="Dough", locale="nl-NL"),
            ),
            (
                {
                    "locale": "nl-NL",
                    "private": True,
                    "citations": [],
                },
                PersonName(
                    individual="Jane", affiliation="Dough", locale="nl-NL", private=True
                ),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: PersonName
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class TestPerson(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Person]:
        return Person

    async def test_parents(self) -> None:
        sut = Person(id="1")
        parent = Person(id="2")
        sut.parents.add(parent)
        assert list(sut.parents) == [parent]
        assert [sut] == list(parent.children)
        sut.parents.remove(parent)
        assert list(sut.parents) == []
        assert list(parent.children) == []

    async def test_children(self) -> None:
        sut = Person(id="1")
        child = Person(id="2")
        sut.children.add(child)
        assert list(sut.children) == [child]
        assert [sut] == list(child.parents)
        sut.children.remove(child)
        assert list(sut.children) == []
        assert list(child.parents) == []

    async def test_presences(self) -> None:
        event = Event(event_type=Birth())
        sut = Person(id="1")
        presence = Presence(sut, Subject(), event)
        sut.presences.add(presence)
        assert list(sut.presences) == [presence]
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
        assert list(sut.names) == [name]
        assert sut == name.person
        sut.names.remove(name)
        assert list(sut.names) == []
        assert name.person is None

    async def test_id(self) -> None:
        person_id = "P1"
        sut = Person(id=person_id)
        assert sut.id == person_id

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
        assert list(sut.siblings) == [sibling]

    async def test_siblings_with_multiple_common_parents(self) -> None:
        sut = Person(id="1")
        sibling = Person(id="2")
        parent = Person(id="3")
        parent.children = [sut, sibling]
        assert list(sut.siblings) == [sibling]

    async def test_ancestors_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.ancestors) == []

    async def test_ancestors_with_parent(self) -> None:
        sut = Person(id="1")
        parent = Person(id="3")
        sut.parents.add(parent)
        grandparent = Person(id="2")
        parent.parents.add(grandparent)
        assert list(sut.ancestors) == [parent, grandparent]

    async def test_descendants_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.descendants) == []

    async def test_descendants_with_parent(self) -> None:
        sut = Person(id="1")
        child = Person(id="3")
        sut.children.add(child)
        grandchild = Person(id="2")
        child.children.add(grandchild)
        assert list(sut.descendants) == [child, grandchild]

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        person_id = "the_person"
        person = Person(id=person_id)
        expected: Mapping[str, Any] = {
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
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

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

        expected: Mapping[str, Any] = {
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
                    "url": "https://example.com/the-person",
                    "label": {
                        "translations": {UNDETERMINED_LOCALE: "The Person Online"}
                    },
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

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

        expected: Mapping[str, Any] = {
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
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected


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


_DUMMY_LINK_DUMPS: Sequence[DumpMapping[Dump]] = (
    {
        "url": "https://example.com",
    },
    {
        "url": "https://example.com",
        "relationship": "canonical",
    },
    {
        "url": "https://example.com",
        "label": {"translations": {UNDETERMINED_LOCALE: "Hello, world!"}},
    },
    {
        "url": "https://example.com",
        "privacy": True,
    },
)


class TestLinkCollectionSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        schemas = []
        valid_datas: Sequence[Dump] = [
            *[[data] for data in _DUMMY_LINK_DUMPS],  # type: ignore[list-item]
            list(_DUMMY_LINK_DUMPS),
        ]
        invalid_datas: Sequence[Dump] = [True, False, None, 123, "abc", {}]
        async with App.new_temporary() as app, app, Project.new_temporary(
            app
        ) as project, project:
            schemas.append(
                (
                    LinkCollectionSchema(),
                    valid_datas,
                    invalid_datas,
                )
            )
        return schemas
