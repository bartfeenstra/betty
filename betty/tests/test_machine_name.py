import pytest

from betty.machine_name import (
    validate_machine_name,
    machinify,
    assert_machine_name,
    InvalidMachineName,
)


class TestValidateMachineName:
    @pytest.mark.parametrize(
        (
            "expected",
            "alleged_machine_name",
        ),
        [
            (True, "package-machine"),
            (False, "package_machine"),
            (True, "package-module-machine"),
            (False, "package_module_machine"),
            (True, "machine1234567890"),
            # String is exactly 250 characters.
            (
                True,
                "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachi",
            ),
            # An empty string.
            (False, ""),
            # String exceeds 250 characters.
            (
                False,
                "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachin",
            ),
        ],
    )
    async def test(self, expected: bool, alleged_machine_name: str) -> None:
        assert validate_machine_name(alleged_machine_name) is expected


class TestAssertMachineName:
    @pytest.mark.parametrize(
        "alleged_machine_name",
        [
            "package-machine",
            "package-module-machine",
            "machine1234567890",
            # String is exactly 250 characters.
            "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachi",
        ],
    )
    async def test_with_valid_value(self, alleged_machine_name: str) -> None:
        await assert_machine_name()(alleged_machine_name)

    @pytest.mark.parametrize(
        "alleged_machine_name",
        [
            "package_machine",
            "package_module_machine",
            # An empty string.
            "",
            # String exceeds 250 characters.
            "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachin",
        ],
    )
    async def test_with_invalid_value(self, alleged_machine_name: str) -> None:
        with pytest.raises(InvalidMachineName):
            await assert_machine_name()(alleged_machine_name)


class TestInvalidMachineName:
    async def test_new(self) -> None:
        InvalidMachineName.new("my-first-machine-name")


class TestMachinify:
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
    async def test(self, expected: str | None, source: str) -> None:
        actual = machinify(source)
        if expected is not None:
            await assert_machine_name()(expected)
        assert actual == expected
