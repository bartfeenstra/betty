from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
    EndOfLifeEventType,
    StartOfLifeEventType,
)
from betty.ancestry.event_type.event_types import (
    Unknown as UnknownEventType,
)
from betty.ancestry.name import Name
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence_role.presence_roles import (
    Subject,
    Witness,
)
from betty.ancestry.presence_role.presence_roles import (
    Unknown as UnknownPresenceRole,
)
from betty.date import Date, DateRange
from betty.jinja2.test import PluginTester
from betty.json.linked_data import LinkedDataDumpableJsonLdObject
from betty.media_type import MediaType
from betty.media_type.media_types import PDF, SVG
from betty.test_utils.ancestry.event_type import DummyEventType
from betty.test_utils.jinja2 import assert_template_string
from betty.test_utils.model import DummyUserFacingEntity
from betty.test_utils.plugin import DummyPlugin
from betty.tests.ancestry.test___init__ import DummyHasFileReferences
from betty.tests.ancestry.test_link import DummyHasLinks
from betty.warnings import BettyDeprecationWarning

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from betty.model import Entity


class DummyPluginOne(DummyPlugin):
    pass


class DummyPluginTwo(DummyPlugin):
    pass


class TestPluginTester:
    def test_tests(self):
        sut = PluginTester(DummyPlugin, "dummy_plugin")
        assert "dummy_plugin_plugin" in sut.tests()

    @pytest.mark.parametrize(
        ("expected", "plugin_identifier", "data"),
        [
            (True, None, DummyPluginOne()),
            (True, DummyPluginOne.plugin_id(), DummyPluginOne()),
            (False, DummyPluginOne.plugin_id(), DummyPluginTwo()),
            (False, None, None),
            (False, None, object()),
        ],
    )
    async def test___call__(
        self, expected: bool, plugin_identifier: MachineName | None, data: Any
    ) -> None:
        sut = PluginTester(DummyPlugin, "dummy_plugin")
        assert sut(data, plugin_identifier) == expected


class TestTestEntity:
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
        with pytest.warns(BettyDeprecationWarning):
            async with assert_template_string(
                template=template,
                data={
                    "data": data,
                },
            ) as (actual, _):
                assert actual == expected


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        ("true", Subject()),
        ("false", Subject),
        ("false", UnknownPresenceRole()),
        ("false", object()),
    ],
)
async def test_test_subject_role(expected: str, data: Any) -> None:
    template = "{% if data is subject_role %}true{% else %}false{% endif %}"
    with pytest.warns(BettyDeprecationWarning):
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        ("true", Witness()),
        ("false", Witness),
        ("false", UnknownPresenceRole()),
        ("false", object()),
    ],
)
async def test_test_witness_role(expected: str, data: Any) -> None:
    template = "{% if data is witness_role %}true{% else %}false{% endif %}"
    with pytest.warns(BettyDeprecationWarning):
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        ("true", DateRange()),
        ("false", DateRange),
        ("false", Date()),
        ("false", object()),
    ],
)
async def test_test_date_range(expected: str, data: Any) -> None:
    template = "{% if data is date_range %}true{% else %}false{% endif %}"
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected


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
async def test_test_end_of_life_event(expected: str, data: Any) -> None:
    template = "{% if data is end_of_life_event %}true{% else %}false{% endif %}"
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        ("true", DummyHasFileReferences()),
        ("false", DummyHasFileReferences),
        ("false", object()),
    ],
)
async def test_test_has_file_references(expected: str, data: Any) -> None:
    template = "{% if data is has_file_references %}true{% else %}false{% endif %}"
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        ("true", DummyHasLinks()),
        ("false", DummyHasLinks),
        ("false", object()),
    ],
)
async def test_test_has_links(expected: str, data: Any) -> None:
    template = "{% if data is has_links %}true{% else %}false{% endif %}"
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        ("true", LinkedDataDumpableJsonLdObject()),
        ("false", LinkedDataDumpableJsonLdObject),
        ("false", object()),
    ],
)
async def test_test_linked_data_dumpable(expected: str, data: Any) -> None:
    template = "{% if data is linked_data_dumpable %}true{% else %}false{% endif %}"
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected


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
async def test_test_start_of_life_event(expected: str, data: Any) -> None:
    template = "{% if data is start_of_life_event %}true{% else %}false{% endif %}"
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        ("true", DummyUserFacingEntity()),
        ("false", DummyUserFacingEntity),
        ("false", object()),
    ],
)
async def test_test_user_facing_entity(expected: str, data: Any) -> None:
    template = "{% if data is user_facing_entity %}true{% else %}false{% endif %}"
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        ("true", PDF),
        ("true", SVG),
        ("true", MediaType("image/gif")),
        ("true", MediaType("image/jpeg")),
        ("true", MediaType("image/png")),
        ("false", MediaType("text/plain")),
        ("false", MediaType("application/json")),
        ("false", None),
    ],
)
async def test_test_image_supported_media_type(expected: str, data: Any) -> None:
    template = (
        "{% if data is image_supported_media_type %}true{% else %}false{% endif %}"
    )
    async with assert_template_string(
        template=template,
        data={
            "data": data,
        },
    ) as (actual, _):
        assert actual == expected
