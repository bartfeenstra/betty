from asyncio.subprocess import Process
from pathlib import Path
from shutil import which

import aiofiles
import pytest

from betty.subprocess import SubprocessError, run_process
from betty.test_utils.user import StaticUser


@pytest.mark.parametrize(
    "shell",
    [
        True,
        False,
    ],
)
async def test_run_process__without_errors(shell: bool) -> None:
    process = await run_process(["true"], shell=shell, user=StaticUser())
    assert isinstance(process, Process)


@pytest.mark.parametrize(
    "shell",
    [
        True,
        False,
    ],
)
async def test_run_process__with_errors_without_output(
    shell: bool, tmp_path: Path
) -> None:
    user = StaticUser()
    script_path = tmp_path / "test.py"
    python_script = """
import sys
sys.exit(1)"""
    async with aiofiles.open(script_path, "w") as f:
        await f.write(python_script)
    with pytest.raises(SubprocessError):
        await run_process(
            [which("python"), "-W", "ignore", str(script_path)],  # ty:ignore[invalid-argument-type]
            shell=shell,
            user=user,
        )
    user.assert_not_message_debug("stdout:\n")
    user.assert_not_message_debug("stderr:\n")


@pytest.mark.parametrize(
    "shell",
    [
        True,
        False,
    ],
)
async def test_run_process__with_errors_with_output(
    shell: bool, tmp_path: Path
) -> None:
    user = StaticUser()
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
    with pytest.raises(SubprocessError):
        await run_process(
            [which("python"), "-W", "ignore", str(script_path)],  # ty:ignore[invalid-argument-type]
            shell=shell,
            user=user,
        )
    user.assert_message_debug(["stdout:", stdout_sentinel])
    user.assert_message_debug(["stderr:", stderr_sentinel])


@pytest.mark.parametrize(
    "shell",
    [
        True,
        False,
    ],
)
async def test_run_process__with_command_not_found(shell: bool, tmp_path: Path) -> None:
    with pytest.raises(SubprocessError):
        await run_process(["non-existent-command"], shell=shell, user=StaticUser())
