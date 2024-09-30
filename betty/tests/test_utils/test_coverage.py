import pytest

from betty.test_utils.coverage import Module, MissingReason


class TestModule:
    @pytest.mark.parametrize(
        ("errors_expected", "sut"),
        [
            (False, Module("betty.tests.test_utils.coverage_fixtures._module_private")),
            (False, Module("betty.tests.test_utils.coverage_fixtures.module_with_test")),
            (
                False,
                Module(
                    "betty.tests.test_utils.coverage_fixtures.module_without_test",
                    missing=MissingReason.SHOULD_BE_COVERED,
                ),
            ),
            (True, Module("betty.tests.test_utils.coverage_fixtures.module_without_test")),
        ],
    )
    async def test(self, errors_expected: bool, sut: Module) -> None:
        assert (len(list(sut.validate())) > 0) is errors_expected
