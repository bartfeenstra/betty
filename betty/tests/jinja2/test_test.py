from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pytest
from betty.model.ancestry import Person, Place, PlaceName
from betty.model.presence_role import Subject, Attendee, Witness
from betty.tests import TemplateTestCase

if TYPE_CHECKING:
    from betty.model import Entity


class TestTestEntity(TemplateTestCase):
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
        self, expected: str, entity_type: type[Entity], data: dict[str, Any]
    ) -> None:
        template = f'{{% if data is entity("{entity_type.plugin_id()}") %}}true{{% else %}}false{{% endif %}}'
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert expected == actual


class TestTestSubjectRole(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", Subject()),
            ("false", Subject),
            ("false", Attendee()),
            ("false", 9),
        ],
    )
    async def test(self, expected: str, data: dict[str, Any]) -> None:
        template = "{% if data is subject_role %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert expected == actual


class TestTestWitnessRole(TemplateTestCase):
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", Witness()),
            ("false", Witness),
            ("false", Attendee()),
            ("false", 9),
        ],
    )
    async def test(self, expected: str, data: dict[str, Any]) -> None:
        template = "{% if data is witness_role %}true{% else %}false{% endif %}"
        async with self._render(
            template_string=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert expected == actual
