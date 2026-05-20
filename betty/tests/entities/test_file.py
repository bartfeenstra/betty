from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, cast, override

from betty.copyright_notices.public_domain import (
    PublicDomain as PublicDomainCopyrightNotice,
)
from betty.entities.citation import Citation
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entities.note import Note
from betty.entities.person import Person
from betty.entities.source import Source
from betty.entity import Entity
from betty.licenses.public_domain import PublicDomain as PublicDomainLicense
from betty.locale import default_locale_tag
from betty.localizer import default_localizer
from betty.media_types.plain_text import PLAIN_TEXT
from betty.privacy import Privacy
from betty.test_utils.entity import EntityTestBase
from betty.test_utils.entity.associations.has_file_references import (
    DummyHasFileReferences,
)
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.test_utils.conftest import AssertDumpsLinkedData

import pytest


class TestFile(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            File(__file__),
            File(__file__, description="My First File"),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    def test_id(self) -> None:
        sut = File(Path(__file__), id="my-first-file")
        assert sut.id == "my-first-file"

    def test_name__with_name(self, tmp_path: Path) -> None:
        name = "a-file.a-suffix"
        sut = File(
            tmp_path / "file",
            name=name,
        )
        assert sut.name == name

    def test_private(self) -> None:
        sut = File(Path(__file__))
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    def test_media_type(self) -> None:
        sut = File(Path(__file__))
        assert sut.media_type is None
        media_type = PLAIN_TEXT
        sut.media_type = media_type
        assert sut.media_type == media_type

    def test_path__with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_path = Path(f.name)
            sut = File(
                id="my-first-file",
                path=file_path,
            )
            assert sut.path == file_path

    def test_path__with_str(self) -> None:
        with NamedTemporaryFile() as f:
            sut = File(
                id="my-first-file",
                path=Path(f.name),
            )
            assert sut.path == Path(f.name)

    def test_description(self) -> None:
        sut = File(Path(__file__))
        assert not sut.description
        description = "Hi, my name is Betty!"
        sut.description = description
        assert sut.description is not None
        assert sut.description.localize(default_localizer) == description

    def test_notes(self) -> None:
        sut = File(Path(__file__))
        assert list(sut.notes) == []
        notes = [Note(DUMMY_LOCALIZABLE), Note(DUMMY_LOCALIZABLE)]
        sut.notes = notes
        assert list(sut.notes) == notes

    def test_referees(self) -> None:
        sut = File(Path(__file__))
        assert list(sut.referees) == []

        entity_one = DummyHasFileReferences()
        entity_two = DummyHasFileReferences()
        FileReference(entity_one, sut)
        FileReference(entity_two, sut)
        assert [file_reference.referee for file_reference in sut.referees] == [
            entity_one,
            entity_two,
        ]

    def test_citations(self) -> None:
        sut = File(Path(__file__))
        assert list(sut.citations) == []

    async def test_dump_linked_data__should_dump_minimal(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="my-first-file",
                path=Path(f.name),
            )
            expected: Mapping[str, Any] = {
                "@context": {"description": "https://schema.org/description"},
                "@id": "https://example.com/file/my-first-file/index.json",
                "id": "my-first-file",
                "privacy": False,
                "citations": [],
                "notes": [],
                "links": [],
                "referees": [],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="my-first-file",
                path=Path(f.name),
                media_type=PLAIN_TEXT,
                copyright_notice=PublicDomainCopyrightNotice(),
                license=PublicDomainLicense(),
                description="The Description",
            )
            file.notes.add(
                Note(
                    id="my-first-note",
                    text="The Note",
                )
            )
            FileReference(
                Person(id="my-first-person"), file, id="my-first-file-reference"
            )
            file.citations.add(
                Citation(
                    id="my-first-citation",
                    source=Source(
                        id="my-first-source",
                        name="The Source",
                    ),
                )
            )
            expected: Mapping[str, Any] = {
                "@context": {"description": "https://schema.org/description"},
                "@id": "https://example.com/file/my-first-file/index.json",
                "id": "my-first-file",
                "privacy": False,
                "mediaType": "text/plain",
                "citations": [
                    "/citation/my-first-citation/index.json",
                ],
                "notes": [
                    "/note/my-first-note/index.json",
                ],
                "links": [],
                "referees": [
                    "/file-reference/my-first-file-reference/index.json",
                ],
                "description": {default_locale_tag: "The Description"},
                "copyrightNotice": "public-domain",
                "license": "public-domain",
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="my-first-file",
                path=Path(f.name),
                privacy=Privacy.PRIVATE,
                media_type=PLAIN_TEXT,
                description="The File",
            )
            file.notes.add(
                Note(
                    id="my-first-note",
                    text="The Note",
                )
            )
            FileReference(
                Person(id="my-first-person"), file, id="my-first-file-reference"
            )
            file.citations.add(
                Citation(
                    id="my-first-citation",
                    source=Source(
                        id="my-first-source",
                        name="The Source",
                    ),
                )
            )
            expected: Mapping[str, Any] = {
                "@context": {"description": "https://schema.org/description"},
                "@id": "https://example.com/file/my-first-file/index.json",
                "id": "my-first-file",
                "privacy": True,
                "citations": [
                    "/citation/my-first-citation/index.json",
                ],
                "notes": [
                    "/note/my-first-note/index.json",
                ],
                "links": [],
                "referees": [
                    "/file-reference/my-first-file-reference/index.json",
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected
