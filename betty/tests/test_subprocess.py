import logging
from asyncio.subprocess import Process
from pathlib import Path
from subprocess import CalledProcessError

import aiofiles
import pytest
from _pytest.logging import LogCaptureFixture

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
    async def test_with_errors(
        self, shell: bool, caplog: LogCaptureFixture, tmp_path: Path
    ) -> None:
        stdout_sentinel = "Hello, stdout!"
        stderr_sentinel = "Hello, stderr!"
        script_path = tmp_path / "test.py"
        python_script = f"""
import sys
print("{stdout_sentinel}")
print("{stderr_sentinel}", file=sys.stderr)
sys.exit(1)"""
        async with aiofiles.open(script_path, "w") as f:
            await f.write(python_script)
        with pytest.raises(CalledProcessError), caplog.at_level(logging.NOTSET):
            await run_process(
                [
                    "python",
                    str(script_path),
                ],
                shell=shell,
            )
        assert f"stdout:\n{stdout_sentinel}" in caplog.text
        assert f"stderr:\n{stderr_sentinel}" in caplog.text
