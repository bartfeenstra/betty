from typing import override

from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.definition.id import (
    IdentifiableDefinitionConfig,
    IdentifiableDefinitionConfigDefinition,
)
from betty.definition.id import IdentifiableDefinition
from betty.typing import Unreachable


class TestIdentifiableDefinitionConfigDefinition:
    def test__porter(self) -> None:
        assert IdentifiableDefinitionConfigDefinition(label="-").porter


class _IdentifiableDefinition(IdentifiableDefinition, ObjectDefinition):
    pass


class _IdentifiableDefinitionConfig(
    IdentifiableDefinitionConfig[_IdentifiableDefinition]
):
    @override
    def new_definition(self) -> _IdentifiableDefinition:
        raise Unreachable


class TestIdentifiableDefinitionConfig:
    def test_id(self) -> None:
        definition_id = "hello-world"
        assert _IdentifiableDefinitionConfig(id=definition_id).id == definition_id
