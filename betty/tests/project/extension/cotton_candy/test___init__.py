from __future__ import annotations

from pathlib import Path
from typing import Iterator, TYPE_CHECKING

import pytest
from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
    Birth,
    Unknown as UnknownEventType,
    Death,
)
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.place import Place
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import (
    Subject,
    Unknown as UnknownPresenceRole,
)
from betty.ancestry.source import Source
from betty.assertion.error import AssertionFailed
from betty.date import Datey, Date, DateRange
from betty.model import persistent_id, ENTITY_TYPE_REPOSITORY, Entity
from betty.model.config import EntityReference
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.privacy import Privacy
from betty.project import Project
from betty.project.config import DEFAULT_LIFETIME_THRESHOLD, EntityTypeConfiguration
from betty.project.extension.cotton_candy import (
    person_timeline_events,
    associated_file_references,
    CottonCandy,
)
from betty.project.generate import generate
from betty.test_utils.model import DummyEntity, DummyUserFacingEntity
from betty.test_utils.project.extension import ExtensionTestBase
from betty.test_utils.project.extension.webpack import WebpackEntryPointProviderTestBase
from typing_extensions import override

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from betty.app import App
    from betty.ancestry.event_type import EventType
    from betty.ancestry.presence_role import PresenceRole

__REFERENCE_DATE = Date(1970, 1, 1)
_REFERENCE_DATES = (
    __REFERENCE_DATE,
    DateRange(__REFERENCE_DATE),
    DateRange(None, __REFERENCE_DATE),
)
_BEFORE_REFERENCE_DATE = Date(1900, 1, 1)
_AFTER_REFERENCE_DATE = Date(2000, 1, 1)


def _parameterize_with_associated_events() -> (
    Iterator[
        tuple[
            bool,
            PresenceRole,
            str | None,
            Privacy,
            EventType,
            Datey | None,
            Privacy,
            EventType,
            Datey | None,
        ]
    ]
):
    ids = (
        (True, "E1"),
        (False, None),
    )
    privacies = (
        (True, Privacy.PUBLIC),
        (False, Privacy.PRIVATE),
    )
    person_event_reference_dateys = (
        *((True, reference_date) for reference_date in _REFERENCE_DATES),
        (False, None),
    )
    person_presence_roles = (
        (True, Subject()),
        (False, UnknownPresenceRole()),
    )
    event_types = (
        (True, Birth()),
        (False, UnknownEventType()),
    )
    event_dateys_and_person_reference_event_types = (
        (True, _AFTER_REFERENCE_DATE, Birth()),
        (False, _BEFORE_REFERENCE_DATE, Birth()),
        (True, _BEFORE_REFERENCE_DATE, Death()),
        (False, _AFTER_REFERENCE_DATE, Death()),
    )
    for event_id_expected, event_id in ids:
        for event_privacy_expected, event_privacy in privacies:
            for (
                person_reference_event_privacy_expected,
                person_reference_event_privacy,
            ) in privacies:
                for (
                    person_reference_event_datey_expected,
                    person_reference_event_datey,
                ) in person_event_reference_dateys:
                    for (
                        person_presence_role_expected,
                        person_presence_role,
                    ) in person_presence_roles:
                        for (
                            event_datey_and_person_reference_event_type_expected,
                            event_datey,
                            person_reference_event_type,
                        ) in event_dateys_and_person_reference_event_types:
                            for event_type_expected, event_type in event_types:
                                yield (
                                    all(
                                        (
                                            person_presence_role_expected,
                                            event_id_expected,
                                            event_privacy_expected,
                                            event_type_expected,
                                            event_datey_and_person_reference_event_type_expected,
                                            person_reference_event_privacy_expected,
                                            person_reference_event_datey_expected,
                                        )
                                    ),
                                    person_presence_role,
                                    event_id,
                                    event_privacy,
                                    event_type,
                                    event_datey,
                                    person_reference_event_privacy,
                                    person_reference_event_type,
                                    person_reference_event_datey,
                                )


