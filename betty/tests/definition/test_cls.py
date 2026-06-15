from betty.definition.cls import ClsDefinition, OptionalClsDefinition


class TestClsDefinition:
    def test_cls(self) -> None:
        sut = ClsDefinition(cls=object)
        assert sut.cls is object

    def test___call__(self) -> None:
        sut = ClsDefinition[object]()
        sut(object)
        assert sut.cls is object


class TestOptionalClsDefinition:
    def test_cls__without_cls(self) -> None:
        sut = OptionalClsDefinition()
        assert sut.cls is None

    def test_cls__with_cls(self) -> None:
        sut = OptionalClsDefinition(cls=object)
        assert sut.cls is object

    def test___call__(self) -> None:
        sut = OptionalClsDefinition[object]()
        sut(object)
        assert sut.cls is object
