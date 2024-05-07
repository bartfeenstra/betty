from pytest_mock import MockerFixture

from betty._npm import NpmRequirement, NpmUnavailable


class TestNpmRequirement:
    async def test_check_met(self) -> None:
        sut = NpmRequirement()
        assert sut.is_met()

    async def test_check_unmet(self, mocker: MockerFixture) -> None:
        m_npm = mocker.patch("betty._npm.npm")
        m_npm.side_effect = NpmUnavailable()
        sut = NpmRequirement()
        assert not sut.is_met()
