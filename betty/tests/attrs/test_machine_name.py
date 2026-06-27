from betty.attr import Object
from betty.attrs.machine_name import new_machine_name_attr
from betty.machine_name import MachineName


class _Owner(Object):
    name = new_machine_name_attr()


def test_new_machine_name_attr__set() -> None:
    name = "hello-world"
    owner = _Owner()
    owner.name = name
    assert isinstance(owner.name, MachineName)
    assert owner.name == name
