from betty.definition.cls import ClassedDefinition, OptionalClassedDefinition


class TestClassedDefinition:
    def test_cls(self) -> None:
        sut = ClassedDefinition(cls=object)
        assert sut.cls is object

    def test___call__(self) -> None:
        sut = ClassedDefinition[object]()
        sut(object)
        assert sut.cls is object


class TestOptionalClassedDefinition:
    def test_cls__without_cls(self) -> None:
        sut = OptionalClassedDefinition()
        assert sut.cls is None

    def test_cls__with_cls(self) -> None:
        sut = OptionalClassedDefinition(cls=object)
        assert sut.cls is object

    def test___call__(self) -> None:
        sut = OptionalClassedDefinition[object]()
        sut(object)
        assert sut.cls is object
