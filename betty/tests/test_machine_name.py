from typing import Any

import pytest

from betty.exception import HumanFacingException
from betty.machine_name import InvalidMachineName, MachineName, MachineNameProperty

VALID_MACHINE_NAMES = (
    "a",
    "-a",
    "--a",
    "a-",
    "a--",
    "a-b",
    "a--b",
    "-a-b",
    "a-b-c",
    "abc1234567890",
    # Name is exactly 250 characters.
    "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachi",
)

INVALID_MACHINE_NAMES = (
    # Underscores.
    "package_machine",
    "package_module_machine",
    # An empty name.
    "",
    # Name exceeds 250 characters.
    "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachin",
)


class TestMachineName:
    @pytest.mark.parametrize("machine_name", VALID_MACHINE_NAMES)
    def test___init____with_valid_value(self, machine_name: str) -> None:
        assert MachineName(machine_name) == machine_name

    @pytest.mark.parametrize("machine_name", INVALID_MACHINE_NAMES)
    def test___init____with_invalid_value(self, machine_name: str) -> None:
        with pytest.raises(InvalidMachineName):
            MachineName(machine_name)

    @pytest.mark.parametrize("machine_name", VALID_MACHINE_NAMES)
    def test_load(self, machine_name: str) -> None:
        assert MachineName.load(machine_name) == machine_name

    @pytest.mark.parametrize(
        "machine_name", [*INVALID_MACHINE_NAMES, {}, None, True, 123]
    )
    def test_load__with_invalid_value(self, machine_name: Any) -> None:
        with pytest.raises(HumanFacingException):
            MachineName.load(machine_name)

    @pytest.mark.parametrize("machine_name", VALID_MACHINE_NAMES)
    def test_dump(self, machine_name: str) -> None:
        sut = MachineName(machine_name)
        assert sut.dump() == machine_name

    @pytest.mark.parametrize(
        ("expected", "source"),
        [
            # Sources that can be used verbatim.
            ("0123456789", "0123456789"),
            ("abc", "abc"),
            # Sources with leading or trailing hyphens.
            ("abc", "-abc"),
            ("abc", "abc-"),
            ("abc", "-abc-"),
            # Sources with leading or trailing hyphens after transforming disallowed characters.
            ("abc", "#abc"),
            ("abc", "abc#"),
            ("abc", "#abc#"),
            # Sources with sequences of hyphens.
            ("a-b", "a--b"),
            ("a-b", "a---------b"),
            # Sources with sequences of hyphens after transforming disallowed characters.
            ("a-b", "a##b"),
            ("a-b", "a#########b"),
            # Source exceeds 250 characters.
            (
                "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachi",
                "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachin",
            ),
            # Sources without usable characters.
            (None, ""),
            (None, "-"),
            (None, "---------"),
            (None, "!@#$%^&*()"),
        ],
    )
    def test_machinify(self, expected: str | None, source: str) -> None:
        assert MachineName.machinify(source) == expected


class TestInvalidMachineName:
    def test_new(self) -> None:
        value = "my-first-machine-name"
        assert value in str(InvalidMachineName(value))


class TestMachineNameProperty:
    class _Owner:
        name = MachineNameProperty()

    def test(self) -> None:
        name = "hello-world"
        owner = self._Owner()
        owner.name = name
        assert isinstance(owner.name, MachineName)
        assert owner.name == name
