import pytest

from betty.machine_id import validate_machine_id


class TestValidateMachineId:
    @pytest.mark.parametrize(
        (
            "expected",
            "alleged_machine_id",
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
    async def test(self, expected: bool, alleged_machine_id: str) -> None:
        assert validate_machine_id(alleged_machine_id) is expected
