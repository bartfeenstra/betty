from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pytest

from betty.ancestry import Person, Place, PlaceName
from betty.ancestry.presence_role import Subject, Attendee, Witness
from betty.test_utils.assets.templates import TemplateTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping
    from betty.model import Entity


class TestTestEntity(TemplateTestBase):
    @pytest.mark.parametrize(
        ("expected", "entity_type", "data"),
        [
            ("true", Person, Person(id="P1")),
            (
                "false",
                Person,
                Place(
                    id="P1",
                    names=[PlaceName(name="The Place")],
                ),
            ),
            (
                "true",
                Place,
                Place(
                    id="P1",
                    names=[PlaceName(name="The Place")],
                ),
            ),
            ("false", Place, Person(id="P1")),
            ("false", Place, 999),
            ("false", Person, object()),
        ],
    )
    async def test(
        self, expected: str, entity_type: type[Entity], data: Mapping[str, Any]
    ) -> None:
        template = f'{{% if data is entity("{entity_type.plugin_id()}") %}}true{{% else %}}false{{% endif %}}'
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
            ("false", Attendee()),
            ("false", 9),
        ],
    )
    async def test(self, expected: str, data: Mapping[str, Any]) -> None:
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
            ("false", Attendee()),
            ("false", 9),
        ],
    )
    async def test(self, expected: str, data: Mapping[str, Any]) -> None:
        template = "{% if data is witness_role %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
