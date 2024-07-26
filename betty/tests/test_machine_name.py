import pytest

from betty.machine_name import validate_machine_name


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
            # String is exactly 255 characters.
            (
                True,
                "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachi",
            ),
            # An empty string.
            (False, ""),
            # String exceeds 255 characters.
            (
                False,
                "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachin",
            ),
        ],
    )
    async def test(self, expected: bool, alleged_machine_name: str) -> None:
        assert validate_machine_name(alleged_machine_name) is expected
