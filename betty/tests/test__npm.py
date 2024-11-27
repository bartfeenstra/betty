from pathlib import Path
from subprocess import CalledProcessError

import pytest
from pytest_mock import MockerFixture

from betty._npm import NpmRequirement, NpmUnavailable, npm


class TestNpm:
    async def test(self) -> None:
        await npm(["--version"])

    async def test_command_not_found(self, mocker: MockerFixture) -> None:
        mocker.patch("betty.subprocess.run_process", side_effect=FileNotFoundError)
        with pytest.raises(NpmUnavailable):
            await npm(["--version"])

    async def test_command_error(self, mocker: MockerFixture, tmp_path: Path) -> None:
        mocker.patch(
            "betty.subprocess.run_process",
            side_effect=CalledProcessError(1, "", "", ""),
        )
        with pytest.raises(CalledProcessError):
            await npm(["--version"])


class TestNpmRequirement:
    async def test_is_met(self) -> None:
        sut = await NpmRequirement.new()
        assert sut.is_met()

    async def test_is_met_with_command_not_found(self, mocker: MockerFixture) -> None:
        mocker.patch("betty._npm.npm", side_effect=NpmUnavailable)
        sut = await NpmRequirement.new()
        assert not sut.is_met()

    async def test_is_met_with_command_error(self, mocker: MockerFixture) -> None:
        mocker.patch("betty._npm.npm", side_effect=CalledProcessError(1, "", "", ""))
        sut = await NpmRequirement.new()
        assert not sut.is_met()
