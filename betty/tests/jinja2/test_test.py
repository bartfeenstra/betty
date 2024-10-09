from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pytest

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
    StartOfLifeEventType,
    Unknown as UnknownEventType,
    EndOfLifeEventType,
)
from betty.ancestry.name import Name
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence_role.presence_roles import (
    Subject,
    Witness,
    Unknown as UnknownPresenceRole,
)
from betty.date import DateRange, Date
from betty.json.linked_data import LinkedDataDumpableJsonLdObject
from betty.test_utils.ancestry.event_type import DummyEventType
from betty.test_utils.assets.templates import TemplateTestBase
from betty.test_utils.model import DummyUserFacingEntity
from betty.tests.ancestry.test___init__ import DummyHasFileReferences
from betty.tests.ancestry.test_link import DummyHasLinks

if TYPE_CHECKING:
    from betty.model import Entity


class TestTestEntity(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "entity_type_identifier", "data"),
        [
            ("true", None, Person(id="P1")),
            ("true", Person, Person(id="P1")),
            (
                "false",
                Person,
                Place(
                    id="P1",
                    names=[Name("The Place")],
                ),
            ),
            (
                "true",
                Place,
                Place(
                    id="P1",
                    names=[Name("The Place")],
                ),
            ),
            ("false", Place, Person(id="P1")),
            ("false", Place, 999),
            ("false", Person, object()),
        ],
    )
    async def test___call__(
        self, expected: str, entity_type_identifier: type[Entity] | None, data: Any
    ) -> None:
        entity_type_identifier_arg = (
            ""
            if entity_type_identifier is None
            else f'"{entity_type_identifier.plugin_id()}"'
        )
        template = f"{{% if data is entity({entity_type_identifier_arg}) %}}true{{% else %}}false{{% endif %}}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestSubjectRole(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", Subject()),
            ("false", Subject),
            ("false", UnknownPresenceRole()),
            ("false", object()),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is subject_role %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestWitnessRole(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", Witness()),
            ("false", Witness),
            ("false", UnknownPresenceRole()),
            ("false", object()),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is witness_role %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestDateRange(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", DateRange()),
            ("false", DateRange),
            ("false", Date()),
            ("false", object()),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is date_range %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestEndOfLifeEvent(TemplateTestBase):
    class _EndOfLife(EndOfLifeEventType, DummyEventType):
        pass

    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", Event(event_type=_EndOfLife())),
            ("false", Event(event_type=UnknownEventType())),
            ("false", Event),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is end_of_life_event %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestHasFileReferences(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", DummyHasFileReferences()),
            ("false", DummyHasFileReferences),
            ("false", object()),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is has_file_references %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestHasLinks(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", DummyHasLinks()),
            ("false", DummyHasLinks),
            ("false", object()),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is has_links %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestLinkedDataDumpable(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", LinkedDataDumpableJsonLdObject()),
            ("false", LinkedDataDumpableJsonLdObject),
            ("false", object()),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is linked_data_dumpable %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestStartOfLifeEvent(TemplateTestBase):
    class _StartOfLife(StartOfLifeEventType, DummyEventType):
        pass

    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", Event(event_type=_StartOfLife())),
            ("false", Event(event_type=UnknownEventType())),
            ("false", Event),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is start_of_life_event %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


class TestTestUserFacingEntity(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", DummyUserFacingEntity()),
            ("false", DummyUserFacingEntity),
            ("false", object()),
        ],
    )
    async def test(self, expected: str, data: Any) -> None:
        template = "{% if data is user_facing_entity %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
