import logging
from asyncio import create_task
from asyncio.subprocess import Process
from os import environ
from pathlib import Path

import aiofiles
import pytest
from _pytest.logging import LogCaptureFixture

from betty.functools import Do
from betty.subprocess import run_process, SubprocessError, run_process_in_terminal


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


@pytest.mark.skipif(
    environ.get("BETTY_TEST_HEADED", None) == "false",
    reason="Cannot test GUI functionality on a headless system",
)
class TestRunProcessInTerminal:
    async def test(self, tmp_path: Path) -> None:
        sentinel_path = tmp_path / "s3nt1n3l"
        task = create_task(
            run_process_in_terminal(
                [
                    "python",
                    "-c",
                    f"from pathlib import Path; Path('{sentinel_path}').touch()",
                ]
            )
        )
        try:
            await Do(lambda: None).until(lambda _: sentinel_path.exists(), retries=50)
        finally:
            task.cancel()
