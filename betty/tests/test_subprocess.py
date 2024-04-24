from asyncio.subprocess import Process
from subprocess import CalledProcessError

import pytest

from betty.subprocess import run_process


class TestRunProcess:
    @pytest.mark.parametrize(
        "shell",
        [
            True,
            False,
        ],
    )
    async def test_without_errors(self, shell: bool) -> None:
        process = await run_process(["true"], shell=shell)
        assert isinstance(process, Process)

    @pytest.mark.parametrize(
        "shell",
        [
            True,
            False,
        ],
    )
    async def test_with_errors(self, shell: bool) -> None:
        with pytest.raises(CalledProcessError):
            await run_process(["false"], shell=shell)
