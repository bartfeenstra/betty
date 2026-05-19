import pytest

from betty.entity import Entity, EntityDefinition, persistent_id
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


class TestEntityDefinition:
    def test_public_facing(self) -> None:
        sut = EntityDefinition(
            "-dummy",
            public_facing=True,
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.public_facing


@pytest.mark.parametrize(
    ("expected", "entity"),
    [
        (False, Entity()),
        (True, Entity("my-first-entity-id")),
    ],
)
def test_persistent_id(expected: bool, entity: Entity) -> None:
    assert persistent_id(entity) == expected
