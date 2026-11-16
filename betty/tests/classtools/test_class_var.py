from betty.classtools.class_var import (
    ClassVar,
    ClassVarOwnership,
    ClassVars,
    HasClassVars,
    OwnedClassVar,
)


class _ClassVarOwner:
    pass


class _OwnedClassVar(OwnedClassVar[_ClassVarOwner]):
    pass


class _OwnerWithClassVar(_ClassVarOwner):
    my_first_class_var = _OwnedClassVar()


class TestClassVars:
    def test___get____without_class_vars(self) -> None:
        assert ClassVars(object, ClassVar).__get__(None, None) == ()

    def test___get____with_class_vars(self) -> None:
        class_var = ClassVar()

        class _Owner:
            my_first_class_var = class_var

        assert ClassVars(_Owner, ClassVar).__get__(None, None) == (class_var,)


class TestHasClassVars:
    def test_class_vars__without_class_vars(self) -> None:
        class _HasClassVars(HasClassVars):
            pass

        assert not _HasClassVars.class_vars

    def test_class_vars__with_class_var(self) -> None:
        class_var = ClassVar()

        class _HasClassVars(HasClassVars):
            my_first_class_var = class_var

        assert _HasClassVars.class_vars == (class_var,)


class TestClassVarOwnership:
    def test_fully_qualified_name(self) -> None:
        sut = ClassVarOwnership(_ClassVarOwner, "my_first_class_var", _OwnedClassVar())
        assert (
            sut.fully_qualified_name
            == "betty.tests.classtools.test_class_var:_ClassVarOwner.my_first_class_var"
        )

    def test___repr__(self) -> None:
        sut = ClassVarOwnership(_ClassVarOwner, "my_first_class_var", _OwnedClassVar())
        assert (
            repr(sut)
            == "<ClassVarOwnership betty.tests.classtools.test_class_var:_OwnedClassVar @ betty.tests.classtools.test_class_var:_ClassVarOwner.my_first_class_var>"
        )


class TestOwnedClassVar:
    def test_ownership(self) -> None:
        assert (
            _OwnerWithClassVar.my_first_class_var.ownership.fully_qualified_name
            == "betty.tests.classtools.test_class_var:_OwnerWithClassVar.my_first_class_var"
        )
