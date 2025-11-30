from pathlib import Path

import pytest
from typing_extensions import override

from betty.model import (
    Entity,
    EntityPlugin,
    persistent_id,
)
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.locale.localizable import (
    DUMMY_LOCALIZABLE,
    _DummyCountableLocalizable,
)
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestEntityPlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EntityPlugin

    def test_public_facing(self) -> None:
        sut = EntityPlugin(
            "-",
            public_facing=True,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=_DummyCountableLocalizable(),
        )
        assert sut.public_facing


class TestEntityDocumentation(PluginDocumentationTestBase[EntityPlugin]):
    _plugin_type = EntityPlugin
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
