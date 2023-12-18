from subprocess import CalledProcessError

import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.extension.npm import _NpmRequirement


class TestNpmRequirement:
    async def test_check_met(self) -> None:
        async with App():
            sut = _NpmRequirement.check()
        assert sut.is_met()

    @pytest.mark.parametrize('e', [
        CalledProcessError(1, ''),
        FileNotFoundError(),
    ])
    async def test_check_unmet(self, e: Exception, mocker: MockerFixture) -> None:
        m_npm = mocker.patch('betty.extension.npm.npm')
        m_npm.side_effect = e
        async with App():
            sut = _NpmRequirement.check()
        assert not sut.is_met()