class TestPersonLifetimeEvents:
    @pytest.mark.parametrize(
        ("expected", "event_id", "event_privacy", "event_datey"),
        [
            # Events without dates are omitted from timelines.
            (False, "E1", Privacy.PUBLIC, None),
            (True, "E1", Privacy.PUBLIC, Date(1970, 1, 1)),
            # Events with generated IDs are included if they are the person's own.
            (True, None, Privacy.PUBLIC, Date(1970, 1, 1)),
            # Events with non-comparable dates are omitted from timelines.
            (False, "E1", Privacy.PUBLIC, Date(None, 1, 1)),
            # Private events are omitted from timelines.
            (False, "E1", Privacy.PRIVATE, Date(1970, 1, 1)),
        ],
    )
    async def test_with_person_event(
        self,
        expected: bool,
        event_id: str | None,
        event_privacy: Privacy,
        event_datey: Datey | None,
    ) -> None:
        person = Person()
        event = Event(
            id=event_id,
            event_type=UnknownEventType(),
            date=event_datey,
            privacy=event_privacy,
        )
        Presence(person, UnknownPresenceRole(), event)
        actual = list(person_timeline_events(person, DEFAULT_LIFETIME_THRESHOLD))
        assert expected is (event in actual)

    @pytest.mark.parametrize(
        (
            "expected",
            "presence_role",
            "event_id",
            "event_privacy",
            "event_type",
            "event_datey",
            "person_reference_event_privacy",
            "person_reference_event_type",
            "person_reference_event_datey",
        ),
        _parameterize_with_associated_events(),
    )
    async def test_with_associated_events(
        self,
        expected: bool,
        presence_role: PresenceRole,
        event_id: str | None,
        event_privacy: Privacy,
        event_type: EventType,
        event_datey: Datey | None,
        person_reference_event_privacy: Privacy,
        person_reference_event_type: EventType,
        person_reference_event_datey: Datey | None,
    ) -> None:
        event_ids = 0

        def _event_id(event_id: str | None) -> str | None:
            nonlocal event_ids

            if event_id is None:
                return None
            if not persistent_id(event_id):
                return event_id
            event_ids += 1
            return f"{event_id}-{event_ids}"

        person = Person()
        person_reference_event = Event(
            id=_event_id(event_id),
            event_type=person_reference_event_type,
            date=person_reference_event_datey,
            privacy=person_reference_event_privacy,
        )
        Presence(person, Subject(), person_reference_event)

        ancestor1 = Person()
        ancestor1.children.add(person)
        ancestor2 = Person()
        ancestor2.children.add(ancestor1)
        ancestor3 = Person()
        ancestor3.children.add(ancestor2)
        ancestor3_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_datey,
            privacy=event_privacy,
        )
        Presence(ancestor3, presence_role, ancestor3_event)

        descendant1 = Person()
        descendant1.parents.add(person)
        descendant2 = Person()
        descendant2.parents.add(descendant1)
        descendant3 = Person()
        descendant3.parents.add(descendant2)
        descendant3_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_datey,
            privacy=event_privacy,
        )
        Presence(descendant3, presence_role, descendant3_event)

        sibling = Person()
        sibling.parents.add(ancestor1)
        sibling_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_datey,
            privacy=event_privacy,
        )
        Presence(sibling, presence_role, sibling_event)

        actual = list(person_timeline_events(person, DEFAULT_LIFETIME_THRESHOLD))
        assert expected is (ancestor3_event in actual)
        assert expected is (descendant3_event in actual)
        assert expected is (sibling_event in actual)


