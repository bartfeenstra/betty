from betty.datas.definition import DefinitionConfigDefinition


class TestDefinitionConfigDefinition:
    def test__default_porter(self) -> None:
        assert DefinitionConfigDefinition(label="-").porter
