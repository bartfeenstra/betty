from typing import Any

import pytest

from betty.exception import HumanFacingException
from betty.machine_name import InvalidMachineName, MachineName
from betty.test_utils.machine_name import INVALID_MACHINE_NAMES, VALID_MACHINE_NAMES


class TestMachineName:
    def test___init____without_value(self) -> None:
        sut = MachineName()
        assert len(sut) == 36
        assert not sut.persistent

    @pytest.mark.parametrize("machine_name", VALID_MACHINE_NAMES)
    def test___init____with_valid_value(self, machine_name: str) -> None:
        sut = MachineName(machine_name)
        assert sut == machine_name
        assert sut.persistent

    @pytest.mark.parametrize("machine_name", INVALID_MACHINE_NAMES)
    def test___init____with_invalid_value(self, machine_name: str) -> None:
        with pytest.raises(InvalidMachineName):
            MachineName(machine_name)

    @pytest.mark.parametrize("machine_name", VALID_MACHINE_NAMES)
    def test_load(self, machine_name: str) -> None:
        sut = MachineName.load(machine_name)
        assert sut == machine_name
        assert sut.persistent

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
        sut = MachineName.machinify(source)
        assert sut == expected
        if sut is not None:
            assert sut.persistent


class TestInvalidMachineName:
    def test_new(self) -> None:
        value = "my-first-machine-name"
        assert value in str(InvalidMachineName(value))
