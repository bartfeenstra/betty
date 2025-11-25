from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_links import HasLinks
from betty.date import Date, DateRange
from betty.jinja2.test import PluginTester
from betty.json.linked_data import LinkedDataDumpableWithSchemaJsonLdObject
from betty.media_type import MediaType
from betty.media_type.media_types import PDF, SVG
from betty.model import Entity
from betty.test_utils.jinja2 import assert_template_string
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginTwo,
)
from betty.tests.ancestry.test_has_notes import DummyHasNotes

if TYPE_CHECKING:
    from betty.machine_name import MachineName


class DummyHasLinks(HasLinks, Entity):
    pass


class DummyHasFileReferences(HasFileReferences, Entity):
    pass


class TestPluginTester:
    def test_tests(self):
        sut = PluginTester(DummyPluginDefinition)
        assert "classed_dummy_plugin_plugin" in sut.tests()

    @pytest.mark.parametrize(
        ("expected", "plugin_identifier", "data"),
        [
            (True, None, DummyPluginOne()),
            (True, DummyPluginOne.plugin.id, DummyPluginOne()),
            (False, DummyPluginOne.plugin.id, DummyPluginTwo()),
            (False, None, None),
            (False, None, object()),
        ],
    )
    async def test___call__(
        self, expected: bool, plugin_identifier: MachineName | None, data: Any
    ) -> None:
        sut = PluginTester(DummyPluginDefinition)
        assert sut(data, plugin_identifier) == expected


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
        ("true", DummyHasNotes()),
        ("false", DummyHasNotes),
        ("false", object()),
    ],
)
async def test_test_has_notes(expected: str, data: Any) -> None:
    template = "{% if data is has_notes %}true{% else %}false{% endif %}"
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
        ("true", LinkedDataDumpableWithSchemaJsonLdObject()),
        ("false", LinkedDataDumpableWithSchemaJsonLdObject),
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
