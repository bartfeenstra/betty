from betty.datas.definition.ordered import OrderedDefinitionConfig


class TestOrderedDefinitionConfig:
    def test_before(self) -> None:
        before = ["my-first-definition"]
        sut = OrderedDefinitionConfig(before=before)
        assert sut.before == before

    def test_after(self) -> None:
        after = ["my-first-definition"]
        sut = OrderedDefinitionConfig(after=after)
        assert sut.after == after
