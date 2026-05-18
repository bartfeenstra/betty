from pathlib import Path
from subprocess import CalledProcessError

import pytest
from pytest_mock import MockerFixture

from betty.npm import NpmUnavailable, npm
from betty.users.no_op import NoOpUser


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
