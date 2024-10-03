from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pytest

from betty.ancestry.name import Name
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence_role.presence_roles import (
    Subject,
    Witness,
    Unknown as UnknownPresenceRole,
)
from betty.test_utils.assets.templates import TemplateTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping
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
    async def test(
        self,
        expected: str,
        entity_type_identifier: type[Entity] | None,
        data: Mapping[str, Any],
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
            ("false", UnknownPresenceRole()),
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
