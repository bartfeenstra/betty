import logging
from asyncio.subprocess import Process
from pathlib import Path

import aiofiles
import pytest
from _pytest.logging import LogCaptureFixture

from betty.subprocess import run_process, SubprocessError


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
    async def test_with_errors_without_output(
        self, shell: bool, caplog: LogCaptureFixture, tmp_path: Path
    ) -> None:
        script_path = tmp_path / "test.py"
        python_script = """
import sys
sys.exit(1)"""
        async with aiofiles.open(script_path, "w") as f:
            await f.write(python_script)
        with pytest.raises(SubprocessError), caplog.at_level(logging.NOTSET):
            await run_process(["python", str(script_path)], shell=shell)
        assert "stdout:\n" not in caplog.text
        assert "stderr:\n" not in caplog.text

    @pytest.mark.parametrize(
        "shell",
        [
            True,
            False,
        ],
    )
    async def test_with_errors_with_output(
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
        with pytest.raises(SubprocessError), caplog.at_level(logging.NOTSET):
            await run_process(["python", str(script_path)], shell=shell)
        assert f"stdout:\n{stdout_sentinel}" in caplog.text
        assert f"stderr:\n{stderr_sentinel}" in caplog.text

    @pytest.mark.parametrize(
        "shell",
        [
            True,
            False,
        ],
    )
    async def test_with_command_not_found(
        self, shell: bool, caplog: LogCaptureFixture, tmp_path: Path
    ) -> None:
        with pytest.raises(SubprocessError), caplog.at_level(logging.NOTSET):
            await run_process(["non-existent-command"], shell=shell)
