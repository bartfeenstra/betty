from betty.attrs.machine_name import MachineNameAttr
from betty.machine_name import MachineName


class TestMachineNameAttr:
    class _Owner:
        name = MachineNameAttr()

    def test(self) -> None:
        name = "hello-world"
        owner = self._Owner()
        owner.name = name
        assert isinstance(owner.name, MachineName)
        assert owner.name == name
