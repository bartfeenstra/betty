from pathlib import Path
from subprocess import CalledProcessError

import pytest
from pytest_mock import MockerFixture

from betty._npm import NpmUnavailable, new_npm_requirement, npm
from betty.user.no_op import NoOpUser


class TestNpm:
    async def test(self) -> None:
        await npm(["--version"], user=NoOpUser())

    async def test_command_not_found(self, mocker: MockerFixture) -> None:
        mocker.patch("betty.subprocess.run_process", side_effect=FileNotFoundError)
        with pytest.raises(NpmUnavailable):
            await npm(["--version"], user=NoOpUser())

    async def test_command_error(self, mocker: MockerFixture, tmp_path: Path) -> None:
        mocker.patch(
            "betty.subprocess.run_process",
            side_effect=CalledProcessError(1, "", "", ""),
        )
        with pytest.raises(CalledProcessError):
            await npm(["--version"], user=NoOpUser())


async def test_new_npm_requirement__is_met() -> None:
    assert await new_npm_requirement(user=NoOpUser()) is None


async def test_new_npm_requirement__is_unmet_with_command_not_found(
    mocker: MockerFixture,
) -> None:
    mocker.patch("betty._npm.npm", side_effect=NpmUnavailable)
    assert await new_npm_requirement(user=NoOpUser()) is not None


async def test_new_npm_requirement__is_unmet_with_command_error(
    mocker: MockerFixture,
) -> None:
    mocker.patch("betty._npm.npm", side_effect=CalledProcessError(1, "", "", ""))
    assert await new_npm_requirement(user=NoOpUser()) is not None
