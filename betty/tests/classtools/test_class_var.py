from betty.classtools.class_var import ClassVarOwnership, HasClassVars, OwnedClassVar
from betty.classtools.co_op import CoOpClassVar


class _ClassVarOwner:
    pass


class _OwnedClassVar(OwnedClassVar[_ClassVarOwner]):
    pass


class _OwnerWithClassVar(_ClassVarOwner):
    my_first_class_var = _OwnedClassVar()


class TestHasClassVars:
    def test_init_class_vars__without_class_vars(self) -> None:
        assert not list(HasClassVars.class_vars())

    def test_init_class_vars__with_class_var(self) -> None:
        class_var = CoOpClassVar()

        class _HasClassVars(HasClassVars):
            my_first_class_var = class_var

        assert list(_HasClassVars.class_vars()) == [class_var]


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
