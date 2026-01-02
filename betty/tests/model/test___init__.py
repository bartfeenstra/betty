import pytest
from typing_extensions import override

from betty.model import Entity, EntityDefinition, persistent_id
from betty.plugin import PluginDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestEntityDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EntityDefinition

    def test_public_facing(self) -> None:
        sut = EntityDefinition(
            "-",
            public_facing=True,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
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
