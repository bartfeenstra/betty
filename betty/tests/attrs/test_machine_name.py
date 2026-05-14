from betty.attrs.machine_name import MachineNameAttr
from betty.machine_name import MachineName
from betty.property import HasProperties


class TestMachineNameAttr:
    class _Owner(HasProperties):
        name = MachineNameAttr()

    def test(self) -> None:
        name = "hello-world"
        owner = self._Owner()
        owner.name = name
        assert isinstance(owner.name, MachineName)
        assert owner.name == name
