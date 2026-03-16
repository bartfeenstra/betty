import pytest

from betty.model import Entity
from betty.test_utils.jinja import assert_template_string


class TestPersistentEntityId:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("false", Entity()),
            ("true", Entity("my-first-entity-id")),
        ],
    )
    async def test___call__(self, expected: bool, data: Entity) -> None:
        template = "{% if data is persistent_entity_id %}true{% else %}false{% endif %}"
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
