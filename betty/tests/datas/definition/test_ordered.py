from betty.datas.definition.ordered import OrderedDefinitionConfig
from betty.definition.ordered import OrderedDefinition
from betty.typing import Unreachable


class _OrderedDefinitionConfig(OrderedDefinitionConfig):
    def new_definition(self) -> OrderedDefinition:
        raise Unreachable


class TestOrderedDefinitionConfig:
    def test_before(self) -> None:
        before = ["my-first-definition"]
        sut = _OrderedDefinitionConfig(id="my-first-plugin", before=before)
        assert sut.before == before

    def test_after(self) -> None:
        after = ["my-first-definition"]
        sut = _OrderedDefinitionConfig(id="my-first-plugin", after=after)
        assert sut.after == after
