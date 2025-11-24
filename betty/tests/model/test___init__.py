from pathlib import Path

import pytest
from typing_extensions import override

from betty.locale.localizable import CountablePlain
from betty.model import (
    Entity,
    EntityDefinition,
    persistent_id,
)
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin.classed import ClassedPluginDefinitionClassTestBase


class TestEntityDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EntityDefinition

    def test_public_facing(self) -> None:
        sut = EntityDefinition(
            public_facing=True,
            id="-",
            label="",
            label_plural="",
            label_countable=CountablePlain("", ""),
        )
        assert sut.public_facing


class TestEntityDocumentation(PluginDocumentationTestBase[EntityDefinition]):
    _plugin_type = EntityDefinition
    _plugin_type_documentation_path = Path("usage") / "ancestry.rst"


@pytest.mark.parametrize(
    ("expected", "entity"),
    [
        (False, Entity()),
        (True, Entity("my-first-entity-id")),
    ],
)
def test_persistent_id(expected: bool, entity: Entity) -> None:
    assert persistent_id(entity) == expected