class TestAssociatedFileReferences:
    async def test_with_plain_has_file_references_without_files(self) -> None:
        class DummyHasFileReferences(HasFileReferences, DummyEntity):
            pass

        assert list(associated_file_references(DummyHasFileReferences())) == []

    async def test_with_plain_has_file_references_with_files(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())

        class _DummyHasFileReferences(HasFileReferences, DummyEntity):
            pass

        has_file_references = _DummyHasFileReferences()
        FileReference(has_file_references, file1)
        FileReference(has_file_references, file2)
        assert [
            file_reference.file
            for file_reference in associated_file_references(has_file_references)
        ] == [file1, file2]

    async def test_with_event_without_files(self) -> None:
        event = Event(event_type=UnknownEventType())
        assert list(associated_file_references(event)) == []

    async def test_with_event_with_citations(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())
        file3 = File(path=Path())
        file4 = File(path=Path())
        event = Event(event_type=UnknownEventType())
        FileReference(event, file1)
        FileReference(event, file2)
        FileReference(event, file1)
        citation = Citation(source=Source())
        FileReference(citation, file3)
        FileReference(citation, file4)
        FileReference(citation, file2)
        event.citations = [citation]
        assert [
            file_reference.file for file_reference in associated_file_references(event)
        ] == [file1, file2, file3, file4]

    async def test_with_person_without_files(
        self,
    ) -> None:
        person = Person(id="1")
        assert list(associated_file_references(person)) == []

    async def test_with_person_with_files(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())
        file3 = File(path=Path())
        file4 = File(path=Path())
        file5 = File(path=Path())
        file6 = File(path=Path())
        person = Person(id="1")
        FileReference(person, file1)
        FileReference(person, file2)
        FileReference(person, file1)
        citation = Citation(source=Source())
        FileReference(citation, file3)
        FileReference(citation, file4)
        FileReference(citation, file2)
        name = PersonName(
            person=person,
            individual="Janet",
        )
        name.citations = [citation]
        event = Event(event_type=UnknownEventType())
        FileReference(event, file5)
        FileReference(event, file6)
        FileReference(event, file4)
        Presence(person, Subject(), event)
        assert [
            file_reference.file for file_reference in associated_file_references(person)
        ] == [file1, file2, file3, file4, file5, file6]

    async def test_with_place_without_files(self) -> None:
        place = Place(id="1")
        assert list(associated_file_references(place)) == []

    async def test_with_place_with_files(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())
        file3 = File(path=Path())
        file4 = File(path=Path())
        place = Place(id="1")
        FileReference(place, file1)
        FileReference(place, file2)
        FileReference(place, file1)
        event = Event(event_type=UnknownEventType())
        FileReference(event, file3)
        FileReference(event, file4)
        FileReference(event, file4)
        event.place = place
        assert [
            file_reference.file for file_reference in associated_file_references(place)
        ] == [file1, file2, file3, file4]


class TestCottonCandy(
    WebpackEntryPointProviderTestBase, ExtensionTestBase[CottonCandy]
):
    @override
    def get_sut_class(self) -> type[CottonCandy]:
        return CottonCandy

    async def test_filters(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await project.new_target(self.get_sut_class())
            assert len(sut.filters)

    async def test_public_css_paths(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await project.new_target(self.get_sut_class())
            assert len(sut.public_css_paths)

    async def test_bootstrap_should_validate_featured_entities_configuration(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await CottonCandy.new_for_project(project)
            sut.configuration.featured_entities.replace(
                EntityReference("non-existent-entity")
            )
            with pytest.raises(AssertionFailed):
                async with sut:
                    pass

    async def test_generate_html_list_for_third_party_entity(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=ProxyPluginRepository[Entity](
                StaticPluginRepository(DummyUserFacingEntity), ENTITY_TYPE_REPOSITORY
            ),
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(CottonCandy)
            project.configuration.entity_types.replace(
                EntityTypeConfiguration(DummyUserFacingEntity, generate_html_list=True)
            )
            async with project:
                await generate(project)
            assert (
                project.configuration.www_directory_path
                / DummyUserFacingEntity.plugin_id()
                / "index.html"
            ).is_file()
