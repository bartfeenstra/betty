from betty.definition.cls import ClsDefinition


class TestClsDefinition:
    def test_cls(self) -> None:
        sut = ClsDefinition(cls=object)
        assert sut.cls is object

    def test___call__(self) -> None:
        sut = ClsDefinition[object]()
        sut(object)
        assert sut.cls is object
