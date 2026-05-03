from betty.machine_name import MachineName
from betty.properties.machine_name import MachineNameProperty


class TestMachineNameProperty:
    class _Owner:
        name = MachineNameProperty()

    def test(self) -> None:
        name = "hello-world"
        owner = self._Owner()
        owner.name = name
        assert isinstance(owner.name, MachineName)
        assert owner.name == name
