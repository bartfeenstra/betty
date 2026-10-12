from typing import Any

import pytest

from betty.machine_name import MachineName
from betty.validation import Invalid
from betty.validators.str import NotAStr

_valid_machine_names = (
    "a",
    "-a",
    "a-",
    "-a-",
    "a-b",
    "-a-b",
    "a-b-",
    "-a-b-",
    "a-b-c",
    "abc1234567890",
    # A UUID4.
    "9e3b550e-4263-4c49-a288-d6c6b585722a",
    # Name is exactly 250 characters.
    "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachi",
)
_invalid_machine_names = (
    # An empty name.
    "",
    # Disallowed characters.
    "A",
    "#",
    "_",
    # Consecutive dashes.
    "--a",
    "a--",
    "--a--",
    "a--b",
    "--a-b",
    "-a-b--",
    # Name exceeds 250 characters.
    "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachin",
)


class TestMachineName:
    def test___init____without_value(self) -> None:
        sut = MachineName()
        assert len(sut) == 36
        assert not sut.persistent

    @pytest.mark.parametrize("machine_name", _valid_machine_names)
    def test___init____with_valid_value(self, machine_name: str) -> None:
        sut = MachineName(machine_name)
        assert sut == machine_name
        assert sut.persistent

    @pytest.mark.parametrize("machine_name", _invalid_machine_names)
    def test___init____with_invalid_value(self, machine_name: str) -> None:
        with pytest.raises(Invalid):
            MachineName(machine_name)

    @pytest.mark.parametrize("machine_name", _valid_machine_names)
    def test_load(self, machine_name: str) -> None:
        sut = MachineName.definition.porter.load(machine_name)
        assert sut == machine_name
        assert sut.persistent

    @pytest.mark.parametrize(
        "value",
        [
            {},
            None,
            True,
            123,
        ],
    )
    def test_load__without_str(self, value: Any) -> None:
        with pytest.raises(NotAStr):
            MachineName.definition.porter.load(value)

    @pytest.mark.parametrize(
        "value",
        _invalid_machine_names,
    )
    def test_load__with_invalid_value(self, value: Any) -> None:
        with pytest.raises(Invalid):
            MachineName.definition.porter.load(value)

    @pytest.mark.parametrize("machine_name", _valid_machine_names)
    def test_dump(self, machine_name: str) -> None:
        sut = MachineName(machine_name)
        assert MachineName.definition.porter.dump(sut) == machine_name

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
